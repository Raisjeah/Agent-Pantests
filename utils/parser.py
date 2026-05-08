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
    Ekstrak dan parse JSON dari output LLM secara robust menggunakan logika final_fix_v2.
    Mendukung format markdown multiple blocks, pembersihan artefak,
    dan fallback greedy untuk menangani noise percakapan.
    """
    if not content:
        return {}

    # 1. Cari blok kode markdown (handle unclosed blocks dan multiple blocks)
    markdown_blocks = re.findall(r"```(?:json)?\s*(.*?)\s*(?:```|$)", content, re.DOTALL | re.IGNORECASE)

    candidates = []
    if markdown_blocks:
        for block in markdown_blocks:
            cleaned = block.strip()
            if cleaned:
                # Bersihkan kata 'json' di awal dan backticks di dalam blok
                cleaned = re.sub(r"^\s*json\s*", "", cleaned, flags=re.IGNORECASE).strip()
                cleaned = cleaned.replace("`", "").strip()
                candidates.append(cleaned)

    # 2. Tambahkan fallback greedy dari seluruh konten
    # Ini menangani kasus di mana LLM menyisipkan JSON tanpa blok kode
    patterns = [r"(\{.*\})", r"(\[.*\])"]
    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            candidate = match.group(1).strip()
            # Bersihkan dari backticks jika ada
            candidate = candidate.replace("`", "").strip()
            if candidate not in candidates:
                candidates.append(candidate)

    # 3. Iterasi candidates dan coba parse
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Coba perbaiki trailing commas
            fixed = re.sub(r",\s*([\]}])", r"\1", candidate)
            try:
                return json.loads(fixed)
            except json.JSONDecodeError:
                continue

    # Jika gagal semua, raise error deskriptif
    raise ValueError(f"Gagal mem-parse JSON dari content ({len(content)} chars): {content}")
