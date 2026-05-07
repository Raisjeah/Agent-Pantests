import yaml
from typing import List, Union
from langgraph.graph import StateGraph, END
from langgraph.types import Send

from .state import AgentState
from .safety import SafetyChecker
from .memory import get_checkpointer
from .agents.recon import recon_node
from .agents.web import web_node
from .agents.os_agent import os_node
from .agents.mobile import mobile_node
from .agents.code import code_node
from .agents.validator import validator_node
from .logger import AILogger

with open("config.yaml") as f:
    config = yaml.safe_load(f)

safety = SafetyChecker(config["safety"])
logger = AILogger("Graph")

def route_after_recon(state: AgentState) -> List[Send]:
    """Mengirim state ke agen spesialis sesuai scope (paralel)."""
    scope = state.get('scope', 'all').split(',')
    sends = []

    # Map scope keywords to node names
    mapping = {
        'web': 'web_agent',
        'os': 'os_agent',
        'mobile': 'mobile_agent',
        'code': 'code_agent'
    }

    for key, node_name in mapping.items():
        if key in scope or 'all' in scope:
            sends.append(Send(node_name, state))

    if not sends:
        # Jika tidak ada scope yang cocok, langsung ke validator atau end
        # Namun dalam case ini kita asumsikan minimal satu atau recon sudah cukup
        pass

    return sends

def create_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("recon", recon_node)
    workflow.add_node("web_agent", web_node)
    workflow.add_node("os_agent", os_node)
    workflow.add_node("mobile_agent", mobile_node)
    workflow.add_node("code_agent", code_node)
    workflow.add_node("validator", validator_node)

    workflow.set_entry_point("recon")

    # Menggunakan conditional edges untuk fan-out
    workflow.add_conditional_edges("recon", route_after_recon)

    # Semua agen spesialis kembali ke validator (fan-in)
    workflow.add_edge("web_agent", "validator")
    workflow.add_edge("os_agent", "validator")
    workflow.add_edge("mobile_agent", "validator")
    workflow.add_edge("code_agent", "validator")

    workflow.add_edge("validator", END)

    # Checkpointing untuk resume
    checkpointer = get_checkpointer(config["memory"]["db_path"])
    return workflow.compile(checkpointer=checkpointer)
