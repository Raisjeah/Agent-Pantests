from langchain_core.tools import tool
from utils.runner import run_command
import json

@tool
def nuclei_tool(target: str, template: str = "services") -> dict:
    """Jalankan nuclei scanner dengan template tertentu."""
    cmd = ["nuclei", "-t", template, "-jsonl", "-silent", "-target", target]
    stdout, stderr = run_command(cmd)
    results = []
    for line in stdout.strip().split('\n'):
        if line:
            try:
                results.append(json.loads(line))
            except:
                pass
    return {"nuclei_results": results, "error": stderr if stderr else None}
