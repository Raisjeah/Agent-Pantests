from langchain_core.tools import tool
from utils.runner import run_command
from datetime import datetime
import json
import shutil

@tool
def trivy_tool(target: str) -> dict:
    """Jalankan trivy pada host/direktori filesystem."""
    timestamp = datetime.now().isoformat()
    result = {
        "tool": "trivy",
        "target": target,
        "status": "failed",
        "timestamp": timestamp,
        "raw_output": "",
        "parsed_output": {},
        "errors": []
    }

    if not shutil.which("trivy"):
        result["errors"].append("trivy tidak ditemukan di sistem.")
        return result

    cmd = ["trivy", "fs", "--scanners", "vuln,misconfig", "--format", "json", target]
    stdout, stderr = run_command(cmd, timeout=300)
    result["raw_output"] = stdout

    try:
        parsed = json.loads(stdout)
        result["parsed_output"] = parsed
        result["status"] = "success" if parsed else "empty"
    except Exception as e:
        result["errors"].append(f"Gagal parsing JSON trivy: {e}")
        if stderr:
            result["errors"].append(stderr)

    return result
