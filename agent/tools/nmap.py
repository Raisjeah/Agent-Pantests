from langchain_core.tools import tool
from utils.runner import run_command
import xml.etree.ElementTree as ET
import shutil
import socket
from utils.parser import extract_host

@tool
def nmap_tool(target: str, ports: str = "1-1000") -> dict:
    """Scan target dengan nmap -sV, kembalikan informasi service."""
    if not shutil.which("nmap"):
        return {"error": "nmap tidak ditemukan di sistem."}

    # Parsing target menggunakan utility terpusat
    clean_target = extract_host(target)

    # DNS Lookup untuk memastikan target valid
    try:
        target_ip = socket.gethostbyname(clean_target)
    except Exception as e:
        return {"error": f"Gagal resolusi DNS untuk {clean_target}: {e}"}

    # Add -Pn to skip host discovery (useful for targets blocking ICMP)
    cmd = ["nmap", "-sV", "-Pn", "-p", ports, "-oX", "-", target_ip]
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
                state_elem = port.find('state')
                state = state_elem.get('state') if state_elem is not None else 'unknown'

                # Hanya ambil port yang terbuka agar LLM tidak bingung dengan filtered/closed ports
                if state != 'open':
                    continue

                svc = port.find('service')
                services.append({
                    "address": address,
                    "port": port.get('portid'),
                    "protocol": port.get('protocol'),
                    "state": state,
                    "name": svc.get('name') if svc is not None else '',
                    "product": svc.get('product', '') if svc is not None else '',
                    "version": svc.get('version', '') if svc is not None else ''
                })
        return {"services": services, "raw_stdout": stdout}
    except Exception as e:
        return {"error": f"Gagal parsing XML nmap: {e}", "raw_stdout": stdout}
