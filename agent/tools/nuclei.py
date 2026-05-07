from langchain_core.tools import tool
from utils.runner import run_command
import json
import shutil

@tool
def nuclei_tool(target: str, template: str = "services") -> dict:
    """Jalankan nuclei scanner dengan template tertentu."""
    if not shutil.which("nuclei"):
        return {"error": "nuclei tidak ditemukan di sistem."}

    cmd = ["nuclei", "-target", target, "-t", template, "-jsonl", "-silent"]
    stdout, stderr = run_command(cmd, timeout=300)

    results = []
    if stdout:
        for line in stdout.strip().split('\n'):
            if line.strip():
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    return {
        "nuclei_results": results,
        "count": len(results),
        "error": stderr if stderr and not results else None
    }
