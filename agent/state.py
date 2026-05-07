from typing import TypedDict, Optional, List, Annotated
import operator

class AgentState(TypedDict):
    target: str
    scope: str
    deep: bool
    recon_data: Optional[dict]
    findings: Annotated[List[dict], operator.add]  # otomatis gabung
    final_report: Optional[dict]
