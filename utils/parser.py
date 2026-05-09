import json
import re
import logging
from typing import Any, Dict, Union, List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def extract_host(target: str) -> str:
    """
    Ekstrak hostname atau IP dari target (URL, IP, atau domain).
    Contoh: http://182.23.82.141/phpmyadmin/ -> 182.23.82.141
    """
    if not target:
        return ""

    # Handle protocol-less URL patterns like example.com/path
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
    # Hapus komentar //
    s = re.sub(r'//.*?\n', '\n', s)
    # Hapus trailing commas
    s = re.sub(r",\s*([\]}])", r"\1", s)
    # Ganti smart quotes jika ada
    s = s.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    return s.strip()

def parse_llm_json(content: str) -> Union[Dict[str, Any], List[Any]]:
    """
    Ekstrak dan parse JSON dari output LLM secara robust.
    Mendukung format markdown multiple blocks, pembersihan artefak,
    dan fallback greedy untuk menangani noise percakapan.
    """
    if not content:
        return {}

    candidates = []

    # 1. Cari blok kode markdown
    markdown_blocks = re.findall(r"```(?:json)?\s*(.*?)\s*(?:```|$)", content, re.DOTALL | re.IGNORECASE)
    for block in markdown_blocks:
        cleaned = block.strip()
        if cleaned:
            # Bersihkan kata 'json' di awal
            cleaned = re.sub(r"^\s*json\s*", "", cleaned, flags=re.IGNORECASE).strip()
            candidates.append(cleaned)

    # 2. Fallback greedy: cari { ... } atau [ ... ] yang paling besar
    # Kita cari semua match dan ambil yang terpanjang
    dict_matches = re.findall(r"(\{.*\})", content, re.DOTALL)
    list_matches = re.findall(r"(\[.*\])", content, re.DOTALL)

    for m in dict_matches + list_matches:
        candidates.append(m.strip())

    # Sort candidates by length (descending) to try the most complete ones first
    candidates.sort(key=len, reverse=True)

    errors = []
    for candidate in candidates:
        candidate = clean_json_string(candidate)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as e:
            # Terakhir, coba bersihkan control characters yang tidak valid
            try:
                # Menghapus non-printable characters kecuali whitespace standar
                fixed = "".join(char for char in candidate if ord(char) >= 32 or char in "\n\r\t")
                return json.loads(fixed)
            except json.JSONDecodeError:
                errors.append(str(e))
                continue

    # Jika semua gagal, coba json.loads pada string murni jika terlihat seperti JSON
    try:
        return json.loads(clean_json_string(content.strip()))
    except json.JSONDecodeError:
        pass

    raise ValueError(f"Gagal mem-parse JSON. Content length: {len(content)}. Errors: {'; '.join(errors[:3])}. Content: {content[:500]}...")
