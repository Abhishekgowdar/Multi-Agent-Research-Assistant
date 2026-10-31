"""CORE API Client - Open access research papers"""

import requests
from typing import Any, List, Dict
from loguru import logger


def _author_names(raw: Any) -> List[str]:
    """CORE returns authors as strings or {'name': ...} objects; keep strings only"""
    names = []
    for author in raw or []:
        name = author.get('name', '') if isinstance(author, dict) else str(author or '')
        if name.strip():
            names.append(name.strip())
    return names[:5] or ['Unknown']


class COREClient:
    """Client for CORE API"""

    def __init__(self):
        self.base_url = "https://api.core.ac.uk/v3"

    def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search for papers on CORE

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of paper dictionaries
        """
        try:
            logger.info(f"Searching CORE for: {query}")

            url = f"{self.base_url}/search/works"
            params = {
                "q": query,
                "limit": max_results
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            papers = []

            for item in data.get('results', []):
                paper = {
                    'title': item.get('title') or 'Unknown',
                    'authors': _author_names(item.get('authors')),
                    'abstract': item.get('abstract') or '',
                    'year': item.get('yearPublished'),
                    'url': item.get('downloadUrl') or next(iter(item.get('sourceFulltextUrls') or []), '') or '',
                    'doi': item.get('doi') or '',
                    'citations': 0,
                    'source': 'CORE'
                }
                papers.append(paper)

            logger.info(f"Found {len(papers)} papers from CORE")
            return papers

        except Exception as e:
            logger.error(f"CORE search error: {e}")
            return []
