import json
from pathlib import Path
import yaml
from langchain_core.prompts import ChatPromptTemplate
from agent.llm import llm
from agent.tools.semgrep import semgrep_tool
from agent.logger import AILogger
from utils.parser import parse_llm_json

logger = AILogger("CodeAgent")
current_dir = Path(__file__).parent.parent
prompt_path = current_dir / "prompts" / "code.yaml"

with open(prompt_path) as f:
    prompt_cfg = yaml.safe_load(f)
prompt = ChatPromptTemplate.from_messages(prompt_cfg["messages"])

def code_node(state):
    target = state["target"]  # path ke direktori source code
    logger.info(f"Code agent memeriksa {target}")
    findings = []

    try:
        semgrep_res = semgrep_tool.invoke({"target": target})
        findings.append(semgrep_res)
    except Exception as e:
        logger.error(f"Semgrep error: {e}")

    # LLM analisis dari recon_data
    recon_data = state.get("recon_data")
    if recon_data:
        chain = prompt | llm
        try:
            response = chain.invoke({
                "target": target,
                "recon_data": json.dumps(recon_data, indent=2)
            })
            parsed = parse_llm_json(response.content)
            extra = []
            if isinstance(parsed, dict):
                extra = parsed.get("findings", [])
            elif isinstance(parsed, list):
                extra = parsed
            findings.extend(extra)
        except Exception as e:
            logger.error(f"LLM analysis error in CodeAgent: {e}")
    else:
        logger.warning("No recon_data available for CodeAgent")

    return {"findings": findings}
