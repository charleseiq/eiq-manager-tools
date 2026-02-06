"""Shared utilities for Rich console and progress display."""

try:
    from rich.console import Console

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None  # type: ignore[assignment]


def get_console() -> Console | None:
    """
    Get Rich Console instance if available.

    Returns:
        Console instance or None if Rich not available
    """
    if RICH_AVAILABLE and Console is not None:
        return Console()
    return None


def print_rich(message: str, style: str = "cyan") -> None:
    """
    Print message using Rich if available, otherwise use regular print.

    Args:
        message: Message to print
        style: Rich style (default: "cyan")
    """
    console = get_console()
    if console:
        console.print(f"[{style}]{message}[/{style}]")
    else:
        print(message)
