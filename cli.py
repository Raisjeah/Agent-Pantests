#!/usr/bin/env python3
import typer
import json
import uuid
import pyfiglet
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn
from agent.graph import create_graph

app = typer.Typer(help="🤖 AI Pentest Agent (Deterministic Workflow)")
console = Console()

def print_banner():
    # Blood red color for the banner
    banner = pyfiglet.figlet_format("ACC", font="slant")
    console.print(f"[bold red]{banner}[/bold red]")
    console.print(Panel(
        Text("AI AGENT CHAINS CAPILOT", style="bold white", justify="center"),
        style="red",
        subtitle="Deterministic Security Workflow Engine",
        subtitle_align="right"
    ))
    console.print("\n")

def display_findings(findings):
    if not findings:
        return

    table = Table(title="🔍 Findings", title_style="bold yellow", border_style="red")
    table.add_column("Type", style="cyan")
    table.add_column("Value", style="white")
    table.add_column("Evidence", style="dim white")

    for f in findings:
        table.add_row(
            str(f.get("type", "N/A")),
            str(f.get("value", "N/A")),
            str(f.get("evidence", "N/A"))[:50] + "..." if len(str(f.get("evidence", ""))) > 50 else str(f.get("evidence", "N/A"))
        )

    console.print(table)

@app.command()
def dashboard(host: str = "0.0.0.0", port: int = 8000):
    """Jalankan Web Dashboard interaktif."""
    import uvicorn
    from web.server import app as web_app
    print_banner()
    console.print(Panel(
        f"Dashboard berjalan di: [bold cyan]http://{host}:{port}[/bold cyan]",
        title="🚀 WEB SERVER",
        border_style="green"
    ))
    uvicorn.run(web_app, host=host, port=port)

@app.command()
def scan(
    target: str = typer.Argument(..., help="Target IP/domain/URL/path"),
    scope: str = typer.Option("all", help="Scope: web, os, mobile, code (comma-separated)"),
    deep: bool = typer.Option(False, "--deep", help="Deep scan mode"),
    model: str = typer.Option("google", help="AI Model Provider (google, anthropic)"),
    output: str = typer.Option(None, help="Simpan laporan ke file JSON")
):
    """Jalankan pemindaian keamanan otomatis dengan tampilan modern."""
    print_banner()

    console.print(f"[bold white]Target:[/bold white] [red]{target}[/red]")
    console.print(f"[bold white]Scope :[/bold white] [dim]{scope}[/dim]")
    console.print(f"[bold white]Model :[/bold white] [dim]{model}[/dim]")
    console.print(f"[bold white]Mode  :[/bold white] [dim]{'Deep' if deep else 'Standard'}[/dim]")
    console.print("-" * 40)

    graph = create_graph()
    initial_state = {
        "target": target,
        "scope": scope,
        "deep": deep,
        "model_provider": model,
        "findings": [],
        "evidence": [],
        "current_state": "START",
        "status": "success",
        "confidence": 0.0,
        "recon": None,
        "scan": None,
        "enum": None,
        "vuln_analysis": None,
        "exploitation": None,
        "report": None
    }

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    console.print(f"[dim]Thread ID: {thread_id}[/dim]\n")

    current_state = initial_state

    try:
        with Progress(
            SpinnerColumn(style="bold red"),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Initializing engine...", total=None)

            while True:
                # Run the graph
                events = graph.stream(current_state, config, stream_mode="values")
                for event in events:
                    current_state = event
                    phase = event.get("current_state", "Processing")
                    status = event.get("status", "working")

                    progress.update(task, description=f"Phase: [bold red]{phase}[/bold red] (Status: {status})")

                    # Update status message below progress
                    if phase != "START":
                        console.print(f"[red]»[/red] Completed [bold]{phase}[/bold] with status: [yellow]{status}[/yellow]")

                # Check if we are at an interrupt point
                snapshot = graph.get_state(config)
                if snapshot.next:
                    progress.stop()
                    next_node = snapshot.next[0]

                    console.print(Panel(
                        f"Agent requires confirmation to enter phase: [bold red]{next_node}[/bold red]",
                        title="⚠️ INTERRUPT",
                        border_style="yellow"
                    ))

                    if next_node == "exploitation":
                        display_findings(current_state.get("findings", []))

                    confirm = typer.confirm("🚀 Lanjutkan ke fase berikutnya?", default=True)
                    if not confirm:
                        console.print("[bold red]Pemindaian dihentikan oleh pengguna.[/bold red]")
                        break

                    progress.start()
                    current_state = None # Resume from checkpoint
                else:
                    break

    except Exception as e:
        console.print(f"\n[bold red]FATAL ERROR:[/bold red] {e}")
        raise typer.Exit(1)

    # Final report processing
    report = current_state.get("report", {})
    if report:
        console.print("\n" + "="*50)
        console.print(Panel(
            "[bold green]PENTEST Selesai. Hasil akhir telah dirangkum.[/bold green]",
            title="🏁 REPORT READY",
            border_style="green"
        ))

        display_findings(current_state.get("findings", []))

        if typer.confirm("Lihat detail JSON report?"):
            console.print_json(json.dumps(report, indent=2))
    else:
        console.print("\n[yellow]Pentest selesai tanpa laporan akhir.[/yellow]")

    if output:
        with open(output, "w") as f:
            json.dump(current_state, f, indent=2)
        console.print(f"\n[dim]State lengkap disimpan ke: {output}[/dim]")

if __name__ == "__main__":
    app()
