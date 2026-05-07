import typer
from rich.console import Console

class SafetyChecker:
    def __init__(self, config: dict):
        self.hitl = config.get("human_in_the_loop", True)
        self.trusted = config.get("trusted_tools", [])
        self.console = Console()

    def approve_action(self, tool_name: str, command: str) -> bool:
        if tool_name in self.trusted:
            return True
        if self.hitl:
            self.console.print(f"[yellow]⚠️  Perintah: {command}[/yellow]")
            confirm = typer.prompt("Lanjutkan? (y/N)", default="n")
            return confirm.lower() == "y"
        return False
