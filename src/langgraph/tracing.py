"""
LangSmith tracing configuration for debugging and observability.

Provides setup and utilities for tracing orchestration execution
through LangSmith for visualization and debugging.
"""

import os
from functools import wraps
from typing import Any, Callable
from datetime import datetime

from langsmith import Client
from langsmith.run_helpers import traceable


class TracingConfig:
    """Configuration for LangSmith tracing."""

    def __init__(
        self,
        project_name: str = "moderator-orchestration",
        api_key: str | None = None,
        enabled: bool = True,
    ):
        """
        Initialize tracing configuration.

        Args:
            project_name: LangSmith project name
            api_key: LangSmith API key (defaults to LANGSMITH_API_KEY env var)
            enabled: Whether tracing is enabled
        """
        self.project_name = project_name
        self.api_key = api_key or os.getenv("LANGSMITH_API_KEY")
        self.enabled = enabled and bool(self.api_key)
        self._client: Client | None = None

    @property
    def client(self) -> Client | None:
        """Get or create LangSmith client."""
        if not self.enabled:
            return None

        if self._client is None:
            self._client = Client(api_key=self.api_key)

        return self._client

    def configure_environment(self) -> None:
        """Set up environment variables for LangSmith tracing."""
        if not self.enabled:
            return

        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = self.project_name

        if self.api_key:
            os.environ["LANGCHAIN_API_KEY"] = self.api_key


def setup_tracing(config: dict) -> TracingConfig:
    """
    Set up LangSmith tracing from configuration.

    Args:
        config: Configuration dictionary with optional langgraph.langsmith section

    Returns:
        Configured TracingConfig instance
    """
    langgraph_config = config.get("langgraph", {})
    langsmith_config = langgraph_config.get("langsmith", {})

    tracing_config = TracingConfig(
        project_name=langsmith_config.get("project", "moderator-orchestration"),
        api_key=langsmith_config.get("api_key"),
        enabled=langsmith_config.get("tracing", True),
    )

    tracing_config.configure_environment()

    return tracing_config


def trace_node(name: str | None = None, metadata: dict | None = None):
    """
    Decorator to trace a graph node execution in LangSmith.

    Args:
        name: Custom name for the trace (defaults to function name)
        metadata: Additional metadata to include in trace

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        trace_name = name or func.__name__

        @wraps(func)
        @traceable(name=trace_name, metadata=metadata or {})
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


def create_run_metadata(
    state: dict,
    node_name: str,
    additional: dict | None = None,
) -> dict:
    """
    Create standardized metadata for a trace run.

    Args:
        state: Current orchestrator state
        node_name: Name of the current node
        additional: Additional metadata to include

    Returns:
        Metadata dictionary
    """
    metadata = {
        "project_id": state.get("project_id"),
        "phase": state.get("phase"),
        "current_task_index": state.get("current_task_index"),
        "node_name": node_name,
        "timestamp": datetime.now().isoformat(),
    }

    if additional:
        metadata.update(additional)

    return metadata


class NodeTracer:
    """
    Context manager for tracing node execution with detailed metrics.
    """

    def __init__(
        self,
        tracing_config: TracingConfig,
        node_name: str,
        state: dict,
    ):
        """
        Initialize node tracer.

        Args:
            tracing_config: Tracing configuration
            node_name: Name of the node being traced
            state: Current orchestrator state
        """
        self.tracing_config = tracing_config
        self.node_name = node_name
        self.state = state
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None

    def __enter__(self):
        """Start tracing the node."""
        self.start_time = datetime.now()

        if self.tracing_config.enabled:
            # Log node entry
            self._log_event("node_entry", {
                "phase": self.state.get("phase"),
                "task_index": self.state.get("current_task_index"),
            })

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End tracing the node."""
        self.end_time = datetime.now()

        if self.tracing_config.enabled:
            duration = (self.end_time - self.start_time).total_seconds()

            # Log node exit
            self._log_event("node_exit", {
                "duration_seconds": duration,
                "error": str(exc_val) if exc_val else None,
                "success": exc_type is None,
            })

        return False  # Don't suppress exceptions

    def _log_event(self, event_type: str, data: dict) -> None:
        """Log an event to the trace."""
        # Events are automatically captured by LangSmith through the traceable decorator
        # This is a placeholder for custom event logging if needed
        pass

    def log_decision(self, decision: str, confidence: float, reasoning: str) -> None:
        """
        Log a supervisor decision.

        Args:
            decision: The decision made
            confidence: Confidence score (0-100)
            reasoning: Explanation of the decision
        """
        if not self.tracing_config.enabled:
            return

        self._log_event("supervisor_decision", {
            "decision": decision,
            "confidence": confidence,
            "reasoning": reasoning,
        })

    def log_state_transition(self, from_phase: str, to_phase: str) -> None:
        """
        Log a state phase transition.

        Args:
            from_phase: Previous phase
            to_phase: New phase
        """
        if not self.tracing_config.enabled:
            return

        self._log_event("state_transition", {
            "from_phase": from_phase,
            "to_phase": to_phase,
        })


def get_trace_url(
    tracing_config: TracingConfig,
    run_id: str,
) -> str | None:
    """
    Get the LangSmith URL for a specific run.

    Args:
        tracing_config: Tracing configuration
        run_id: The run ID to get URL for

    Returns:
        LangSmith URL or None if tracing disabled
    """
    if not tracing_config.enabled:
        return None

    return f"https://smith.langchain.com/o/{tracing_config.project_name}/runs/{run_id}"
