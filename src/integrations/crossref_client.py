"""CrossRef API Client - Metadata for research papers"""

import requests
from typing import List, Dict
from loguru import logger


class CrossRefClient:
    """Client for CrossRef API"""

    def __init__(self):
        self.base_url = "https://api.crossref.org"

    def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search for papers on CrossRef

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of paper dictionaries
        """
        try:
            logger.info(f"Searching CrossRef for: {query}")

            url = f"{self.base_url}/works"
            params = {
                "query": query,
                "rows": max_results,
                "select": "title,author,abstract,published,DOI,URL,container-title,is-referenced-by-count"
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            papers = []

            for item in data.get('message', {}).get('items', []):
                # Extract authors
                authors = []
                for author in item.get('author', [])[:3]:
                    name = f"{author.get('given', '')} {author.get('family', '')}".strip()
                    if name:
                        authors.append(name)

                # Extract year
                year = 'N/A'
                if 'published' in item:
                    parts = item['published'].get('date-parts', [[]])
                    if parts and parts[0]:
                        year = str(parts[0][0])

                paper = {
                    'title': item.get('title', ['Unknown'])[0] if item.get('title') else 'Unknown',
                    'authors': authors if authors else ['Unknown'],
                    'abstract': item.get('abstract', ''),
                    'year': year,
                    'url': item.get('URL', f"https://doi.org/{item.get('DOI', '')}"),
                    'doi': item.get('DOI', ''),
                    'venue': (item.get('container-title') or [''])[0],
                    'citations': item.get('is-referenced-by-count', 0),
                    'source': 'CrossRef'
                }
                papers.append(paper)

            logger.info(f"Found {len(papers)} papers from CrossRef")
            return papers

        except Exception as e:
            logger.error(f"CrossRef search error: {e}")
            return []
