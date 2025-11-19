"""Help Screen for Terminal UI Dashboard.

Displays keyboard shortcuts in a modal overlay.
"""

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Static


class HelpScreen(ModalScreen):
    """Help screen showing keyboard shortcuts.

    Displays a modal overlay with all available keyboard shortcuts
    for the dashboard.

    Keyboard shortcuts:
    - Tab / Shift+Tab: Navigate between panels
    - Enter: Expand selected panel for details
    - Q: Quit dashboard
    - ?: Toggle this help screen
    - ESC: Close help screen
    """

    CSS = """
    HelpScreen {
        align: center middle;
    }

    HelpScreen > Container {
        width: 60;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 2;
    }

    #help-content {
        width: 100%;
        height: auto;
    }
    """

    BINDINGS = [
        ("escape", "dismiss", "Close"),
        ("?", "dismiss", "Close"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the help screen layout.

        Yields:
            Static widget containing help text
        """
        with Container():
            yield Static(
                """[bold cyan]Keyboard Shortcuts[/bold cyan]

[bold]Navigation:[/bold]
  [cyan]Tab[/]            Navigate to next panel
  [cyan]Shift+Tab[/]      Navigate to previous panel
  [cyan]Enter[/]          Expand selected panel

[bold]Actions:[/bold]
  [cyan]Q[/]              Quit dashboard
  [cyan]?[/]              Toggle this help screen
  [cyan]ESC[/]            Close help screen

[bold]Auto-Refresh:[/bold]
  Panels update every 3 seconds automatically

[dim]Press ? or ESC to close this help screen[/dim]
""",
                id="help-content",
            )

    def action_dismiss(self) -> None:
        """Close the help screen."""
        self.app.pop_screen()
