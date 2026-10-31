"""IEEE Xplore API Client - Engineering and Computer Science papers"""

import requests
from typing import List, Dict
from loguru import logger
import os


class IEEEClient:
    """Client for IEEE Xplore API"""

    def __init__(self):
        self.base_url = "https://ieeexploreapi.ieee.org/api/v1/search/articles"
        self.api_key = os.getenv('IEEE_API_KEY', '')

    def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search for papers on IEEE Xplore

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of paper dictionaries
        """
        if not self.api_key or self.api_key == 'your_ieee_key_here':
            logger.info("IEEE API key not configured. Skipping IEEE search. Get a FREE key at: https://developer.ieee.org/member/register")
            return []

        try:
            logger.info(f"Searching IEEE Xplore for: {query}")

            params = {
                "apikey": self.api_key,
                "querytext": query,
                "max_records": max_results,
                "format": "json"
            }

            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            papers = []

            for item in data.get('articles', []):
                # Extract authors
                authors = []
                for author in item.get('authors', {}).get('authors', [])[:3]:
                    name = author.get('full_name', 'Unknown')
                    authors.append(name)

                paper = {
                    'title': item.get('title', 'Unknown'),
                    'authors': authors if authors else ['Unknown'],
                    'abstract': item.get('abstract', ''),
                    'year': str(item.get('publication_year', 'N/A')),
                    'url': item.get('pdf_url') or item.get('html_url') or '',
                    'doi': item.get('doi', ''),
                    'venue': item.get('publication_title', ''),
                    'citations': item.get('citing_paper_count', 0),
                    'source': 'IEEE Xplore'
                }
                papers.append(paper)

            logger.info(f"Found {len(papers)} papers from IEEE Xplore")
            return papers

        except Exception as e:
            logger.error(f"IEEE Xplore search error: {e}")
            return []
