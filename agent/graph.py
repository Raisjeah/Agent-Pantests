import yaml
import time
from pathlib import Path
from typing import List, Union
from functools import wraps
from langgraph.graph import StateGraph, END

from .state import AgentState
from .memory import get_checkpointer
from .agents.passive_recon import passive_recon_node
from .agents.active_recon import active_recon_node
from .agents.scanning import scanning_node
from .agents.enumeration import enumeration_node
from .agents.vuln_assess import vuln_assess_node
from .agents.weaponization import weaponization_node
from .agents.delivery import delivery_node
from .agents.exploitation import exploitation_node
from .agents.access import access_node
from .logger import AILogger

config_path = Path(__file__).parent / "config.yaml"
with open(config_path) as f:
    config = yaml.safe_load(f)

logger = AILogger("Graph")

def delayed_node(func):
    @wraps(func)
    def wrapper(state):
        logger.info(f"Menunggu 2 detik sebelum eksekusi {func.__name__} (Hemat API)...")
        time.sleep(2)
        return func(state)
    return wrapper

def create_graph():
    workflow = StateGraph(AgentState)

    # Add 9 nodes with delay
    workflow.add_node("passive_recon", delayed_node(passive_recon_node))
    workflow.add_node("active_recon", delayed_node(active_recon_node))
    workflow.add_node("scanning", delayed_node(scanning_node))
    workflow.add_node("enumeration", delayed_node(enumeration_node))
    workflow.add_node("vuln_assess", delayed_node(vuln_assess_node))
    workflow.add_node("weaponization", delayed_node(weaponization_node))
    workflow.add_node("delivery", delayed_node(delivery_node))
    workflow.add_node("exploitation", delayed_node(exploitation_node))
    workflow.add_node("access", delayed_node(access_node))

    # Set entry point
    workflow.set_entry_point("passive_recon")

    # Linear workflow
    workflow.add_edge("passive_recon", "active_recon")
    workflow.add_edge("active_recon", "scanning")
    workflow.add_edge("scanning", "enumeration")
    workflow.add_edge("enumeration", "vuln_assess")
    workflow.add_edge("vuln_assess", "weaponization")
    workflow.add_edge("weaponization", "delivery")
    workflow.add_edge("delivery", "exploitation")
    workflow.add_edge("exploitation", "access")
    workflow.add_edge("access", END)

    # Checkpointing for resume
    checkpointer = get_checkpointer(config["memory"]["db_path"])

    # Compile with human-in-the-loop interrupts
    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["weaponization", "exploitation"]
    )
