from langchain_core.tools import tool
from utils.runner import run_command
from datetime import datetime
import json
import shutil

@tool
def semgrep_tool(target: str) -> dict:
    """Jalankan semgrep pada direktori kode."""
    timestamp = datetime.now().isoformat()
    result = {
        "tool": "semgrep",
        "target": target,
        "status": "failed",
        "timestamp": timestamp,
        "raw_output": "",
        "parsed_output": {},
        "errors": []
    }

    if target.startswith("http://") or target.startswith("https://"):
        result["errors"].append("Semgrep hanya mendukung file lokal, bukan URL website.")
        return result

    if not shutil.which("semgrep"):
        result["errors"].append("semgrep tidak ditemukan di sistem.")
        return result

    cmd = ["semgrep", "--config=auto", "--quiet", "--json", target]
    stdout, stderr = run_command(cmd, timeout=300)
    result["raw_output"] = stdout

    try:
        parsed = json.loads(stdout)
        result["parsed_output"] = parsed
        result["status"] = "success" if parsed else "empty"
    except Exception as e:
        result["errors"].append(f"Gagal parsing JSON semgrep: {e}")
        if stderr:
            result["errors"].append(stderr)

    return result
