"""
Monitor Agent for system health metrics collection (Story 6.1).

This agent runs as a background daemon collecting metrics from EventBus messages
and persisting them to LearningDB for health monitoring and trend analysis.
"""

import threading
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from collections import defaultdict

from .base_agent import BaseAgent
from ..communication.message_bus import MessageBus
from ..communication.messages import AgentMessage, MessageType
from ..logger import StructuredLogger
from ..models import Metric, MetricType, HealthStatus, Alert
from ..health.health_scorer import HealthScoreCalculator
from ..health.anomaly_detector import AnomalyDetector


class MonitorAgent(BaseAgent):
    """
    Monitor Agent - Collects and persists system health metrics.

    Responsibilities:
    - Subscribe to EventBus for TASK_*, PR_*, QA_* events
    - Calculate metrics (success rate, error rate, execution time, etc.)
    - Persist metrics to LearningDB
    - Run background daemon thread for periodic collection

    Configuration (gear3.monitoring):
        enabled: bool - Toggle monitoring on/off
        collection_interval: int - Seconds between metric collections
        metrics_window_hours: int - Time window for metric calculations
        metrics: list[str] - List of metrics to collect

    Example:
        >>> config = {
        ...     'gear3': {
        ...         'monitoring': {
        ...             'enabled': true,
        ...             'collection_interval': 300,
        ...             'metrics_window_hours': 24,
        ...             'metrics': ['task_success_rate', 'task_error_rate']
        ...         }
        ...     }
        ... }
        >>> agent = MonitorAgent("monitor", message_bus, learning_db, logger, config)
        >>> agent.start()
    """

    def __init__(
        self,
        agent_id: str,
        message_bus: MessageBus,
        learning_db,  # LearningDB instance
        logger: StructuredLogger,
        config: dict
    ):
        """
        Initialize MonitorAgent.

        Args:
            agent_id: Unique identifier for this agent (typically "monitor")
            message_bus: MessageBus instance for event subscription
            learning_db: LearningDB instance for metric persistence
            logger: StructuredLogger instance
            config: Configuration dictionary with gear3.monitoring section
        """
        super().__init__(agent_id, message_bus, logger)

        self.learning_db = learning_db
        self.config = config

        # Load configuration from gear3.monitoring section
        monitoring_config = config.get('gear3', {}).get('monitoring', {})
        self.enabled = monitoring_config.get('enabled', False)
        self.collection_interval = monitoring_config.get('collection_interval', 300)  # 5 minutes
        self.metrics_window_hours = monitoring_config.get('metrics_window_hours', 24)
        self.configured_metrics = monitoring_config.get('metrics', [
            'task_success_rate',
            'task_error_rate',
            'average_execution_time',
            'pr_approval_rate',
            'qa_score_average'
        ])

        # Health score configuration (Story 6.2)
        health_score_config = monitoring_config.get('health_score', {})
        self.health_score_enabled = health_score_config.get('enabled', False)

        # Initialize HealthScoreCalculator with custom config if provided
        health_weights = health_score_config.get('weights')
        health_thresholds = health_score_config.get('thresholds')

        # Convert metric names from config to MetricType enum keys if weights provided
        if health_weights:
            # Map string names to MetricType enum
            from ..models import MetricType as MT
            enum_weights = {}
            for metric_name, weight in health_weights.items():
                try:
                    enum_weights[MT(metric_name)] = weight
                except ValueError:
                    self.logger.warn(
                        component=self.agent_id,
                        action="invalid_health_weight_metric",
                        metric=metric_name
                    )
            health_weights = enum_weights if enum_weights else None

        self.health_scorer = HealthScoreCalculator(
            weights=health_weights,
            thresholds=health_thresholds
        )

        # Alert configuration (Story 6.3)
        alerts_config = monitoring_config.get('alerts', {})
        self.alerts_enabled = alerts_config.get('enabled', False)

        # Initialize AnomalyDetector with custom config if provided
        thresholds_min_config = alerts_config.get('thresholds', {})
        thresholds_max_config = alerts_config.get('thresholds', {})
        severity_levels_config = alerts_config.get('severity_levels', {})

        # Extract min/max thresholds and convert to MetricType enums
        thresholds_min = {}
        thresholds_max = {}
        severity_levels = {}

        if thresholds_min_config:
            from ..models import MetricType as MT
            for key, value in thresholds_min_config.items():
                if key.endswith('_min'):
                    metric_name = key[:-4]  # Remove '_min' suffix
                    try:
                        thresholds_min[MT(metric_name)] = value
                    except ValueError:
                        pass  # Skip unknown metric types

            for key, value in thresholds_max_config.items():
                if key.endswith('_max'):
                    metric_name = key[:-4]  # Remove '_max' suffix
                    try:
                        thresholds_max[MT(metric_name)] = value
                    except ValueError:
                        pass  # Skip unknown metric types

        # Convert severity levels to MetricType enums
        if severity_levels_config:
            from ..models import MetricType as MT
            for metric_name, severity in severity_levels_config.items():
                try:
                    severity_levels[MT(metric_name)] = severity
                except ValueError:
                    pass  # Skip unknown metric types

        qa_score_min = thresholds_min_config.get('qa_score_average_min')
        suppression_window = alerts_config.get('suppression_window_minutes')
        sustained_violations = alerts_config.get('sustained_violations_required')

        self.anomaly_detector = AnomalyDetector(
            thresholds_min=thresholds_min if thresholds_min else None,
            thresholds_max=thresholds_max if thresholds_max else None,
            qa_score_min=qa_score_min,
            severity_levels=severity_levels if severity_levels else None,
            suppression_window_minutes=suppression_window,
            sustained_violations_required=sustained_violations
        )

        # Event cache for metric calculations (in-memory)
        self._event_cache: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._cache_lock = threading.Lock()

        # Daemon thread for periodic metric collection
        self._collection_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()
        self._running = False

        # Health check tracking (Story 6.4, AC 6.4.3)
        self._start_time: Optional[datetime] = None
        self._last_collection_time: Optional[datetime] = None
        self._metrics_collected_count: int = 0
        self._error_message: Optional[str] = None

        self.logger.info(
            component=self.agent_id,
            action="monitor_agent_initialized",
            enabled=self.enabled,
            collection_interval=self.collection_interval,
            configured_metrics=self.configured_metrics
        )

    def start(self):
        """
        Start the MonitorAgent.

        Subscribes to EventBus messages and starts the background collection daemon
        if monitoring is enabled.
        """
        super().start()

        # Track start time for health check uptime (Story 6.4, AC 6.4.3)
        self._start_time = datetime.now()
        self._error_message = None

        if not self.enabled:
            self.logger.info(
                component=self.agent_id,
                action="monitoring_disabled",
                message="MonitorAgent started but monitoring is disabled in config"
            )
            return

        # Subscribe to EventBus message types
        self._subscribe_to_events()

        # Start daemon thread for periodic metric collection
        self._running = True
        self._shutdown_event.clear()
        self._collection_thread = threading.Thread(
            target=self._run_collection_loop,
            daemon=True,
            name="monitor-agent-daemon"
        )
        self._collection_thread.start()

        self.logger.info(
            component=self.agent_id,
            action="collection_daemon_started",
            interval=self.collection_interval
        )

    def stop(self):
        """
        Stop the MonitorAgent.

        Gracefully shuts down the collection daemon thread within 5 seconds.
        """
        if not self.enabled or not self._running:
            super().stop()
            return

        self.logger.info(
            component=self.agent_id,
            action="stopping_monitor_agent"
        )

        # Signal shutdown and wait for daemon thread to exit
        self._running = False
        self._shutdown_event.set()

        if self._collection_thread and self._collection_thread.is_alive():
            self._collection_thread.join(timeout=5)  # 5 second timeout per AC 6.1.7

            if self._collection_thread.is_alive():
                self.logger.warn(
                    component=self.agent_id,
                    action="daemon_shutdown_timeout",
                    message="Collection thread did not exit within 5 seconds"
                )

        super().stop()

        self.logger.info(
            component=self.agent_id,
            action="monitor_agent_stopped"
        )

    def get_status(self) -> dict:
        """
        Get current status of MonitorAgent.

        Returns:
            dict: Status information including enabled state, running state, cache size
        """
        status = {
            'agent_id': self.agent_id,
            'enabled': self.enabled,
            'running': self._running,
            'daemon_alive': self._collection_thread.is_alive() if self._collection_thread else False,
            'collection_interval': self.collection_interval,
            'configured_metrics': self.configured_metrics,
            'cached_events': {
                event_type: len(events)
                for event_type, events in self._event_cache.items()
            }
        }
        return status

    def handle_message(self, message: AgentMessage):
        """
        Handle incoming EventBus messages.

        Extracts relevant metrics data and caches for periodic calculation.

        Args:
            message: AgentMessage from EventBus
        """
        if not self.enabled:
            return

        # Route to appropriate handler based on message type
        handlers = {
            MessageType.TASK_STARTED: self._handle_task_started,
            MessageType.TASK_COMPLETED: self._handle_task_completed,
            MessageType.TASK_FAILED: self._handle_task_failed,
            MessageType.PR_CREATED: self._handle_pr_event,
            MessageType.PR_APPROVED: self._handle_pr_event,
            MessageType.PR_REJECTED: self._handle_pr_event,
            # QA_CHECK_COMPLETED will be added when Epic 4 is integrated
        }

        handler = handlers.get(message.message_type)
        if handler:
            try:
                handler(message)
            except Exception as e:
                self.logger.error(
                    component=self.agent_id,
                    action="message_handler_error",
                    message_type=message.message_type.value,
                    error=str(e)
                )

    def _subscribe_to_events(self):
        """Subscribe to EventBus message types for metric collection (AC 6.1.2)."""
        # EventBus subscription happens via BaseAgent's message bus subscription
        # The message bus routes messages to handle_message() based on subscriptions
        self.logger.info(
            component=self.agent_id,
            action="subscribed_to_events",
            message_types=[
                "TASK_STARTED", "TASK_COMPLETED", "TASK_FAILED",
                "PR_CREATED", "PR_APPROVED", "PR_REJECTED"
            ]
        )

    def _handle_task_started(self, message: AgentMessage):
        """Extract task start time for execution time calculation."""
        with self._cache_lock:
            self._event_cache['task_started'].append({
                'task_id': message.payload.get('task_id'),
                'timestamp': message.timestamp,
                'data': message.payload
            })

    def _handle_task_completed(self, message: AgentMessage):
        """Extract task completion for success rate calculation."""
        with self._cache_lock:
            self._event_cache['task_completed'].append({
                'task_id': message.payload.get('task_id'),
                'timestamp': message.timestamp,
                'duration': message.payload.get('duration'),
                'data': message.payload
            })

    def _handle_task_failed(self, message: AgentMessage):
        """Extract task failure for error rate calculation."""
        with self._cache_lock:
            self._event_cache['task_failed'].append({
                'task_id': message.payload.get('task_id'),
                'timestamp': message.timestamp,
                'error': message.payload.get('error'),
                'data': message.payload
            })

    def _handle_pr_event(self, message: AgentMessage):
        """Extract PR events for approval rate calculation."""
        with self._cache_lock:
            event_type = message.message_type.value
            self._event_cache['pr_events'].append({
                'pr_number': message.payload.get('pr_number'),
                'event_type': event_type,
                'timestamp': message.timestamp,
                'data': message.payload
            })

    def _run_collection_loop(self):
        """
        Background daemon loop that periodically collects and persists metrics (AC 6.1.7).

        Runs at configured interval until shutdown event is signaled.
        """
        self.logger.info(
            component=self.agent_id,
            action="collection_loop_started",
            interval=self.collection_interval
        )

        while self._running and not self._shutdown_event.is_set():
            try:
                # Sleep with early exit on shutdown
                if self._shutdown_event.wait(timeout=self.collection_interval):
                    break  # Shutdown signaled

                # Collect and persist metrics
                self._collect_metrics()

            except Exception as e:
                self.logger.error(
                    component=self.agent_id,
                    action="collection_loop_error",
                    error=str(e)
                )
                # Continue running despite errors

        self.logger.info(
            component=self.agent_id,
            action="collection_loop_exited"
        )

    def _collect_metrics(self):
        """
        Calculate all configured metrics and persist to database (AC 6.1.4, 6.1.5).

        This is called periodically by the daemon thread.
        """
        self.logger.debug(
            component=self.agent_id,
            action="collecting_metrics"
        )

        metrics_to_persist = []

        # Calculate each configured metric
        for metric_name in self.configured_metrics:
            try:
                metric = self._calculate_metric(metric_name)
                if metric:
                    metrics_to_persist.append(metric)
            except Exception as e:
                self.logger.error(
                    component=self.agent_id,
                    action="metric_calculation_error",
                    metric=metric_name,
                    error=str(e)
                )

        # Persist all metrics to database
        for metric in metrics_to_persist:
            try:
                self.learning_db.record_metric(metric)
            except Exception as e:
                self.logger.error(
                    component=self.agent_id,
                    action="metric_persistence_error",
                    metric_id=metric.metric_id,
                    error=str(e)
                )

        if metrics_to_persist:
            self.logger.info(
                component=self.agent_id,
                action="metrics_collected",
                count=len(metrics_to_persist)
            )

            # Calculate and persist health score if enabled (Story 6.2, AC 6.2.3)
            if self.health_score_enabled:
                try:
                    self._calculate_and_persist_health_score(metrics_to_persist)
                except Exception as e:
                    self.logger.error(
                        component=self.agent_id,
                        action="health_score_calculation_error",
                        error=str(e)
                    )

            # Check thresholds and generate alerts if enabled (Story 6.3, AC 6.3.3)
            if self.alerts_enabled:
                try:
                    self._check_thresholds_and_generate_alerts(metrics_to_persist)
                except Exception as e:
                    self.logger.error(
                        component=self.agent_id,
                        action="alert_generation_error",
                        error=str(e)
                    )

        # Update health check tracking (Story 6.4, AC 6.4.3)
        self._last_collection_time = datetime.now()
        self._metrics_collected_count += len(metrics_to_persist)

    def _calculate_metric(self, metric_name: str) -> Optional[Metric]:
        """
        Calculate a single metric from cached events (AC 6.1.4).

        Args:
            metric_name: Name of metric to calculate

        Returns:
            Metric object or None if calculation not possible
        """
        calculators = {
            'task_success_rate': self.calculate_task_success_rate,
            'task_error_rate': self.calculate_task_error_rate,
            'average_execution_time': self.calculate_average_execution_time,
            'pr_approval_rate': self.calculate_pr_approval_rate,
            'qa_score_average': self.calculate_qa_score_average
        }

        calculator = calculators.get(metric_name)
        if not calculator:
            self.logger.warn(
                component=self.agent_id,
                action="unknown_metric",
                metric=metric_name
            )
            return None

        return calculator()

    def calculate_task_success_rate(self) -> Optional[Metric]:
        """
        Calculate percentage of tasks completed successfully (AC 6.1.4).

        Returns:
            Metric with success rate (0.0-1.0) or None if no data
        """
        with self._cache_lock:
            completed = len(self._event_cache['task_completed'])
            failed = len(self._event_cache['task_failed'])

        total = completed + failed
        if total == 0:
            return None  # No data available

        success_rate = completed / total

        return Metric(
            metric_id=f"metric_{uuid.uuid4().hex[:12]}",
            metric_type=MetricType.TASK_SUCCESS_RATE,
            value=success_rate,
            context={'completed': completed, 'failed': failed, 'total': total}
        )

    def calculate_task_error_rate(self) -> Optional[Metric]:
        """
        Calculate percentage of tasks that failed (AC 6.1.4).

        Returns:
            Metric with error rate (0.0-1.0) or None if no data
        """
        with self._cache_lock:
            completed = len(self._event_cache['task_completed'])
            failed = len(self._event_cache['task_failed'])

        total = completed + failed
        if total == 0:
            return None

        error_rate = failed / total

        return Metric(
            metric_id=f"metric_{uuid.uuid4().hex[:12]}",
            metric_type=MetricType.TASK_ERROR_RATE,
            value=error_rate,
            context={'completed': completed, 'failed': failed, 'total': total}
        )

    def calculate_average_execution_time(self) -> Optional[Metric]:
        """
        Calculate mean task execution duration (AC 6.1.4).

        Returns:
            Metric with average duration in seconds or None if no data
        """
        with self._cache_lock:
            completed_tasks = self._event_cache['task_completed']

        if not completed_tasks:
            return None

        # Extract durations from completed tasks
        durations = [
            task.get('duration', 0)
            for task in completed_tasks
            if task.get('duration') is not None
        ]

        if not durations:
            return None

        avg_duration = sum(durations) / len(durations)

        return Metric(
            metric_id=f"metric_{uuid.uuid4().hex[:12]}",
            metric_type=MetricType.AVERAGE_EXECUTION_TIME,
            value=avg_duration,
            context={'task_count': len(durations), 'total_duration': sum(durations)}
        )

    def calculate_pr_approval_rate(self) -> Optional[Metric]:
        """
        Calculate percentage of PRs approved (AC 6.1.4).

        Returns:
            Metric with approval rate (0.0-1.0) or None if no data
        """
        with self._cache_lock:
            pr_events = self._event_cache['pr_events']

        if not pr_events:
            return None

        # Count approved vs rejected PRs
        approved_count = sum(1 for event in pr_events if event['event_type'] == 'pr_approved')
        rejected_count = sum(1 for event in pr_events if event['event_type'] == 'pr_rejected')

        total = approved_count + rejected_count
        if total == 0:
            return None

        approval_rate = approved_count / total

        return Metric(
            metric_id=f"metric_{uuid.uuid4().hex[:12]}",
            metric_type=MetricType.PR_APPROVAL_RATE,
            value=approval_rate,
            context={'approved': approved_count, 'rejected': rejected_count, 'total': total}
        )

    def calculate_qa_score_average(self) -> Optional[Metric]:
        """
        Calculate mean QA scores from recent tasks (AC 6.1.4).

        Note: This will be fully implemented when Epic 4 (QA Integration) is complete.
        For now, returns None as QA_CHECK_COMPLETED messages are not yet available.

        Returns:
            Metric with average QA score or None if no data
        """
        # Placeholder for Epic 4 integration
        # Will subscribe to QA_CHECK_COMPLETED messages and extract QA scores
        return None

    def _calculate_and_persist_health_score(self, metrics: List[Metric]) -> None:
        """
        Calculate health score from collected metrics and persist to database (Story 6.2, AC 6.2.3).

        Called after metrics are collected and persisted. Extracts metric values,
        calculates health score, and stores result with component breakdown.

        Args:
            metrics: List of Metric objects just collected
        """
        # Convert metrics list to dict for HealthScoreCalculator
        metrics_dict = {}
        for metric in metrics:
            if metric:  # Skip None metrics
                metrics_dict[metric.metric_type] = metric.value

        if not metrics_dict:
            self.logger.debug(
                component=self.agent_id,
                action="health_score_skipped",
                reason="no_metrics_available"
            )
            return

        # Calculate health score
        score, status = self.health_scorer.calculate_health_score(metrics_dict)

        # Get component breakdown for storage
        component_scores = self.health_scorer.get_component_scores(metrics_dict)

        # Persist to database
        context = {
            'agent_id': self.agent_id,
            'metrics_count': len(metrics_dict)
        }

        score_id = self.learning_db.record_health_score(
            score=score,
            status=status.value,  # Convert enum to string
            component_scores=component_scores,
            context=context
        )

        # Log event (AC 6.2.3)
        self.logger.info(
            component=self.agent_id,
            action="MONITOR_HEALTH_SCORE_UPDATED",
            score=score,
            status=status.value,
            score_id=score_id
        )

        self.logger.debug(
            component=self.agent_id,
            action="health_score_calculated",
            score=score,
            status=status.value,
            component_count=len(component_scores)
        )

    def _check_thresholds_and_generate_alerts(self, metrics: List[Metric]) -> None:
        """
        Check metrics against thresholds and generate alerts for violations (Story 6.3, AC 6.3.3).

        Called after metrics are collected. Checks each metric against configured thresholds,
        implements sustained violation detection and alert suppression, then persists alerts.

        Args:
            metrics: List of Metric objects just collected
        """
        alerts_generated = []

        for metric in metrics:
            if not metric:  # Skip None metrics
                continue

            # Check metric against thresholds
            alert = self.anomaly_detector.check_metric(
                metric_name=metric.metric_type.value,
                value=metric.value,
                history=None  # Could pass historical values here if needed
            )

            if alert:
                # Persist alert to database
                with self.learning_db as db:
                    alert_id = db.record_alert(
                        alert_id=alert.alert_id,
                        alert_type=alert.alert_type,
                        metric_name=alert.metric_name,
                        threshold_value=alert.threshold_value,
                        actual_value=alert.actual_value,
                        severity=alert.severity,
                        message=alert.message,
                        context=alert.context
                    )

                # Log event (AC 6.3.3)
                self.logger.info(
                    component=self.agent_id,
                    action="MONITOR_ALERT_GENERATED",
                    alert_id=alert.alert_id,
                    metric_name=alert.metric_name,
                    severity=alert.severity,
                    message=alert.message
                )

                alerts_generated.append(alert)

        if alerts_generated:
            self.logger.debug(
                component=self.agent_id,
                action="alerts_generated",
                count=len(alerts_generated)
            )

    # Alert query and management API methods (Story 6.3, AC 6.3.5)

    def get_active_alerts(self) -> List[dict]:
        """
        Get unacknowledged alerts (Story 6.3, AC 6.3.5).

        Returns:
            List of alert dicts with acknowledged=False
        """
        with self.learning_db as db:
            return db.query_alerts(acknowledged=False, limit=100)

    def get_alert_history(self, hours: int = 24) -> List[dict]:
        """
        Get recent alerts within time window (Story 6.3, AC 6.3.5).

        Args:
            hours: Time window in hours (default 24)

        Returns:
            List of alert dicts within time window
        """
        from datetime import datetime, timedelta, UTC

        end_time = datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')
        start_time = (datetime.now(UTC) - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')

        with self.learning_db as db:
            return db.query_alerts(start_time=start_time, end_time=end_time, limit=1000)

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """
        Mark alert as acknowledged (Story 6.3, AC 6.3.5).

        Args:
            alert_id: Alert identifier (UUID)
            acknowledged_by: User/operator who acknowledged

        Returns:
            bool: True if alert was updated, False if not found
        """
        with self.learning_db as db:
            return db.acknowledge_alert(alert_id, acknowledged_by)

    def get_alert_counts_by_severity(self) -> dict[str, int]:
        """
        Get count of unacknowledged alerts by severity level (Story 6.3, AC 6.3.5).

        Returns:
            Dict with severity counts: {'critical': N, 'warning': M}
        """
        with self.learning_db as db:
            all_active = db.query_alerts(acknowledged=False, limit=10000)

        counts = {'critical': 0, 'warning': 0}
        for alert in all_active:
            severity = alert.get('severity', 'warning')
            counts[severity] = counts.get(severity, 0) + 1

        return counts

    def health_check(self) -> dict:
        """
        Check MonitorAgent health status (Story 6.4, AC 6.4.3).

        Returns:
            Dictionary containing health status information:
            {
                "agent_id": str,
                "status": "running" | "stopped" | "error",
                "last_collection": ISO timestamp or None,
                "metrics_collected": int,
                "uptime_seconds": float,
                "error_message": str | None
            }
        """
        # Calculate uptime
        uptime_seconds = 0.0
        if self._start_time:
            uptime_seconds = (datetime.now() - self._start_time).total_seconds()

        # Determine status
        status = "stopped"
        if self._running:
            if self._error_message:
                status = "error"
            else:
                status = "running"

        # Format last collection time
        last_collection = None
        if self._last_collection_time:
            last_collection = self._last_collection_time.isoformat()

        return {
            "agent_id": self.agent_id,
            "status": status,
            "last_collection": last_collection,
            "metrics_collected": self._metrics_collected_count,
            "uptime_seconds": uptime_seconds,
            "error_message": self._error_message
        }

    # Dashboard Query API (Story 6.5)

    def get_current_health(self) -> dict | None:
        """
        Query latest health status with score and component breakdown (Story 6.5, AC 6.5.1).

        Returns:
            Dictionary with current health status:
            {
                "health_score": float (0-100),
                "status": "healthy" | "degraded" | "critical",
                "timestamp": ISO timestamp,
                "component_scores": {
                    "task_success_rate": float,
                    "task_error_rate": float,
                    "average_execution_time": float,
                    "pr_approval_rate": float,
                    "qa_score_average": float
                },
                "metrics_count": int
            }
            or None if no health scores exist
        """
        with self.learning_db as db:
            health_scores = db.query_health_scores(limit=1)

        if not health_scores:
            return None

        # Latest health score (first result)
        latest = health_scores[0]

        # Parse component_scores JSON if it's a string
        import json
        component_scores = latest.get('component_scores')
        if isinstance(component_scores, str):
            component_scores = json.loads(component_scores)

        return {
            "health_score": latest['score'],
            "status": latest['status'],
            "timestamp": latest['timestamp'],
            "component_scores": component_scores or {},
            "metrics_count": len(component_scores) if component_scores else 0
        }

    def get_metrics_history(
        self,
        metric_type: str | None = None,
        hours: int = 24,
        limit: int = 100
    ) -> list[dict]:
        """
        Query historical metrics with time window filtering (Story 6.5, AC 6.5.2).

        Args:
            metric_type: Specific metric type to query (e.g., 'task_success_rate') or None for all
            hours: Time window in hours (default: 24)
            limit: Maximum results to return (default: 100)

        Returns:
            List of metric dictionaries ordered by timestamp DESC (newest first):
            [
                {
                    "metric_type": str,
                    "value": float,
                    "timestamp": ISO timestamp,
                    "context": dict
                },
                ...
            ]
        """
        # Calculate start time
        start_time = (datetime.now() - timedelta(hours=hours)).isoformat()

        # Query metrics from database
        with self.learning_db as db:
            metrics = db.query_metrics(
                metric_type=metric_type,
                start_time=start_time,
                end_time=None,
                limit=limit
            )

        # Convert Metric objects to dictionaries
        import json
        result = []
        for metric in metrics:
            result.append({
                "metric_type": metric.metric_type.value,
                "value": metric.value,
                "timestamp": metric.timestamp,
                "context": metric.context
            })

        return result

    def get_health_score_history(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> list[dict]:
        """
        Query health score history with trends (Story 6.5, AC 6.5.3).

        Args:
            hours: Time window in hours (default: 24)
            limit: Maximum results to return (default: 100)

        Returns:
            List of health score dictionaries ordered by timestamp DESC (newest first):
            [
                {
                    "score": float (0-100),
                    "status": str,
                    "timestamp": ISO timestamp,
                    "component_scores": dict,
                    "context": dict
                },
                ...
            ]
        """
        # Calculate start time
        start_time = (datetime.now() - timedelta(hours=hours)).isoformat()

        # Query health scores from database
        with self.learning_db as db:
            health_scores = db.query_health_scores(
                start_time=start_time,
                limit=limit
            )

        # Convert to dictionaries
        import json
        result = []
        for score_record in health_scores:
            # Parse JSON fields if they're strings
            component_scores = score_record.get('component_scores')
            if isinstance(component_scores, str):
                try:
                    component_scores = json.loads(component_scores) if component_scores else {}
                except json.JSONDecodeError:
                    component_scores = {}

            context = score_record.get('context')
            if isinstance(context, str):
                try:
                    context = json.loads(context) if context else None
                except json.JSONDecodeError:
                    context = None

            result.append({
                "score": score_record['score'],
                "status": score_record['status'],
                "timestamp": score_record['timestamp'],
                "component_scores": component_scores,
                "context": context
            })

        return result

    def get_metrics_summary(self, hours: int = 24) -> dict:
        """
        Calculate summary statistics for all metrics (Story 6.5, AC 6.5.4).

        Args:
            hours: Time window in hours (default: 24)

        Returns:
            Dictionary with comprehensive metrics summary:
            {
                "time_window_hours": int,
                "metrics": {
                    "task_success_rate": {
                        "current": float,
                        "average": float,
                        "min": float,
                        "max": float,
                        "trend": "improving" | "stable" | "degrading",
                        "data_points": int
                    },
                    ... (other metrics)
                },
                "health_score_average": float,
                "active_alerts_count": int
            }
        """
        # Query all metrics for time window
        start_time = (datetime.now() - timedelta(hours=hours)).isoformat()

        with self.learning_db as db:
            all_metrics = db.query_metrics(
                metric_type=None,  # All metrics
                start_time=start_time,
                end_time=None,
                limit=10000  # Large limit to get all data
            )

        # Group metrics by type
        from collections import defaultdict
        metrics_by_type = defaultdict(list)

        for metric in all_metrics:
            metric_type = metric.metric_type.value
            metrics_by_type[metric_type].append({
                'value': metric.value,
                'timestamp': metric.timestamp
            })

        # Calculate statistics for each metric
        metrics_summary = {}

        for metric_type, values in metrics_by_type.items():
            if not values:
                continue

            # Sort by timestamp to calculate trend
            sorted_values = sorted(values, key=lambda x: x['timestamp'])
            value_list = [v['value'] for v in sorted_values]

            # Calculate statistics
            current = value_list[-1] if value_list else 0.0
            average = sum(value_list) / len(value_list) if value_list else 0.0
            min_val = min(value_list) if value_list else 0.0
            max_val = max(value_list) if value_list else 0.0

            # Calculate trend (compare first half vs second half)
            trend = "stable"
            if len(value_list) >= 4:  # Need at least 4 data points for meaningful trend
                midpoint = len(value_list) // 2
                first_half = value_list[:midpoint]
                second_half = value_list[midpoint:]

                first_avg = sum(first_half) / len(first_half)
                second_avg = sum(second_half) / len(second_half)

                # 5% threshold for trend detection
                threshold = 0.05
                if second_avg > first_avg * (1 + threshold):
                    trend = "improving"
                elif second_avg < first_avg * (1 - threshold):
                    trend = "degrading"

            metrics_summary[metric_type] = {
                "current": current,
                "average": average,
                "min": min_val,
                "max": max_val,
                "trend": trend,
                "data_points": len(value_list)
            }

        # Calculate average health score
        health_scores = self.get_health_score_history(hours=hours, limit=1000)
        health_score_average = 0.0
        if health_scores:
            health_score_average = sum(s['score'] for s in health_scores) / len(health_scores)

        # Get active alerts count
        active_alerts = self.get_active_alerts()
        active_alerts_count = len(active_alerts)

        return {
            "time_window_hours": hours,
            "metrics": metrics_summary,
            "health_score_average": health_score_average,
            "active_alerts_count": active_alerts_count
        }

    def get_alerts_summary(self, hours: int = 24) -> dict:
        """
        Summarize alert statistics for dashboard (Story 6.5, AC 6.5.5).

        Args:
            hours: Time window in hours (default: 24)

        Returns:
            Dictionary with alert statistics:
            {
                "time_window_hours": int,
                "total_alerts": int,
                "active_alerts": int,
                "acknowledged_alerts": int,
                "by_severity": {"critical": int, "warning": int},
                "by_metric": {metric_name: count, ...},
                "recent_alerts": [list of 5 most recent alerts]
            }
        """
        # Query all alerts for time window
        start_time = (datetime.now() - timedelta(hours=hours)).isoformat()

        with self.learning_db as db:
            all_alerts = db.query_alerts(
                start_time=start_time,
                end_time=None,
                acknowledged=None,  # Get both acknowledged and unacknowledged
                severity=None,  # Get all severities
                limit=10000
            )

        # Calculate counts
        total_alerts = len(all_alerts)
        active_alerts = len([a for a in all_alerts if not a.get('acknowledged', False)])
        acknowledged_alerts = len([a for a in all_alerts if a.get('acknowledged', False)])

        # Group by severity
        by_severity = {"critical": 0, "warning": 0}
        for alert in all_alerts:
            severity = alert.get('severity', 'warning')
            by_severity[severity] = by_severity.get(severity, 0) + 1

        # Group by metric
        by_metric = {}
        for alert in all_alerts:
            metric_name = alert.get('metric_name', 'unknown')
            by_metric[metric_name] = by_metric.get(metric_name, 0) + 1

        # Get 5 most recent alerts (already ordered by timestamp DESC from query)
        recent_alerts = all_alerts[:5]

        return {
            "time_window_hours": hours,
            "total_alerts": total_alerts,
            "active_alerts": active_alerts,
            "acknowledged_alerts": acknowledged_alerts,
            "by_severity": by_severity,
            "by_metric": by_metric,
            "recent_alerts": recent_alerts
        }
