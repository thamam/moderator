"""
LangGraph orchestrator for Moderator.

Main orchestration class that builds and executes the
supervision graph with checkpoint and interrupt support.
"""

from pathlib import Path
from typing import Any
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

from .state import (
    OrchestratorState,
    ExecutionPhase,
    create_initial_state,
    deserialize_approval_request,
)
from .nodes import (
    initialize_node,
    decompose_node,
    supervisor_review_node,
    human_approval_node,
    execute_task_node,
    complete_node,
    should_get_approval,
    check_approval_result,
    after_human_approval,
    check_more_tasks,
    increment_task_index,
)
from .tracing import setup_tracing, TracingConfig

# Import core Moderator components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from logger import StructuredLogger
from models import ProjectState, Task, TaskStatus


class LangGraphOrchestrator:
    """
    LangGraph-based orchestrator with human-like supervision.

    Provides a stateful graph execution with:
    - Automated supervisor review
    - Human approval interrupt points
    - Checkpoint/resume capability
    - LangSmith debugging integration
    """

    def __init__(self, config: dict, target_dir: str | Path | None = None):
        """
        Initialize the LangGraph orchestrator.

        Args:
            config: Configuration dictionary
            target_dir: Target directory for the project
        """
        self.config = config
        self.target_dir = Path(target_dir) if target_dir else Path(config.get("repo_path", "."))

        # Setup tracing
        self.tracing = setup_tracing(config)

        # Setup checkpoint persistence
        self.checkpointer = self._create_checkpointer()

        # Build the graph
        self.graph = self._build_graph()
        self.app = self.graph.compile(checkpointer=self.checkpointer)

        # Initialize logger
        self.logger = StructuredLogger(
            log_dir=self.target_dir / ".moderator" / "logs",
            project_id="langgraph",
        )

    def _create_checkpointer(self):
        """
        Create the appropriate checkpointer based on configuration.

        Returns:
            Checkpointer instance
        """
        langgraph_config = self.config.get("langgraph", {})
        checkpoint_config = langgraph_config.get("checkpoints", {})

        backend = checkpoint_config.get("backend", "memory")

        if backend == "sqlite":
            # Use SQLite for persistent checkpoints
            checkpoint_path = checkpoint_config.get(
                "path",
                str(self.target_dir / ".moderator" / "checkpoints" / "orchestrator.db")
            )
            # Ensure directory exists
            Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
            return SqliteSaver.from_conn_string(checkpoint_path)
        else:
            # Use memory for development
            return MemorySaver()

    def _build_graph(self) -> StateGraph:
        """
        Build the orchestration state graph.

        Returns:
            Configured StateGraph
        """
        # Create graph with state schema
        graph = StateGraph(OrchestratorState)

        # Add nodes
        graph.add_node("initialize", initialize_node)
        graph.add_node("decompose", decompose_node)
        graph.add_node("supervisor_review", supervisor_review_node)
        graph.add_node("human_approval", human_approval_node)
        graph.add_node("execute_task", execute_task_node)
        graph.add_node("increment_task", increment_task_index)
        graph.add_node("complete", complete_node)

        # Set entry point
        graph.set_entry_point("initialize")

        # Add edges

        # initialize -> decompose
        graph.add_edge("initialize", "decompose")

        # decompose -> check if approval needed
        graph.add_conditional_edges(
            "decompose",
            should_get_approval,
            {
                "supervisor_review": "supervisor_review",
                "execute_task": "execute_task",
            }
        )

        # supervisor_review -> check if human approval needed
        graph.add_conditional_edges(
            "supervisor_review",
            check_approval_result,
            {
                "human_approval": "human_approval",
                "execute_task": "execute_task",
                "complete": "complete",
            }
        )

        # human_approval -> next step based on approval
        graph.add_conditional_edges(
            "human_approval",
            after_human_approval,
            {
                "execute_task": "execute_task",
                "complete": "complete",
                "decompose": "decompose",
            }
        )

        # execute_task -> review or check for more tasks
        graph.add_conditional_edges(
            "execute_task",
            check_more_tasks,
            {
                "supervisor_review": "increment_task",
                "complete": "complete",
            }
        )

        # increment_task -> supervisor_review
        graph.add_edge("increment_task", "supervisor_review")

        # complete -> END
        graph.add_edge("complete", END)

        return graph

    def execute(
        self,
        requirements: str,
        project_id: str | None = None,
        thread_id: str | None = None,
    ) -> ProjectState:
        """
        Execute orchestration for given requirements.

        Args:
            requirements: Project requirements to execute
            project_id: Optional project ID
            thread_id: Optional thread ID for checkpointing

        Returns:
            Final ProjectState
        """
        # Create initial state
        initial_state = create_initial_state(
            requirements=requirements,
            config=self.config,
            target_dir=str(self.target_dir),
            project_id=project_id,
        )

        # Create thread config
        if thread_id is None:
            thread_id = initial_state["project_id"]

        config = {"configurable": {"thread_id": thread_id}}

        self.logger.info(
            "langgraph_orchestrator",
            "execution_started",
            project_id=initial_state["project_id"],
            thread_id=thread_id,
        )

        try:
            # Run the graph
            final_state = None
            for event in self.app.stream(initial_state, config):
                # Log each step
                for node_name, node_state in event.items():
                    self.logger.debug(
                        "langgraph_orchestrator",
                        "node_executed",
                        node=node_name,
                        phase=node_state.get("phase"),
                    )

                    # Check for interrupt (pending approval)
                    if node_state.get("pending_approval"):
                        self.logger.info(
                            "langgraph_orchestrator",
                            "approval_required",
                            approval_type=node_state.get("approval_request", {}).get("approval_type"),
                        )
                        # Return partial state - execution paused
                        return self._state_to_project_state(node_state)

                    final_state = node_state

            if final_state:
                return self._state_to_project_state(final_state)

            # Shouldn't reach here
            return self._state_to_project_state(initial_state)

        except Exception as e:
            self.logger.error(
                "langgraph_orchestrator",
                "execution_failed",
                error=str(e),
            )
            raise

    def resume(
        self,
        thread_id: str,
        approved: bool = True,
        feedback: str | None = None,
    ) -> ProjectState:
        """
        Resume execution after approval interrupt.

        Args:
            thread_id: Thread ID to resume
            approved: Whether approval was granted
            feedback: Optional human feedback

        Returns:
            Final ProjectState after resumption
        """
        config = {"configurable": {"thread_id": thread_id}}

        # Get current state
        state = self.app.get_state(config)
        if not state or not state.values:
            raise ValueError(f"No state found for thread {thread_id}")

        current_state = state.values

        # Update approval request with response
        if current_state.get("approval_request"):
            approval_request = current_state["approval_request"]
            approval_request["approved"] = approved
            approval_request["human_feedback"] = feedback
            approval_request["resolved_at"] = datetime.now().isoformat()

            # Add to history
            history = current_state.get("approval_history", [])
            history.append(approval_request)

            # Clear pending
            updates = {
                "pending_approval": False,
                "approval_request": None,
                "approval_history": history,
            }

            # If approved and was in AWAITING_APPROVAL, move to EXECUTING
            if approved and current_state.get("phase") == ExecutionPhase.AWAITING_APPROVAL.value:
                updates["phase"] = ExecutionPhase.EXECUTING.value

            # Update state
            self.app.update_state(config, updates)

        self.logger.info(
            "langgraph_orchestrator",
            "execution_resumed",
            thread_id=thread_id,
            approved=approved,
        )

        # Continue execution
        try:
            final_state = None
            for event in self.app.stream(None, config):
                for node_name, node_state in event.items():
                    self.logger.debug(
                        "langgraph_orchestrator",
                        "node_executed",
                        node=node_name,
                        phase=node_state.get("phase"),
                    )

                    # Check for another interrupt
                    if node_state.get("pending_approval"):
                        return self._state_to_project_state(node_state)

                    final_state = node_state

            if final_state:
                return self._state_to_project_state(final_state)

            return self._state_to_project_state(current_state)

        except Exception as e:
            self.logger.error(
                "langgraph_orchestrator",
                "resume_failed",
                thread_id=thread_id,
                error=str(e),
            )
            raise

    def get_state(self, thread_id: str) -> OrchestratorState | None:
        """
        Get current state for a thread.

        Args:
            thread_id: Thread ID to get state for

        Returns:
            Current state or None if not found
        """
        config = {"configurable": {"thread_id": thread_id}}
        state = self.app.get_state(config)

        if state and state.values:
            return state.values

        return None

    def list_pending_approvals(self) -> list[dict]:
        """
        List all threads with pending approvals.

        Returns:
            List of pending approval summaries
        """
        # Note: This is a simplified implementation
        # Full implementation would need to track active threads
        pending = []

        # For now, return empty list
        # TODO: Implement proper thread tracking

        return pending

    def _state_to_project_state(self, state: OrchestratorState) -> ProjectState:
        """
        Convert LangGraph state to core ProjectState.

        Args:
            state: LangGraph orchestrator state

        Returns:
            Core ProjectState object
        """
        from models import ProjectPhase

        # Map ExecutionPhase to ProjectPhase
        phase_map = {
            ExecutionPhase.INITIALIZING.value: ProjectPhase.INITIALIZING,
            ExecutionPhase.DECOMPOSING.value: ProjectPhase.DECOMPOSING,
            ExecutionPhase.AWAITING_APPROVAL.value: ProjectPhase.DECOMPOSING,
            ExecutionPhase.EXECUTING.value: ProjectPhase.EXECUTING,
            ExecutionPhase.REVIEWING.value: ProjectPhase.EXECUTING,
            ExecutionPhase.IMPROVING.value: ProjectPhase.IMPROVEMENT,
            ExecutionPhase.COMPLETED.value: ProjectPhase.COMPLETED,
            ExecutionPhase.FAILED.value: ProjectPhase.FAILED,
        }

        phase = phase_map.get(state.get("phase", ""), ProjectPhase.INITIALIZING)

        # Convert tasks
        tasks = []
        for task_dict in state.get("tasks", []):
            task = Task(
                id=task_dict["id"],
                description=task_dict["description"],
                acceptance_criteria=task_dict["acceptance_criteria"],
                status=TaskStatus(task_dict["status"]),
                branch_name=task_dict.get("branch_name"),
                pr_url=task_dict.get("pr_url"),
                pr_number=task_dict.get("pr_number"),
                files_generated=task_dict.get("files_generated", []),
                created_at=task_dict["created_at"],
                started_at=task_dict.get("started_at"),
                completed_at=task_dict.get("completed_at"),
                error=task_dict.get("error"),
            )
            tasks.append(task)

        return ProjectState(
            project_id=state.get("project_id", "unknown"),
            requirements=state.get("requirements", ""),
            phase=phase,
            tasks=tasks,
            current_task_index=state.get("current_task_index", 0),
            require_approval=state.get("config", {}).get("git", {}).get("require_approval", True),
            created_at=state.get("started_at", datetime.now().isoformat()),
            completed_at=state.get("completed_at"),
        )

    def get_graph_visualization(self) -> str:
        """
        Get Mermaid diagram of the graph.

        Returns:
            Mermaid diagram string
        """
        return self.app.get_graph().draw_mermaid()

    def get_langsmith_url(self, run_id: str) -> str | None:
        """
        Get LangSmith URL for a run.

        Args:
            run_id: Run ID

        Returns:
            LangSmith URL or None
        """
        if not self.tracing.enabled:
            return None

        return f"https://smith.langchain.com/o/{self.tracing.project_name}/runs/{run_id}"
