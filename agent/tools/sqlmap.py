from langchain_core.tools import tool
from utils.runner import run_command

@tool
def sqlmap_tool(url: str) -> dict:
    """Jalankan sqlmap (mode batch, low risk)."""
    cmd = [
        "sqlmap", "-u", url,
        "--batch", "--smart", "--level=1", "--risk=1",
        "--output-dir=/tmp/sqlmap", "--flush-session"
    ]
    stdout, stderr = run_command(cmd, timeout=600)
    finding = {}
    if "vulnerable" in stdout.lower():
        finding = {
            "finding": "Potential SQL injection found",
            "tool": "sqlmap",
            "severity": "high"
        }
    else:
        finding = {
            "finding": "No SQL injection detected",
            "tool": "sqlmap",
            "severity": "info"
        }
    return {**finding, "output": stdout, "error": stderr}
