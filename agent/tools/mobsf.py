from langchain_core.tools import tool
from utils.runner import run_command

@tool
def mobsf_tool(file_path: str) -> dict:
    """Analisis APK/IPA dengan MobSF CLI."""
    cmd = ["mobsf", "scan", file_path]
    stdout, stderr = run_command(cmd, timeout=300)
    return {"tool": "mobsf", "output": stdout, "error": stderr}
