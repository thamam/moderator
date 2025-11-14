"""Abstract base class for all dashboard panels."""

from textual.reactive import reactive
from textual.widget import Widget


class BasePanel(Widget):
    """Abstract base class for all dashboard panels.

    All dashboard panels must inherit from this class and implement
    the abstract methods refresh_data() and render_content().

    Note: We use refresh_data() instead of refresh() to avoid conflicting
    with Textual's Widget.refresh() method.

    Attributes:
        is_expanded: Reactive property tracking panel expansion state
        error_message: Reactive property for displaying error messages
    """

    # Reactive properties (auto-trigger UI updates when value changes)
    is_expanded = reactive(False)
    error_message = reactive(None)

    async def refresh_data(self) -> None:
        """Fetch fresh data from MonitorAgent.

        Subclasses should override this method to query the MonitorAgent
        APIs and update the panel's data.

        This method is called automatically by the dashboard's auto-refresh
        timer (default: every 3 seconds).
        """
        pass  # Default implementation does nothing

    def render_content(self) -> str:
        """Render panel content as Rich markup.

        Subclasses should override this method to return the panel's
        content as a string with Rich markup formatting.

        Returns:
            str: Panel content with Rich markup (e.g., "[green]Healthy[/]")
        """
        return "[dim]No content[/]"  # Default implementation

    def render(self) -> str:
        """Main render method with error handling.

        This method is called by Textual to render the widget.
        It handles errors gracefully by displaying error messages
        instead of crashing the panel.

        Returns:
            str: Rendered content (either render_content() or error message)
        """
        if self.error_message:
            return f"[red]Error: {self.error_message}[/]"
        return self.render_content()
