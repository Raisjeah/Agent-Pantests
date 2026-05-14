from langchain_core.tools import tool
from utils.runner import run_command
from datetime import datetime
import shutil

@tool
def sqlmap_tool(url: str) -> dict:
    """Jalankan sqlmap (mode batch, low risk)."""
    timestamp = datetime.now().isoformat()
    result = {
        "tool": "sqlmap",
        "target": url,
        "status": "failed",
        "timestamp": timestamp,
        "raw_output": "",
        "parsed_output": {"findings": []},
        "errors": []
    }

    if not shutil.which("sqlmap"):
        result["errors"].append("sqlmap tidak ditemukan di sistem.")
        return result

    cmd = [
        "sqlmap", "-u", url,
        "--batch", "--smart", "--level=1", "--risk=1",
        "--output-dir=/tmp/sqlmap", "--flush-session"
    ]
    stdout, stderr = run_command(cmd, timeout=600)
    result["raw_output"] = stdout

    if "vulnerable" in stdout.lower():
        result["parsed_output"]["findings"].append({
            "finding": "Potential SQL injection found",
            "severity": "high"
        })
        result["status"] = "success"
    else:
        result["status"] = "empty"

    if stderr:
        result["errors"].append(stderr)

    return result
