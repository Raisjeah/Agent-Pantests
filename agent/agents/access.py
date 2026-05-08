import json
from pathlib import Path
import yaml
from langchain_core.prompts import ChatPromptTemplate
from agent.llm import llm
from agent.logger import AILogger
from utils.parser import parse_llm_json
from utils.runner import run_command
import shlex

logger = AILogger("Access")
current_dir = Path(__file__).parent.parent
prompt_path = current_dir / "prompts" / "access.yaml"

def access_node(state):
    target = state["target"]
    logger.info(f"Initial Access & Persistence dimulai: {target}")

    exploitation_data = state.get("exploitation", {})
    results = exploitation_data.get("results", [])

    if not results:
        logger.warning("No exploitation results for access.")
        return {"access": {"status": "skipped", "reason": "no exploitation results"}}

    if not prompt_path.exists():
        logger.error(f"Prompt file not found: {prompt_path}")
        return {"access": {"error": "Prompt not found"}}

    with open(prompt_path) as f:
        prompt_cfg = yaml.safe_load(f)
    prompt = ChatPromptTemplate.from_messages(prompt_cfg["messages"])

    chain = prompt | llm
    access_plan = {}
    try:
        response = chain.invoke({
            "target": target,
            "exploitation_results": json.dumps(results, indent=2)
        })
        parsed = parse_llm_json(response.content)
        access_plan = parsed

        # Execute commands if present
        commands = access_plan.get("commands", [])
        execution_logs = []
        for cmd_str in commands:
            logger.info(f"Executing: {cmd_str}")
            try:
                cmd_list = shlex.split(cmd_str)
                stdout, stderr = run_command(cmd_list)
                execution_logs.append({
                    "command": cmd_str,
                    "stdout": stdout,
                    "stderr": stderr
                })
            except Exception as cmd_err:
                logger.error(f"Command execution error: {cmd_err}")
                execution_logs.append({
                    "command": cmd_str,
                    "error": str(cmd_err)
                })
        access_plan["execution_logs"] = execution_logs

    except Exception as e:
        logger.error(f"LLM analysis error in Access: {e}")

    return {"access": access_plan}
