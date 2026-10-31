"""Google Scholar Client - Most popular for Indian students"""

import requests
from typing import List, Dict
from loguru import logger
from bs4 import BeautifulSoup
import time


class GoogleScholarClient:
    """Client for Google Scholar (scraping-based)"""

    def __init__(self):
        self.base_url = "https://scholar.google.com/scholar"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search for papers on Google Scholar

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of paper dictionaries
        """
        try:
            logger.info(f"Searching Google Scholar for: {query}")

            params = {
                "q": query,
                "num": min(max_results, 10)  # Google Scholar limits per page
            }

            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=30
            )

            if response.status_code != 200:
                logger.warning(f"Google Scholar returned status {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            papers = []

            # Parse search results
            for result in soup.select('.gs_ri')[:max_results]:
                try:
                    # Title
                    title_elem = result.select_one('.gs_rt')
                    title = title_elem.get_text() if title_elem else 'Unknown'

                    # URL
                    url = ''
                    link = title_elem.select_one('a') if title_elem else None
                    if link and link.get('href'):
                        url = link.get('href')

                    # Fallback: Create Google Scholar search URL if no direct link
                    if not url or url == '':
                        import urllib.parse
                        search_term = urllib.parse.quote(title[:100])  # First 100 chars of title
                        url = f"https://scholar.google.com/scholar?q={search_term}"

                    # Authors and year
                    meta_elem = result.select_one('.gs_a')
                    authors = ['Unknown']
                    year = 'N/A'
                    if meta_elem:
                        meta_text = meta_elem.get_text()
                        parts = meta_text.split('-')
                        if parts:
                            # First part usually has authors
                            authors = [parts[0].strip()]
                        # Try to extract year
                        import re
                        year_match = re.search(r'\b(19|20)\d{2}\b', meta_text)
                        if year_match:
                            year = year_match.group()

                    # Abstract
                    abstract_elem = result.select_one('.gs_rs')
                    abstract = abstract_elem.get_text() if abstract_elem else ''

                    paper = {
                        'title': title,
                        'authors': authors,
                        'abstract': abstract,
                        'year': year,
                        'url': url,
                        'source': 'Google Scholar'
                    }
                    papers.append(paper)

                except Exception as e:
                    logger.debug(f"Error parsing Google Scholar result: {e}")
                    continue

            logger.info(f"Found {len(papers)} papers from Google Scholar")

            # Be nice to Google - add small delay
            time.sleep(1)

            return papers

        except Exception as e:
            logger.error(f"Google Scholar search error: {e}")
            return []
