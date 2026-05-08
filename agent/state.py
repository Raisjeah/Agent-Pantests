from typing import TypedDict, Optional, List, Annotated
import operator

class AgentState(TypedDict):
    target: str
    scope: str
    deep: bool
    findings: Annotated[List[dict], operator.add]
    final_report: Optional[dict]
    # 9 Node Data tracking
    passive_recon: Optional[dict]
    active_recon: Optional[dict]
    scanning: Optional[dict]
    enumeration: Optional[dict]
    vuln_assess: Optional[dict]
    weaponization: Optional[dict]
    delivery: Optional[dict]
    exploitation: Optional[dict]
    access: Optional[dict]
