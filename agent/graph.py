import yaml
from typing import List
from langgraph.graph import StateGraph, END
from langgraph.types import Send
from langgraph.checkpoint.sqlite import SqliteSaver

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
    scope = state['scope'].split(',')
    sends = []
    if 'web' in scope or 'all' in scope:
        sends.append(Send("web_agent", state))
    if 'os' in scope or 'all' in scope:
        sends.append(Send("os_agent", state))
    if 'mobile' in scope or 'all' in scope:
        sends.append(Send("mobile_agent", state))
    if 'code' in scope or 'all' in scope:
        sends.append(Send("code_agent", state))
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
    workflow.add_conditional_edges("recon", route_after_recon)

    # Setelah agen spesialis, langsung ke validator
    workflow.add_edge("web_agent", "validator")
    workflow.add_edge("os_agent", "validator")
    workflow.add_edge("mobile_agent", "validator")
    workflow.add_edge("code_agent", "validator")
    workflow.add_edge("validator", END)

    # Checkpointing untuk resume
    checkpointer = get_checkpointer(config["memory"]["db_path"])
    return workflow.compile(checkpointer=checkpointer)
