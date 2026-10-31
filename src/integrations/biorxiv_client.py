"""bioRxiv/medRxiv API Client - Biology and medical preprints"""

import requests
from typing import List, Dict
from loguru import logger


class BioRxivClient:
    """Client for bioRxiv and medRxiv APIs"""

    def __init__(self):
        self.base_url = "https://api.biorxiv.org/details/biorxiv"

    def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search for papers on bioRxiv

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of paper dictionaries
        """
        try:
            logger.info(f"Searching bioRxiv for: {query}")

            # bioRxiv API doesn't have direct search, so we'll get recent papers
            # and filter by query terms
            url = f"{self.base_url}/2024-01-01/2024-12-31/0/100"

            response = requests.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()
            papers = []
            query_lower = query.lower()

            for item in data.get('collection', []):
                # Filter by query in title or abstract
                title = item.get('title', '').lower()
                abstract = item.get('abstract', '').lower()

                if query_lower in title or query_lower in abstract:
                    paper = {
                        'title': item.get('title', 'Unknown'),
                        'authors': [a.strip() for a in item.get('authors', 'Unknown').split(';')[:3]],
                        'abstract': item.get('abstract', ''),
                        'year': item.get('date', 'N/A')[:4],
                        'url': f"https://www.biorxiv.org/content/{item.get('doi', '')}",
                        'doi': item.get('doi', ''),
                        'source': 'bioRxiv'
                    }
                    papers.append(paper)

                    if len(papers) >= max_results:
                        break

            logger.info(f"Found {len(papers)} papers from bioRxiv")
            return papers

        except Exception as e:
            logger.error(f"bioRxiv search error: {e}")
            return []
