import json
from pathlib import Path
import yaml
from langchain_core.prompts import ChatPromptTemplate
from agent.llm import llm
from agent.tools.nuclei import nuclei_tool
from agent.logger import AILogger
from utils.parser import parse_llm_json

logger = AILogger("Enumeration")
current_dir = Path(__file__).parent.parent
prompt_path = current_dir / "prompts" / "enumeration.yaml"

def enumeration_node(state):
    target = state["target"]
    logger.info(f"ENUM phase started for {target}")

    scanning_data = state.get("scan", {})

    # Run specific nuclei templates for deep enumeration
    try:
        nuclei_res = nuclei_tool.invoke({"target": target, "template": "http,config,cves"})
    except Exception as e:
        logger.error(f"nuclei failed: {e}")
        nuclei_res = {"error": str(e)}

    has_nuclei = nuclei_res and "error" not in nuclei_res and nuclei_res.get("nuclei_results")

    if not has_nuclei:
        logger.warning(f"No evidence found in ENUM for {target}")
        return {
            "current_state": "ENUM",
            "status": "empty_result",
            "enum": {"nuclei": nuclei_res}
        }

    with open(prompt_path) as f:
        prompt_cfg = yaml.safe_load(f)
    prompt = ChatPromptTemplate.from_messages(prompt_cfg["messages"])

    chain = prompt | llm
    try:
        response = chain.invoke({
            "target": target,
            "scanning_data": json.dumps(scanning_data, indent=2),
            "nuclei_output": json.dumps(nuclei_res, indent=2)
        })
        parsed = parse_llm_json(response.content)

        return {
            "current_state": "ENUM",
            "status": parsed.get("status", "success"),
            "confidence": parsed.get("confidence", 0.5),
            "findings": parsed.get("findings", []),
            "evidence": [{"tool": "enum", "data": {"nuclei": nuclei_res}}],
            "enum": parsed
        }
    except Exception as e:
        logger.error(f"LLM error in ENUM: {e}")
        return {"current_state": "ENUM", "status": "failed", "status_reason": str(e)}
