# AUDIT_REPORT.md

## 1. Existing Architecture

The project is an AI-powered penetration testing CLI tool built on **LangGraph**, providing a deterministic 6-phase state machine:

1.  **RECON**: Basic host discovery and service identification (Nmap, Nuclei).
2.  **SCAN**: Detailed port scanning and network-level vulnerability scanning.
3.  **ENUM**: Service enumeration and CVE matching.
4.  **VULN_ANALYSIS**: Targeted vulnerability assessment (SQLMap, Trivy, Semgrep).
5.  **EXPLOITATION**: Execution of shell commands based on identified findings (with Human-in-the-Loop interrupt).
6.  **REPORT**: Final summarization and validation of findings.

### Components:
- **Entrypoint**: `cli.py` (Typer CLI).
- **Workflow Engine**: `agent/graph.py` (LangGraph).
- **State Management**: `agent/state.py` (`AgentState` TypedDict).
- **Agents**: `agent/agents/` (Node functions per phase).
- **Tools**: `agent/tools/` (Nmap, Nuclei, Sqlmap, etc., using `langchain.tools.tool`).
- **Parsing Logic**: `utils/parser.py` (Robust JSON extraction).
- **Execution**: `utils/runner.py` (Subprocess wrapper).

---

## 2. Current Weaknesses (Prior to Refactor)

1.  **Inconsistent Tool Outputs**: Tools returned varying structures. Some tools (like `sqlmap_tool`) performed their own "finding" logic instead of just providing raw/parsed data.
2.  **Direct LLM-Tool Coupling**: Agent nodes passed raw tool outputs (JSON or XML strings) directly to the LLM. While `nmap_tool` parsed XML to a list of dicts, the LLM still saw "raw-ish" data.
3.  **Hallucination Risk**: Prompts, while instructing the LLM to be deterministic, still relied on the LLM to "extract" findings. There was no strict schema validation of the tool outputs *before* the LLM saw them.
4.  **Normalization Missing**: There was no dedicated layer to normalize different tool outputs into a common security schema (e.g., a standard "Port" or "Vulnerability" object) before LLM analysis.
5.  **Evidence vs. Inference**: The boundary between "what the tool found" and "what the LLM thinks" was blurred in the `findings` list.

---

## 3. Hallucination Risks

- **Data Fabrication**: LLMs might invent open ports or CVEs if the tool output is empty or ambiguous.
- **Severity Inflation**: LLMs might exaggerate the risk of a finding without supporting evidence from the tool.
- **Chain of Thought Drift**: In the EXPLOITATION phase, the LLM might propose commands for vulnerabilities it "imagined" in earlier phases.

---

## 4. Parsing Failure Points

- **Truncated Output**: Large Nmap or Nuclei outputs might exceed context windows or be truncated, leading to malformed JSON.
- **JSON Formatting**: LLMs often include conversational noise despite "JSON ONLY" instructions.
- **XML Parsing**: `nmap_tool` uses `xml.etree.ElementTree`, which might crash on malformed or incomplete XML from interrupted scans.

---

## 5. Deterministic Risks

- **Tool Failures**: If a tool fails (e.g., binary missing), some nodes returned `empty_result`, but the workflow continued. A failure in RECON might lead to a cascade of "empty" phases that still consume LLM tokens.
- **State Pollution**: `findings` were appended via `operator.add`. If not carefully managed, duplicate or contradictory findings from different tools might confuse the LLM.

---

## 6. Minimal Refactor Strategy (Implemented)

1.  **Standardized Tool Interface**: Every tool must return a mandatory JSON structure: `tool`, `target`, `status`, `timestamp`, `raw_output`, `parsed_output`, `errors`.
2.  **Normalization Layer**: Implement a layer that maps tool-specific `parsed_output` to a strict Pydantic-based `SecurityState`.
3.  **Analyzer-Only LLM**: Refactor prompts to strictly forbid any output not present in the normalized state. Use "Evidence-Based reasoning" where every finding must point to a specific `evidence_id`.
4.  **Schema Validation**: Use Pydantic to validate LLM outputs and tool outputs.
5.  **Graceful Degeneracy**: If critical tools fail, the agent reports the failure and returns "failed" or "empty_result" status.
