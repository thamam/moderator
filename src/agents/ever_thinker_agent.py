"""
Ever-Thinker Agent - Continuous Improvement Engine for Moderator system.

This agent runs as a background daemon thread that continuously analyzes
completed work during system idle time to identify improvement opportunities.

Core responsibilities:
- Run as background daemon without blocking primary task execution
- Detect system idle time (no tasks executing)
- Orchestrate improvement cycles during idle periods
- Coordinate analyzer modules (6 perspectives: performance, code quality, testing, docs, UX, architecture)
- Manage graceful shutdown within timeout
- Integrate with Learning System to improve suggestion quality

See Epic 3 Tech Spec for detailed design:
bmad-docs/tech-spec-epic-3.md#Story-31-Ever-Thinker-Agent-with-Threading-Daemon
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional
from ..communication.message_bus import MessageBus
from ..communication.messages import AgentMessage, MessageType
from ..logger import StructuredLogger
from ..models import ProjectState, TaskStatus, Task
from .base_agent import BaseAgent
from .analyzers import (
    PerformanceAnalyzer,
    CodeQualityAnalyzer,
    TestingAnalyzer,
    DocumentationAnalyzer,
    UXAnalyzer,
    ArchitectureAnalyzer
)
from .analyzers.models import Improvement, ImprovementType
from ..learning.improvement_tracker import ImprovementTracker


class EverThinkerAgent(BaseAgent):
    """
    Ever-Thinker Agent - Background daemon for continuous improvement analysis.

    Inherits from BaseAgent and implements daemon thread lifecycle for analyzing
    completed work during system idle time without blocking primary execution.

    Threading Strategy:
    - Uses daemon thread (daemon=True) to avoid blocking main thread exit
    - Uses threading.Event for signaling (running, shutdown)
    - Polls for idle status every 60 seconds
    - Graceful shutdown within 5 seconds

    Attributes:
        message_bus: MessageBus for inter-agent communication
        learning_db: LearningDB for pattern queries and improvement tracking
        logger: StructuredLogger for structured logging
        config: Configuration dict with gear3.ever_thinker section
        project_state: ProjectState for tracking task execution status
        daemon_thread: Background daemon thread
        running: Event indicating daemon is running
        shutdown_event: Event to signal graceful shutdown
        last_activity_time: Timestamp of last task activity for idle detection
        max_cycles: Maximum improvement cycles per project (from config)
        idle_threshold_seconds: Idle time threshold before starting analysis (from config)
        perspectives: List of analysis perspectives to use (from config)
        polling_interval: Seconds between idle checks (default 60)
    """

    def __init__(
        self,
        message_bus: MessageBus,
        learning_db: 'LearningDB',  # Type hint as string to avoid circular import
        project_state: ProjectState,
        logger: StructuredLogger,
        config: dict
    ):
        """
        Initialize Ever-Thinker Agent.

        Args:
            message_bus: MessageBus instance for communication
            learning_db: LearningDB instance for pattern queries (Story 3.6)
            project_state: ProjectState for tracking task execution
            logger: StructuredLogger instance
            config: Configuration dict containing gear3.ever_thinker section
        """
        # Initialize base agent
        super().__init__(
            agent_id="ever-thinker",
            message_bus=message_bus,
            logger=logger
        )

        # Store references
        self.learning_db = learning_db
        self.project_state = project_state
        self.config = config

        # Load configuration with defaults (AC 3.1.6)
        ever_thinker_config = config.get('gear3', {}).get('ever_thinker', {})
        self.enabled = ever_thinker_config.get('enabled', False)
        self.max_cycles = ever_thinker_config.get('max_cycles', 3)
        self.idle_threshold_seconds = ever_thinker_config.get('idle_threshold_seconds', 300)
        self.perspectives = ever_thinker_config.get('perspectives', [
            'performance',
            'code_quality',
            'testing',
            'documentation',
            'ux',
            'architecture'
        ])

        # Validate configuration
        if self.max_cycles <= 0:
            raise ValueError(f"max_cycles must be > 0, got {self.max_cycles}")

        # Threading components (AC 3.1.2, 3.1.5)
        self.daemon_thread: Optional[threading.Thread] = None
        self.running = threading.Event()
        self.shutdown_event = threading.Event()

        # Idle detection state (AC 3.1.3)
        self.last_activity_time = time.time()
        self.polling_interval = 60  # Seconds between idle checks

        # Improvement cycle tracking (Story 3.5 - AC 3.5.3)
        self.cycle_count = 0  # Tracks improvement cycles for max_cycles enforcement
        self.improvement_cycle_count = 0  # Same as cycle_count, clearer name for AC 3.5.3

        # Initialize analyzers (Story 3.5 - AC 3.5.4, 3.5.5)
        self.analyzers = [
            PerformanceAnalyzer(),
            CodeQualityAnalyzer(),
            TestingAnalyzer(),
            DocumentationAnalyzer(),
            UXAnalyzer(),
            ArchitectureAnalyzer()
        ]

        # Initialize improvement tracker (Story 3.6 - AC 3.6.3)
        self.improvement_tracker = ImprovementTracker(learning_db)

        # Log initialization
        self.logger.info(
            component=self.agent_id,
            action="ever_thinker_initialized",
            enabled=self.enabled,
            max_cycles=self.max_cycles,
            idle_threshold_seconds=self.idle_threshold_seconds,
            perspectives=self.perspectives,
            analyzer_count=len(self.analyzers)
        )

    def start(self):
        """
        Start the Ever-Thinker agent and daemon thread (AC 3.1.2).

        Creates and starts the background daemon thread that polls for idle time
        and runs improvement cycles. Thread is marked as daemon (daemon=True) so
        it doesn't block main thread exit.

        Overrides BaseAgent.start() to add daemon thread initialization.
        """
        # Call parent start (sets is_running, sends AGENT_READY message)
        super().start()

        # Only start daemon if enabled in config
        if not self.enabled:
            self.logger.info(
                component=self.agent_id,
                action="daemon_not_started",
                reason="ever_thinker.enabled=false"
            )
            return

        # Create daemon thread (AC 3.1.5)
        self.daemon_thread = threading.Thread(
            target=self._run_daemon_loop,
            daemon=True,  # Critical: daemon thread doesn't block main exit
            name="ever-thinker-daemon"
        )

        # Set running event
        self.running.set()

        # Start daemon thread
        self.daemon_thread.start()

        self.logger.info(
            component=self.agent_id,
            action="daemon_started",
            thread_name=self.daemon_thread.name,
            is_daemon=self.daemon_thread.daemon
        )

    def stop(self):
        """
        Stop the Ever-Thinker agent and daemon thread (AC 3.1.4).

        Sets shutdown event and waits for daemon thread to exit within 5-second
        timeout. Ensures graceful shutdown without orphaned threads.

        Overrides BaseAgent.stop() to add daemon thread cleanup.
        """
        # Signal shutdown to daemon thread
        self.shutdown_event.set()
        self.running.clear()

        self.logger.info(
            component=self.agent_id,
            action="shutdown_initiated"
        )

        # Wait for daemon thread to exit (5 second timeout per AC 3.1.4)
        if self.daemon_thread and self.daemon_thread.is_alive():
            self.daemon_thread.join(timeout=5.0)

            if self.daemon_thread.is_alive():
                # Thread didn't exit within timeout - log warning
                self.logger.warn(
                    component=self.agent_id,
                    action="daemon_shutdown_timeout",
                    message="Daemon thread did not exit within 5 seconds"
                )
            else:
                self.logger.info(
                    component=self.agent_id,
                    action="daemon_stopped"
                )

        # Call parent stop (sets is_running=False, unsubscribes from message bus)
        super().stop()

    def _run_daemon_loop(self):
        """
        Main daemon loop - polls for idle time and runs improvement cycles (AC 3.1.2).

        Runs in background daemon thread. Polls every polling_interval seconds
        to check if system is idle. When idle threshold is met, runs improvement
        cycle. Continues until shutdown_event is set.

        This method should never be called directly - only via daemon thread.
        """
        self.logger.info(
            component=self.agent_id,
            action="daemon_loop_started",
            polling_interval=self.polling_interval
        )

        while not self.shutdown_event.is_set():
            try:
                # Check if system is idle (AC 3.1.3)
                if self._detect_idle_time():
                    self.logger.info(
                        component=self.agent_id,
                        action="idle_detected",
                        idle_duration=time.time() - self.last_activity_time
                    )

                    # Run improvement cycle (placeholder for Story 3.5)
                    self._run_improvement_cycle()

                # Sleep until next poll
                self.shutdown_event.wait(timeout=self.polling_interval)

            except Exception as e:
                # Log error but don't crash daemon
                self.logger.error(
                    component=self.agent_id,
                    action="daemon_loop_error",
                    error=str(e),
                    error_type=type(e).__name__
                )

                # Sleep before retrying
                self.shutdown_event.wait(timeout=self.polling_interval)

        self.logger.info(
            component=self.agent_id,
            action="daemon_loop_exited"
        )

    def _detect_idle_time(self) -> bool:
        """
        Detect if system is idle (AC 3.1.3).

        System is considered idle when:
        1. No tasks are currently executing (status != RUNNING)
        2. Idle time >= idle_threshold_seconds

        Returns:
            True if system has been idle for at least idle_threshold_seconds,
            False otherwise
        """
        # Check if any tasks are currently executing
        executing_tasks = [
            task for task in self.project_state.tasks
            if task.status == TaskStatus.RUNNING
        ]

        if executing_tasks:
            # Tasks are executing - update activity time and return False
            self.last_activity_time = time.time()
            return False

        # No tasks executing - check idle duration
        idle_duration = time.time() - self.last_activity_time

        return idle_duration >= self.idle_threshold_seconds

    def calculate_priority_score(self, improvement: Improvement) -> float:
        """
        Calculate priority score for an improvement (AC 3.5.2).

        Uses the formula:
            score = impact_weight[improvement.impact] +
                    effort_weight[improvement.effort] +
                    (acceptance_rate * 5)

        Where:
        - impact_weight: {'critical': 10, 'high': 7, 'medium': 4, 'low': 1}
        - effort_weight: {'trivial': 5, 'small': 3, 'medium': 1, 'large': -2}
        - acceptance_rate: Historical acceptance rate from learning system (0.0 to 1.0)

        Args:
            improvement: Improvement object with impact, effort, and type fields

        Returns:
            Float score (higher is better priority)
        """
        # Impact weight mapping (AC 3.5.2)
        impact_weight = {
            'critical': 10,
            'high': 7,
            'medium': 4,
            'low': 1
        }

        # Effort weight mapping - lower effort = higher priority (AC 3.5.2)
        effort_weight = {
            'trivial': 5,
            'small': 3,
            'medium': 1,
            'large': -2
        }

        # Query learning system for historical acceptance rate
        try:
            acceptance_rate = self.learning_db.get_acceptance_rate(improvement.improvement_type)
        except Exception as e:
            # If learning system query fails, use default rate of 0.5
            print(f"Warning: Failed to query learning system for acceptance rate: {e}")
            acceptance_rate = 0.5

        # Calculate score using formula from tech spec (AC 3.5.2)
        score = (
            impact_weight.get(improvement.impact, 1) +
            effort_weight.get(improvement.effort, 1) +
            (acceptance_rate * 5)
        )

        return score

    def run_all_analyzers(self, task: Task) -> list[Improvement]:
        """
        Run all 6 analyzers in parallel with fault isolation (AC 3.5.4, 3.5.5).

        Executes all analyzer.analyze(task) calls concurrently using ThreadPoolExecutor.
        Each analyzer is wrapped in try/except to ensure one analyzer failure doesn't
        crash the entire cycle (fault isolation).

        Args:
            task: Completed task to analyze for improvements

        Returns:
            Combined list of improvements from all successful analyzers
        """
        improvements = []

        # Run analyzers in parallel using ThreadPoolExecutor (AC 3.5.4)
        with ThreadPoolExecutor(max_workers=6) as executor:
            # Submit all analyzer jobs
            future_to_analyzer = {
                executor.submit(analyzer.analyze, task): analyzer
                for analyzer in self.analyzers
            }

            # Collect results as they complete
            for future in as_completed(future_to_analyzer):
                analyzer = future_to_analyzer[future]
                try:
                    # Get results from analyzer (AC 3.5.5 - fault isolation)
                    results = future.result()
                    improvements.extend(results)

                    print(f"Analyzer {analyzer.analyzer_name} found {len(results)} improvements")

                except Exception as e:
                    # Fault isolation - log error but continue with other analyzers (AC 3.5.5)
                    print(f"Analyzer {analyzer.analyzer_name} failed: {e}")
                    self.logger.error(
                        component=self.agent_id,
                        action="analyzer_failed",
                        analyzer=analyzer.analyzer_name,
                        error=str(e),
                        error_type=type(e).__name__
                    )

        return improvements

    def _run_improvement_cycle(self):
        """
        Run single improvement cycle (AC 3.5.1).

        Complete workflow:
        1. Check if max_cycles limit reached (AC 3.5.3)
        2. Detect idle time
        3. Select recently completed task for analysis
        4. Run all 6 analyzers in parallel (AC 3.5.4)
        5. Collect and score improvements using priority algorithm (AC 3.5.2)
        6. Create PR for top priority improvement
        7. Publish IMPROVEMENT_PROPOSAL message
        8. Wait for IMPROVEMENT_FEEDBACK message (handled in handle_message)
        9. Update learning system with acceptance/rejection outcome

        This method implements the full improvement cycle workflow from the tech spec.
        """
        start_time = time.time()

        # Increment cycle counter (AC 3.5.3)
        self.cycle_count += 1
        self.improvement_cycle_count += 1

        # Check if max cycles reached BEFORE running cycle (AC 3.5.3)
        if self.improvement_cycle_count > self.max_cycles:
            print(f"Max improvement cycles ({self.max_cycles}) reached - stopping")
            self.logger.info(
                component=self.agent_id,
                action="max_cycles_reached",
                improvement_cycle_count=self.improvement_cycle_count,
                max_cycles=self.max_cycles
            )
            return  # Stop running cycles

        # Log cycle start using Gear 3 EventType (Story 1.2)
        self.logger.log_improvement_cycle_start(
            cycle_number=self.cycle_count,
            analysis_perspectives=self.perspectives,
            task_id=None  # No specific task selected yet
        )

        print(f"Starting improvement cycle #{self.improvement_cycle_count}")

        # Step 2: Select recently completed task for analysis (AC 3.5.1)
        # For now, use a placeholder task - Story 3.6 will integrate with actual task history
        # TODO Story 3.6: Select from actual task history
        completed_tasks = [
            task for task in self.project_state.tasks
            if task.status == TaskStatus.COMPLETED
        ]

        if not completed_tasks:
            print("No completed tasks found for analysis")
            self.logger.info(
                component=self.agent_id,
                action="no_completed_tasks",
                cycle_number=self.cycle_count
            )
            return

        # Select most recently completed task
        task_to_analyze = completed_tasks[-1]

        # Step 3: Run all 6 analyzers in parallel (AC 3.5.1, 3.5.4, 3.5.5)
        print(f"Running 6 analyzers in parallel on task: {task_to_analyze.id}")
        improvements = self.run_all_analyzers(task_to_analyze)

        print(f"Total improvements found: {len(improvements)}")

        # If no improvements found, log and exit
        if not improvements:
            print("No improvements found in this cycle")
            self.logger.info(
                component=self.agent_id,
                action="no_improvements_found",
                cycle_number=self.cycle_count,
                task_id=task_to_analyze.id
            )

            # Log cycle complete
            self.logger.log_improvement_cycle_complete(
                cycle_number=self.cycle_count,
                improvements_found=0,
                time_taken=time.time() - start_time,
                task_id=task_to_analyze.id
            )
            return

        # Step 4: Score each improvement using priority algorithm (AC 3.5.1, 3.5.2)
        print("Scoring improvements...")
        for improvement in improvements:
            improvement.score = self.calculate_priority_score(improvement)

        # Step 5: Sort by score (high → low)
        improvements.sort(key=lambda imp: imp.score, reverse=True)

        # Step 5.5: Filter out recently rejected improvements (AC 3.6.2)
        filtered_improvements = []
        with self.learning_db as db:
            for improvement in improvements:
                try:
                    # Check if similar improvement was rejected in last 30 days
                    was_rejected_recently = db.check_recent_rejection(
                        improvement_type=improvement.improvement_type.value,
                        target_file=improvement.target_file,
                        days_back=30
                    )

                    if was_rejected_recently:
                        print(f"Skipping improvement '{improvement.title}' - similar improvement rejected recently")
                        self.logger.info(
                            component=self.agent_id,
                            action="improvement_filtered",
                            improvement_id=improvement.improvement_id,
                            improvement_type=improvement.improvement_type.value,
                            target_file=improvement.target_file,
                            reason="similar_improvement_rejected_recently"
                        )
                    else:
                        filtered_improvements.append(improvement)
                except Exception as e:
                    # Graceful degradation (AC 3.6.5): On error, allow the proposal
                    print(f"Warning: Failed to check recent rejections for '{improvement.title}': {e}")
                    self.logger.warn(
                        component=self.agent_id,
                        action="learning_system_degraded",
                        operation="check_recent_rejection",
                        improvement_id=improvement.improvement_id,
                        error=str(e),
                        degraded_behavior="allowing_proposal"
                    )
                    filtered_improvements.append(improvement)

        # If all improvements were filtered out, exit
        if not filtered_improvements:
            print("All improvements were filtered (recently rejected)")
            self.logger.info(
                component=self.agent_id,
                action="all_improvements_filtered",
                cycle_number=self.cycle_count,
                original_count=len(improvements)
            )
            return

        # Get top priority improvement from filtered list
        top_improvement = filtered_improvements[0]

        print(f"Top improvement: {top_improvement.title} (score: {top_improvement.score:.2f})")
        print(f"Improvements considered: {len(improvements)}, Improvements after filtering: {len(filtered_improvements)}")

        # Step 6-8: Create PR and publish IMPROVEMENT_PROPOSAL message (AC 3.5.1)
        # TODO: Integrate with GitManager to actually create PR
        # For now, just publish the message
        self.message_bus.publish(AgentMessage(
            message_type=MessageType.IMPROVEMENT_PROPOSAL,
            from_agent=self.agent_id,
            to_agent="moderator",
            payload={
                'improvement_id': top_improvement.improvement_id,
                'improvement_type': top_improvement.improvement_type.value,
                'priority': top_improvement.priority.value,
                'target_file': top_improvement.target_file,
                'title': top_improvement.title,
                'description': top_improvement.description,
                'proposed_changes': top_improvement.proposed_changes,
                'rationale': top_improvement.rationale,
                'impact': top_improvement.impact,
                'effort': top_improvement.effort,
                'score': top_improvement.score
            }
        ))

        print(f"Published IMPROVEMENT_PROPOSAL for improvement: {top_improvement.improvement_id}")

        # Note: Steps 7-9 (wait for feedback, update learning system) happen in handle_message()
        # when IMPROVEMENT_FEEDBACK is received (Story 3.6 integration)

        # Log cycle complete
        time_taken = time.time() - start_time
        self.logger.log_improvement_cycle_complete(
            cycle_number=self.cycle_count,
            improvements_found=len(improvements),
            time_taken=time_taken,
            task_id=task_to_analyze.id
        )

        print(f"Improvement cycle #{self.cycle_count} complete (took {time_taken:.2f}s)")

    def handle_message(self, message: AgentMessage):
        """
        Handle incoming messages from message bus.

        Implements abstract method from BaseAgent. Handles IMPROVEMENT_FEEDBACK
        messages to record improvement outcomes in learning system (Story 3.6).

        Args:
            message: Incoming AgentMessage
        """
        self.logger.debug(
            component=self.agent_id,
            action="message_received",
            message_type=message.message_type.value,
            message_id=message.message_id,
            from_agent=message.from_agent
        )

        # Handle IMPROVEMENT_FEEDBACK messages (Story 3.6 - AC 3.6.3)
        if message.message_type == MessageType.IMPROVEMENT_FEEDBACK:
            try:
                # Extract payload fields
                improvement_id = message.payload.get('improvement_id')
                accepted = message.payload.get('accepted')
                reason = message.payload.get('reason', '')

                # Validate required fields
                if improvement_id is None or accepted is None:
                    self.logger.error(
                        component=self.agent_id,
                        action="invalid_improvement_feedback",
                        message_id=message.message_id,
                        payload=message.payload,
                        error="Missing required fields: improvement_id or accepted"
                    )
                    return

                # Record outcome in learning system
                if accepted:
                    # Record acceptance with PR number (if available)
                    pr_number = message.payload.get('pr_number', 0)
                    self.improvement_tracker.record_acceptance(improvement_id, pr_number)
                    print(f"Improvement {improvement_id} accepted - recorded in learning system")
                else:
                    # Record rejection with reason
                    self.improvement_tracker.record_rejection(improvement_id, reason)
                    print(f"Improvement {improvement_id} rejected: {reason}")

                # Log outcome with structured logger (AC 3.6.3)
                self.logger.info(
                    component=self.agent_id,
                    action="improvement_feedback_processed",
                    improvement_id=improvement_id,
                    accepted=accepted,
                    reason=reason,
                    from_agent=message.from_agent
                )

            except Exception as e:
                # Graceful degradation (AC 3.6.5): Log error but don't crash daemon
                print(f"Error processing IMPROVEMENT_FEEDBACK: {e}")
                self.logger.error(
                    component=self.agent_id,
                    action="improvement_feedback_error",
                    message_id=message.message_id,
                    error=str(e),
                    error_type=type(e).__name__,
                    degraded_behavior="continuing_without_recording"
                )
        else:
            # Log other message types
            self.logger.info(
                component=self.agent_id,
                action="message_received",
                message_type=message.message_type.value,
                message="Message type not yet handled by Ever-Thinker"
            )
