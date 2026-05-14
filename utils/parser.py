import json
import re
import logging
from typing import Any, Dict, Union, List, Type, TypeVar
from urllib.parse import urlparse
from pydantic import BaseModel

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

def extract_host(target: str) -> str:
    """
    Ekstrak hostname atau IP dari target (URL, IP, atau domain).
    """
    if not target:
        return ""

    if "/" in target and not (target.startswith("http://") or target.startswith("https://")):
        parts = target.split("/", 1)
        potential_host = parts[0]
        if "." in potential_host and " " not in potential_host:
             target = "http://" + target

    if target.startswith("http://") or target.startswith("https://"):
        try:
            parsed = urlparse(target)
            return parsed.hostname or target
        except Exception:
            return target

    return target

def clean_json_string(s: str) -> str:
    """Pembersihan string JSON dari noise umum LLM."""
    s = re.sub(r'//.*?\n', '\n', s)
    s = re.sub(r",\s*([\]}])", r"\1", s)
    s = s.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    return s.strip()

def parse_llm_json(content: str) -> Union[Dict[str, Any], List[Any]]:
    """
    Ekstrak dan parse JSON dari output LLM secara robust.
    """
    if not content:
        return {}

    candidates = []
    markdown_blocks = re.findall(r"```(?:json)?\s*(.*?)\s*(?:```|$)", content, re.DOTALL | re.IGNORECASE)
    for block in markdown_blocks:
        cleaned = block.strip()
        if cleaned:
            cleaned = re.sub(r"^\s*json\s*", "", cleaned, flags=re.IGNORECASE).strip()
            candidates.append(cleaned)

    dict_matches = re.findall(r"(\{.*\})", content, re.DOTALL)
    list_matches = re.findall(r"(\[.*\])", content, re.DOTALL)

    for m in dict_matches + list_matches:
        candidates.append(m.strip())

    candidates.sort(key=len, reverse=True)

    errors = []
    for candidate in candidates:
        candidate = clean_json_string(candidate)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as e:
            try:
                fixed = "".join(char for char in candidate if ord(char) >= 32 or char in "\n\r\t")
                return json.loads(fixed)
            except json.JSONDecodeError:
                errors.append(str(e))
                continue

    try:
        return json.loads(clean_json_string(content.strip()))
    except json.JSONDecodeError:
        pass

    raise ValueError(f"Gagal mem-parse JSON. Content length: {len(content)}. Errors: {'; '.join(errors[:3])}. Content: {content[:500]}...")

def safe_json_parse(content: str, model: Type[T]) -> T:
    """
    Parse LLM output and validate against a Pydantic model.
    """
    data = parse_llm_json(content)
    if isinstance(data, list) and not isinstance(data, dict):
        # If we expected a dict (model) but got a list, this is a schema mismatch
        raise ValueError(f"Expected dictionary for model {model.__name__}, but got list.")

    return model.model_validate(data)
