"""Stable paper identity across data sources"""

import hashlib
import re
from typing import Any, Dict, List, Set


def normalize_doi(doi: Any) -> str:
    """Lowercase DOI without a URL prefix, or an empty string"""
    if not isinstance(doi, str):
        return ""
    value = re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", doi.strip().lower())
    return value if value.startswith("10.") else ""


def normalize_title(title: Any) -> str:
    """Lowercase title with punctuation removed, for matching"""
    text = title if isinstance(title, str) else ""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _digest(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def paper_key(paper: Dict[str, Any]) -> str:
    """Most specific stable key available: DOI, then source ID, then URL, then title"""
    doi = normalize_doi(paper.get("doi"))
    if doi:
        return f"doi:{doi}"

    raw_id = str(paper.get("id") or "").strip()
    if raw_id:
        source = str(paper.get("source") or "id").lower().replace(" ", "_")
        return f"{source}:{raw_id.lower()}"

    url = str(paper.get("url") or "").strip().lower()
    if url:
        return f"url:{_digest(url)}"

    return f"title:{_digest(normalize_title(paper.get('title')))}"


def dedupe_papers(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Keep the first paper for each DOI, source ID, URL, or normalized title, and assign ids"""
    seen: Set[str] = set()
    unique: List[Dict[str, Any]] = []

    for paper in papers:
        key = paper_key(paper)
        title = normalize_title(paper.get("title"))
        keys = {key}
        if title and title != "unknown":
            keys.add(f"title:{_digest(title)}")

        if keys & seen:
            continue
        seen |= keys

        paper["key"] = key
        if not paper.get("id"):
            paper["id"] = key
        unique.append(paper)

    return unique
