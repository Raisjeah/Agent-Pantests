from typing import TypedDict, Optional, List, Annotated, Any
import operator

class AgentState(TypedDict):
    # Core target info
    target: str
    scope: str
    deep: bool

    # Workflow control
    current_state: str # RECON, SCAN, ENUM, VULN_ANALYSIS, EXPLOITATION, REPORT, ERROR
    status: str        # success, failed, blocked, insufficient_evidence, empty_result
    status_reason: Optional[str]
    confidence: float

    # Evidence & Data
    findings: Annotated[List[dict], operator.add]
    evidence: Annotated[List[dict], operator.add]

    # Node-specific results
    recon: Optional[dict]
    scan: Optional[dict]
    enum: Optional[dict]
    vuln_analysis: Optional[dict]
    exploitation: Optional[dict]
    report: Optional[dict]

    # Compatibility with older nodes if needed during transition
    final_report: Optional[dict]
