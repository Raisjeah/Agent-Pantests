from rich.console import Console
from rich.theme import Theme

def setup_console():
    theme = Theme({
        "info": "cyan",
        "warning": "yellow",
        "error": "red bold",
        "success": "green",
    })
    return Console(theme=theme)
