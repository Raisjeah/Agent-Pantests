#!/usr/bin/env python3
import typer
import json
import uuid
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
        "findings": [],
        "final_report": None,
        "passive_recon": None,
        "active_recon": None,
        "scanning": None,
        "enumeration": None,
        "vuln_assess": None,
        "weaponization": None,
        "delivery": None,
        "exploitation": None,
        "access": None
    }
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    current_state = initial_state

    while True:
        try:
            # Run the graph until it finishes or hits an interrupt
            events = graph.stream(current_state, config, stream_mode="values")
            for event in events:
                current_state = event

            # Check if we are at an interrupt point
            snapshot = graph.get_state(config)
            if snapshot.next:
                next_node = snapshot.next[0]
                console.print(f"\n[bold yellow]INTERRUPT: Agent akan memasuki fase {next_node}[/bold yellow]")

                # Show some context
                if next_node == "weaponization":
                    findings = current_state.get("findings", [])
                    console.print(f"Ditemukan {len(findings)} temuan potensial untuk di-weaponize.")
                elif next_node == "exploitation":
                    strategies = current_state.get("delivery", {}).get("strategies", [])
                    console.print(f"Ditemukan {len(strategies)} strategi delivery untuk dieksploitasi.")

                confirm = typer.confirm("Lanjutkan ke fase berikutnya?")
                if not confirm:
                    console.print("[red]Pemindaian dihentikan oleh pengguna.[/red]")
                    break

                # Resume execution
                current_state = None # Set to None to resume from checkpoint
            else:
                # Execution finished
                break

        except Exception as e:
            console.print(f"[red]Error saat menjalankan graph: {e}[/red]")
            raise typer.Exit(1)

    # Final report processing
    # Since we removed the validator node in the linear graph, let's just show the access plan or summary
    access_plan = current_state.get("access")
    if access_plan:
        console.print("\n[bold green]Pentest Selesai. Hasil Akses Akhir:[/bold green]")
        console.print_json(json.dumps(access_plan, indent=2))
    else:
        console.print("[yellow]Pentest selesai tanpa hasil akses akhir.[/yellow]")

    if output:
        with open(output, "w") as f:
            json.dump(current_state, f, indent=2)
        console.print(f"Semua data state disimpan ke: {output}")

if __name__ == "__main__":
    app()
