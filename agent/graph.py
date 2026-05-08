import yaml
from pathlib import Path
from typing import List, Union, Literal
from langgraph.graph import StateGraph, END

from .state import AgentState
from .memory import get_checkpointer
from .agents.recon import recon_node
from .agents.scanning import scanning_node
from .agents.enumeration import enumeration_node
from .agents.vuln_assess import vuln_assess_node
from .agents.exploitation import exploitation_node
from .agents.validator import validator_node as report_node
from .logger import AILogger

config_path = Path(__file__).parent / "config.yaml"
with open(config_path) as f:
    config = yaml.safe_load(f)

logger = AILogger("Graph")

def router(state: AgentState) -> Literal["recon", "scan", "enum", "vuln_analysis", "exploitation", "report", "__end__"]:
    status = state.get("status")
    if status in ["blocked", "insufficient_evidence", "empty_result", "failed"]:
        logger.info(f"Workflow interrupted due to status: {status}")
        return "report"

    current = state.get("current_state")
    if current == "RECON":
        return "scan"
    if current == "SCAN":
        return "enum"
    if current == "ENUM":
        return "vuln_analysis"
    if current == "VULN_ANALYSIS":
        if state.get("confidence", 0) < 0.7:
            logger.warning(f"Confidence {state.get('confidence')} too low for exploitation. Blocking.")
            return "report"
        return "exploitation"
    if current == "EXPLOITATION":
        return "report"

    return "__end__"

def create_graph():
    workflow = StateGraph(AgentState)

    # Simplified 6 Nodes
    workflow.add_node("recon", recon_node)
    workflow.add_node("scan", scanning_node)
    workflow.add_node("enum", enumeration_node)
    workflow.add_node("vuln_analysis", vuln_assess_node)
    workflow.add_node("exploitation", exploitation_node)
    workflow.add_node("report", report_node)

    # Entry point
    workflow.set_entry_point("recon")

    # Transitions with routers
    workflow.add_conditional_edges("recon", router, {
        "scan": "scan",
        "report": "report"
    })
    workflow.add_conditional_edges("scan", router, {
        "enum": "enum",
        "report": "report"
    })
    workflow.add_conditional_edges("enum", router, {
        "vuln_analysis": "vuln_analysis",
        "report": "report"
    })
    workflow.add_conditional_edges("vuln_analysis", router, {
        "exploitation": "exploitation",
        "report": "report"
    })
    workflow.add_conditional_edges("exploitation", router, {
        "report": "report"
    })

    workflow.add_edge("report", END)

    # Checkpointing for resume
    checkpointer = get_checkpointer(config["memory"]["db_path"])

    # Compile with human-in-the-loop interrupts
    # Interrupt before exploitation for safety as per requirements
    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["exploitation"]
    )
