import json
import re
from typing import Any, Dict, Union
from urllib.parse import urlparse

def extract_host(target: str) -> str:
    """
    Ekstrak hostname atau IP dari target (URL, IP, atau domain).
    Contoh: http://182.23.82.141/phpmyadmin/ -> 182.23.82.141
    """
    if not target:
        return ""

    # Handle protocol-less URL patterns like example.com/path
    if "/" in target and not (target.startswith("http://") or target.startswith("https://")):
        # Simple heuristic: if it has a slash but no protocol, it might be a path
        # Check if it looks like an IP/domain before the slash
        parts = target.split("/", 1)
        potential_host = parts[0]
        # Very basic check for domain/IP: contains dot and no space
        if "." in potential_host and " " not in potential_host:
             target = "http://" + target

    if target.startswith("http://") or target.startswith("https://"):
        try:
            parsed = urlparse(target)
            return parsed.hostname or target
        except Exception:
            return target

    return target

def parse_llm_json(content: str) -> Union[Dict[str, Any], list]:
    """
    Ekstrak dan parse JSON dari output LLM.
    Mendukung format markdown ```json ... ``` atau string JSON mentah.
    """
    # Bersihkan whitespace
    content = content.strip()

    # Cari blok kode markdown (handle unclosed blocks as well)
    json_match = re.search(r"```(?:json)?\s*(.*?)\s*(?:```|$)", content, re.DOTALL)
    if json_match:
        json_str = json_match.group(1).strip()
    else:
        json_str = content

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Percobaan terakhir: cari pattern { ... } atau [ ... ]
        pattern_match = re.search(r"(\{.*\}|\[.*\])", json_str, re.DOTALL)
        if pattern_match:
            try:
                return json.loads(pattern_match.group(1))
            except json.JSONDecodeError:
                pass

        # Jika gagal semua, raise error yang lebih deskriptif
        raise ValueError(f"Gagal mem-parse JSON dari content: {content[:100]}...")
