"""PLOS ONE API Client - Open access journals"""

import requests
from typing import List, Dict
from loguru import logger


class PLOSClient:
    """Client for PLOS ONE API"""

    def __init__(self):
        self.base_url = "https://api.plos.org/search"

    def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search for papers on PLOS ONE

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of paper dictionaries
        """
        try:
            logger.info(f"Searching PLOS ONE for: {query}")

            params = {
                "q": query,
                "rows": max_results,
                "wt": "json",
                "fl": "id,title,author,abstract,publication_date"
            }

            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            papers = []

            for item in data.get('response', {}).get('docs', []):
                # Extract authors
                authors = item.get('author', ['Unknown'])
                if isinstance(authors, list):
                    authors = authors[:3]
                else:
                    authors = [authors]

                # Extract year
                year = 'N/A'
                pub_date = item.get('publication_date', '')
                if pub_date:
                    year = pub_date[:4]

                paper = {
                    'title': item.get('title', 'Unknown'),
                    'authors': authors,
                    'abstract': item.get('abstract', [''])[0] if isinstance(item.get('abstract'), list) else item.get('abstract', ''),
                    'year': year,
                    'url': f"https://journals.plos.org/plosone/article?id={item.get('id', '')}",
                    'doi': item.get('id', ''),
                    'source': 'PLOS ONE'
                }
                papers.append(paper)

            logger.info(f"Found {len(papers)} papers from PLOS ONE")
            return papers

        except Exception as e:
            logger.error(f"PLOS ONE search error: {e}")
            return []
