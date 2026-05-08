from langchain_core.tools import tool
from utils.runner import run_command
import json
import shutil
from utils.parser import extract_host

@tool
def nuclei_tool(target: str, template: str = "services") -> dict:
    """Jalankan nuclei scanner dengan template tertentu."""
    if not shutil.which("nuclei"):
        return {"error": "nuclei tidak ditemukan di sistem."}

    # Gunakan host saja untuk template 'services' agar scanning lebih akurat
    if template == "services":
        target = extract_host(target)

    cmd = ["nuclei", "-target", target, "-t", template, "-jsonl", "-silent"]
    stdout, stderr = run_command(cmd, timeout=300)

    if "no templates" in stderr.lower():
        return {"error": "Nuclei: Template tidak ditemukan atau tidak tersedia.", "raw_stderr": stderr}

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
