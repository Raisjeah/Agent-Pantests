from agent.models import ToolOutput, PortInfo, Service, Vulnerability, SecurityFinding, NormalizedState
from typing import List, Dict, Any

def normalize_nmap(tool_out: ToolOutput) -> NormalizedState:
    state = NormalizedState(target=tool_out.target)
    services_list = tool_out.parsed_output.get("services", [])
    for s in services_list:
        port_info = PortInfo(
            port=s.get("port", ""),
            protocol=s.get("protocol", ""),
            state=s.get("state", ""),
            service=s.get("name", ""),
            product=s.get("product", ""),
            version=s.get("version", "")
        )
        state.ports.append(port_info)
        state.services.append(Service(
            name=s.get("name", ""),
            version=s.get("version", ""),
            port=s.get("port", ""),
            protocol=s.get("protocol", "")
        ))
        state.findings.append(SecurityFinding(
            type="port",
            value=f"{s.get('port')}/{s.get('protocol')}",
            evidence=f"Nmap found {s.get('name')} {s.get('product')} {s.get('version')}"
        ))
    return state

def normalize_nuclei(tool_out: ToolOutput) -> NormalizedState:
    state = NormalizedState(target=tool_out.target)
    results = tool_out.parsed_output.get("nuclei_results", [])
    for r in results:
        info = r.get("info", {})
        vuln = Vulnerability(
            id=r.get("template-id"),
            name=info.get("name", "Unknown Nuclei Finding"),
            description=info.get("description"),
            severity=info.get("severity", "info"),
            tool="nuclei",
            evidence_id=f"nuclei_{r.get('template-id')}_{r.get('timestamp')}",
            metadata=r
        )
        state.vulnerabilities.append(vuln)
        state.findings.append(SecurityFinding(
            type="vulnerability",
            value=info.get("name", "Unknown"),
            evidence=f"Nuclei template {r.get('template-id')} matched",
            severity=info.get("severity", "info")
        ))
    return state

def normalize_sqlmap(tool_out: ToolOutput) -> NormalizedState:
    state = NormalizedState(target=tool_out.target)
    findings = tool_out.parsed_output.get("findings", [])
    for f in findings:
        vuln = Vulnerability(
            name=f.get("finding", "SQL Injection"),
            severity=f.get("severity", "high"),
            tool="sqlmap",
            evidence_id=f"sqlmap_{tool_out.timestamp}",
            metadata={"raw_output": tool_out.raw_output}
        )
        state.vulnerabilities.append(vuln)
        state.findings.append(SecurityFinding(
            type="vulnerability",
            value="SQL Injection",
            evidence="SQLMap detected potential vulnerability",
            severity=f.get("severity", "high")
        ))
    return state

def normalize_trivy(tool_out: ToolOutput) -> NormalizedState:
    state = NormalizedState(target=tool_out.target)
    parsed = tool_out.parsed_output
    # Trivy JSON usually has 'Results'
    results = parsed.get("Results", [])
    for res in results:
        target_name = res.get("Target", "unknown")
        vulnerabilities = res.get("Vulnerabilities", [])
        for v in vulnerabilities:
            vuln = Vulnerability(
                id=v.get("VulnerabilityID"),
                name=v.get("Title", v.get("VulnerabilityID", "Trivy Finding")),
                description=v.get("Description"),
                severity=v.get("Severity", "info").lower(),
                tool="trivy",
                evidence_id=f"trivy_{v.get('VulnerabilityID')}_{tool_out.timestamp}",
                metadata=v
            )
            state.vulnerabilities.append(vuln)
            state.findings.append(SecurityFinding(
                type="vulnerability",
                value=v.get("VulnerabilityID", "Vulnerability"),
                evidence=f"Trivy found {v.get('VulnerabilityID')} in {target_name}",
                severity=v.get("Severity", "info").lower()
            ))
    return state

def normalize_semgrep(tool_out: ToolOutput) -> NormalizedState:
    state = NormalizedState(target=tool_out.target)
    results = tool_out.parsed_output.get("results", [])
    for r in results:
        extra = r.get("extra", {})
        vuln = Vulnerability(
            id=r.get("check_id"),
            name=extra.get("message", "Semgrep Finding"),
            severity=extra.get("severity", "info").lower(),
            tool="semgrep",
            evidence_id=f"semgrep_{r.get('check_id')}_{tool_out.timestamp}",
            metadata=r
        )
        state.vulnerabilities.append(vuln)
        state.findings.append(SecurityFinding(
            type="vulnerability",
            value=r.get("check_id"),
            evidence=f"Semgrep matched rule {r.get('check_id')} in {r.get('path')}",
            severity=extra.get("severity", "info").lower()
        ))
    return state

def normalize_tool_output(tool_out_dict: Dict[str, Any]) -> NormalizedState:
    try:
        # Check if it's already an error dict from try/except block in node
        if "error" in tool_out_dict and "tool" in tool_out_dict and "timestamp" not in tool_out_dict:
             return NormalizedState(target=tool_out_dict.get("target", "unknown"), errors=[tool_out_dict["error"]])

        tool_out = ToolOutput(**tool_out_dict)
    except Exception as e:
        return NormalizedState(target=tool_out_dict.get("target", "unknown"), errors=[f"Invalid ToolOutput schema: {e}"])

    if tool_out.tool == "nmap":
        return normalize_nmap(tool_out)
    if tool_out.tool == "nuclei":
        return normalize_nuclei(tool_out)
    if tool_out.tool == "sqlmap":
        return normalize_sqlmap(tool_out)
    if tool_out.tool == "trivy":
        return normalize_trivy(tool_out)
    if tool_out.tool == "semgrep":
        return normalize_semgrep(tool_out)

    state = NormalizedState(target=tool_out.target)
    if tool_out.errors:
        state.errors.extend(tool_out.errors)
    return state
