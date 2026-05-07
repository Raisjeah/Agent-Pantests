from langchain_core.tools import tool
from utils.runner import run_command
import json

@tool
def trivy_tool(target: str) -> dict:
    """Jalankan trivy pada host/direktori filesystem."""
    cmd = ["trivy", "fs", "--scanners", "vuln,misconfig", "--format", "json", target]
    stdout, stderr = run_command(cmd, timeout=300)
    try:
        return json.loads(stdout)
    except:
        return {"raw": stdout, "error": stderr}
