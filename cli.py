#!/usr/bin/env python3
import typer
import json
from rich.console import Console
from agent.graph import create_graph

app = typer.Typer(help="🤖 AI Pentest Agent (LangChain + LangGraph)")
console = Console()

@app.command()
def scan(
    target: str = typer.Argument(..., help="Target IP/domain/URL/path"),
    scope: str = typer.Option("all", help="Scope: web, os, mobile, code (comma-separated)"),
    deep: bool = typer.Option(False, "--deep", help="Deep scan mode"),
    output: str = typer.Option(None, help="Simpan laporan ke file JSON")
):
    """Jalankan pemindaian keamanan otomatis."""
    console.print(f"[bold green]Memulai AI Pentest terhadap {target}[/bold green]")
    graph = create_graph()
    initial_state = {
        "target": target,
        "scope": scope,
        "deep": deep,
        "recon_data": None,
        "findings": [],
        "final_report": None
    }
    config = {"configurable": {"thread_id": "1"}}
    try:
        result = graph.invoke(initial_state, config)
    except Exception as e:
        console.print(f"[red]Error saat menjalankan graph: {e}[/red]")
        raise typer.Exit(1)

    report = result.get("final_report")
    if not report:
        console.print("[red]Tidak ada laporan yang dihasilkan.[/red]")
        raise typer.Exit(1)

    if output:
        with open(output, "w") as f:
            json.dump(report, f, indent=2)
        console.print(f"Laporan disimpan: {output}")
    else:
        console.print_json(json.dumps(report, indent=2))

    summary = report["summary"]
    console.print(f"\n[bold]Ringkasan:[/bold] High: {summary.get('high',0)}, "
                  f"Medium: {summary.get('medium',0)}, Low: {summary.get('low',0)}, "
                  f"Total: {summary.get('total',0)}")

if __name__ == "__main__":
    app()
