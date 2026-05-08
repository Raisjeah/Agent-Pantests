from langchain_core.tools import tool
from utils.runner import run_command
import xml.etree.ElementTree as ET
import shutil
import socket
from urllib.parse import urlparse

@tool
def nmap_tool(target: str, ports: str = "1-1000") -> dict:
    """Scan target dengan nmap -sV, kembalikan informasi service."""
    if not shutil.which("nmap"):
        return {"error": "nmap tidak ditemukan di sistem."}

    # Parsing target jika berupa URL
    clean_target = target
    if target.startswith("http://") or target.startswith("https://"):
        try:
            parsed = urlparse(target)
            clean_target = parsed.hostname or target
        except Exception:
            clean_target = target

    # DNS Lookup untuk memastikan target valid
    try:
        target_ip = socket.gethostbyname(clean_target)
    except Exception as e:
        return {"error": f"Gagal resolusi DNS untuk {clean_target}: {e}"}

    cmd = ["nmap", "-sV", "-p", ports, "-oX", "-", target_ip]
    stdout, stderr = run_command(cmd)

    if not stdout and stderr:
        return {"error": stderr}

    try:
        root = ET.fromstring(stdout)
        services = []
        for host in root.findall('.//host'):
            addr_elem = host.find('address')
            address = addr_elem.get('addr') if addr_elem is not None else target

            for port in host.findall('.//ports/port'):
                svc = port.find('service')
                services.append({
                    "address": address,
                    "port": port.get('portid'),
                    "protocol": port.get('protocol'),
                    "state": port.find('state').get('state') if port.find('state') is not None else 'unknown',
                    "name": svc.get('name') if svc is not None else '',
                    "product": svc.get('product', '') if svc is not None else '',
                    "version": svc.get('version', '') if svc is not None else ''
                })
        return {"services": services, "raw_stdout": stdout[:500]}
    except Exception as e:
        return {"error": f"Gagal parsing XML nmap: {e}", "raw_stdout": stdout[:1000]}
