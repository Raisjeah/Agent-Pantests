from langchain_core.tools import tool
from utils.runner import run_command
import xml.etree.ElementTree as ET

@tool
def nmap_tool(target: str, ports: str = "1-1000") -> dict:
    """Scan target dengan nmap -sV, kembalikan informasi service."""
    cmd = ["nmap", "-sV", "-p", ports, "-oX", "-", target]
    stdout, stderr = run_command(cmd, sudo=True)
    if stderr and not stdout:
        return {"error": stderr}
    try:
        root = ET.fromstring(stdout)
        services = []
        for host in root.findall('.//host'):
            for port in host.findall('.//ports/port'):
                svc = port.find('service')
                services.append({
                    "port": port.get('portid'),
                    "protocol": port.get('protocol'),
                    "name": svc.get('name') if svc is not None else '',
                    "product": svc.get('product', ''),
                    "version": svc.get('version', '')
                })
        return {"services": services}
    except ET.ParseError:
        return {"raw": stdout}
