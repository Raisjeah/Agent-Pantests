from langchain_core.tools import tool
from utils.runner import run_command
import json
import shutil
import os
from pathlib import Path
from datetime import datetime
from utils.parser import extract_host

@tool
def nuclei_tool(target: str, template: str = "services") -> dict:
    """
    Jalankan nuclei scanner dengan template tertentu.
    Template bisa berupa nama default nuclei (misal: 'services')
    atau path ke template custom di agent/tools/templates/.
    """
    timestamp = datetime.now().isoformat()
    result = {
        "tool": "nuclei",
        "target": target,
        "status": "failed",
        "timestamp": timestamp,
        "raw_output": "",
        "parsed_output": {"nuclei_results": [], "template_used": template},
        "errors": []
    }

    if not shutil.which("nuclei"):
        result["errors"].append("nuclei tidak ditemukan di sistem.")
        return result

    # Gunakan host saja untuk template 'services' agar scanning lebih akurat
    clean_target = target
    if template == "services":
        clean_target = extract_host(target)

    # Cek apakah template adalah file custom
    template_path = template
    custom_dir = Path(__file__).parent / "templates"
    if not os.path.exists(template):
        potential_custom = custom_dir / f"{template}.yaml"
        if potential_custom.exists():
            template_path = str(potential_custom)
        elif (custom_dir / template).exists():
             template_path = str(custom_dir / template)

    result["parsed_output"]["template_used"] = template_path

    cmd = ["nuclei", "-target", clean_target, "-t", template_path, "-jsonl", "-silent"]
    stdout, stderr = run_command(cmd, timeout=300)
    result["raw_output"] = stdout

    if "no templates" in stderr.lower() or "could not load templates" in stderr.lower():
        result["errors"].append(f"Nuclei: Template '{template}' tidak ditemukan.")
        result["errors"].append(stderr)
        return result

    findings = []
    if stdout:
        for line in stdout.strip().split('\n'):
            if line.strip():
                try:
                    findings.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    result["parsed_output"]["nuclei_results"] = findings
    result["status"] = "success" if findings else "empty"
    if stderr:
        result["errors"].append(stderr)

    return result
