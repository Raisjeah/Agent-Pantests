from langchain_core.tools import tool
from utils.runner import run_command
import json
import shutil
import os
from pathlib import Path
from utils.parser import extract_host

@tool
def nuclei_tool(target: str, template: str = "services") -> dict:
    """
    Jalankan nuclei scanner dengan template tertentu.
    Template bisa berupa nama default nuclei (misal: 'services')
    atau path ke template custom di agent/tools/templates/.
    """
    if not shutil.which("nuclei"):
        return {"error": "nuclei tidak ditemukan di sistem."}

    # Gunakan host saja untuk template 'services' agar scanning lebih akurat
    if template == "services":
        target = extract_host(target)

    # Cek apakah template adalah file custom
    template_path = template
    custom_dir = Path(__file__).parent / "templates"
    if not os.path.exists(template):
        potential_custom = custom_dir / f"{template}.yaml"
        if potential_custom.exists():
            template_path = str(potential_custom)
        elif (custom_dir / template).exists():
             template_path = str(custom_dir / template)

    cmd = ["nuclei", "-target", target, "-t", template_path, "-jsonl", "-silent"]
    stdout, stderr = run_command(cmd, timeout=300)

    if "no templates" in stderr.lower() or "could not load templates" in stderr.lower():
        return {"error": f"Nuclei: Template '{template}' tidak ditemukan.", "raw_stderr": stderr}

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
        "template_used": template_path,
        "error": stderr if stderr and not results else None
    }
