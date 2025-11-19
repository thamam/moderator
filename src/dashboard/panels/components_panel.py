"""Components Panel for Terminal UI Dashboard.

Displays per-component health status for system components.
"""

from typing import Dict
from textual.reactive import reactive
from src.dashboard.panels.base_panel import BasePanel


class ComponentsPanel(BasePanel):
    """Component Health panel showing per-component status.

    Displays health indicators for 5 core system components:
    - Task Executor (parallel/sequential)
    - Backend Router
    - Learning System (LearningDB)
    - QA Manager
    - Monitor Agent

    Status indicators:
    - 🟢 Operational: Component registered and functional
    - 🟡 Degraded: Component registered but has issues
    - 🔴 Error: Component not registered or failed

    Attributes:
        component_statuses: Dictionary mapping component names to status strings
    """

    component_statuses: Dict[str, str] = reactive({})

    def __init__(self, **kwargs):
        """Initialize ComponentsPanel.

        Args:
            **kwargs: Additional arguments passed to BasePanel
        """
        super().__init__(**kwargs)

    async def refresh_data(self) -> None:
        """Check component health via Orchestrator.

        Checks health of all 5 system components and updates status.
        """
        try:
            # TODO: Integrate with Orchestrator when available
            # For now, simulate component checks
            self.component_statuses = {
                "Task Executor": self._check_executor_health(),
                "Backend Router": self._check_router_health(),
                "Learning System": self._check_learning_health(),
                "QA Manager": self._check_qa_health(),
                "Monitor Agent": self._check_monitor_health(),
            }
            self.error_message = None
        except Exception as e:
            self.error_message = f"Error checking components: {str(e)}"

    def render_content(self) -> str:
        """Render components panel content.

        Returns:
            Formatted string with component status table
        """
        if self.error_message:
            return f"[red]{self.error_message}[/]"

        if not self.component_statuses:
            return "[dim]No component data available[/]"

        output = []
        output.append("[bold]Component Health Status[/]")
        output.append("")

        # Table header
        output.append(f"{'Component':<20} │ {'Status':<8} │ {'Details':<40}")
        output.append("─" * 72)

        # Table rows
        for component, status in self.component_statuses.items():
            status_icon, status_text = self._get_status_display(status)
            details = self._get_component_details(component, status)
            output.append(f"{component:<20} │ {status_icon:<8} │ {details:<40}")

        return "\n".join(output)

    def _check_executor_health(self) -> str:
        """Check if Task Executor is operational.

        Returns:
            Status string: operational, degraded, or error
        """
        # TODO: Integrate with actual Orchestrator
        # For now, return placeholder status
        return "operational"  # Assume operational until integrated

    def _check_router_health(self) -> str:
        """Check if Backend Router is operational.

        Returns:
            Status string: operational, degraded, or error
        """
        # TODO: Integrate with actual Backend Router
        return "operational"  # Assume operational until integrated

    def _check_learning_health(self) -> str:
        """Check if Learning System is operational.

        Returns:
            Status string: operational, degraded, or error
        """
        # TODO: Integrate with actual LearningDB
        return "operational"  # Assume operational until integrated

    def _check_qa_health(self) -> str:
        """Check if QA Manager is operational.

        Returns:
            Status string: operational, degraded, or error
        """
        # TODO: Check if QA tools are installed
        return "degraded"  # Example: Some QA tools might be missing

    def _check_monitor_health(self) -> str:
        """Check if Monitor Agent is operational.

        Returns:
            Status string: operational, degraded, or error
        """
        # TODO: Integrate with actual MonitorAgent
        return "operational"  # Assume operational until integrated

    def _get_status_display(self, status: str) -> tuple[str, str]:
        """Get formatted status icon and text.

        Args:
            status: Component status (operational, degraded, error)

        Returns:
            Tuple of (status_icon, status_text)
        """
        status_lower = status.lower()

        if status_lower == "operational":
            return ("[green]🟢[/]", "OK")
        elif status_lower == "degraded":
            return ("[yellow]🟡[/]", "WARN")
        elif status_lower == "error":
            return ("[red]🔴[/]", "ERROR")
        else:
            return ("[dim]⚪[/]", "UNK")

    def _get_component_details(self, component: str, status: str) -> str:
        """Get details text for a component.

        Args:
            component: Component name
            status: Component status

        Returns:
            Details string describing component state
        """
        # TODO: Get actual details from components
        # For now, return placeholder details
        if status == "operational":
            if component == "Task Executor":
                return "Active (parallel mode)"
            elif component == "Backend Router":
                return "Active (3 backends configured)"
            elif component == "Learning System":
                return "Database connected"
            elif component == "QA Manager":
                return "Ready (some tools optional)"
            elif component == "Monitor Agent":
                return "Collecting metrics"
            else:
                return "Active"
        elif status == "degraded":
            if component == "QA Manager":
                return "Bandit not installed (optional)"
            else:
                return "Partial functionality"
        else:  # error
            return "Not configured"
