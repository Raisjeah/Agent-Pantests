from langchain_core.tools import tool
from utils.runner import run_command
import json

@tool
def semgrep_tool(target: str) -> dict:
    """Jalankan semgrep pada direktori kode."""
    cmd = ["semgrep", "--config=auto", "--quiet", "--json", target]
    stdout, stderr = run_command(cmd, timeout=300)
    try:
        return json.loads(stdout)
    except:
        return {"raw": stdout, "error": stderr}
