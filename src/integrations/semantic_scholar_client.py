"""Semantic Scholar API client"""

import requests
from typing import List, Dict, Any
from loguru import logger

from src.utils.config import settings


class SemanticScholarClient:
    """Client for searching Semantic Scholar"""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self, api_key: str = None, max_results: int = 50):
        """Initialize Semantic Scholar client

        Args:
            api_key: Optional API key for higher rate limits
            max_results: Maximum number of results per search
        """
        self.api_key = api_key or settings.semantic_scholar_api_key
        self.max_results = max_results
        self.headers = {
            'User-Agent': 'AI-Research-Assistant/1.0 (Educational Purpose)'
        }
        if self.api_key and self.api_key != 'optional_key_here':
            self.headers['x-api-key'] = self.api_key

    def search(
        self,
        query: str,
        max_results: int = None,
        fields: str = None
    ) -> List[Dict[str, Any]]:
        """Search Semantic Scholar for papers

        Args:
            query: Search query
            max_results: Maximum results to return
            fields: Comma-separated fields to return

        Returns:
            List of paper dictionaries
        """
        if max_results is None:
            max_results = self.max_results

        if fields is None:
            fields = "paperId,title,abstract,authors,year,citationCount,url,venue,publicationDate,externalIds"

        logger.info(f"[Semantic Scholar] Searching for: {query} (max: {max_results})")

        url = f"{self.BASE_URL}/paper/search"
        params = {
            'query': query,
            'limit': min(max_results, 100),  # API limit is 100
            'fields': fields
        }

        try:
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            papers = []

            for result in data.get('data', []):
                paper = self._format_paper(result)
                papers.append(paper)

            logger.info(f"[Semantic Scholar] Found {len(papers)} papers")
            return papers

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                logger.warning(f"[Semantic Scholar] 403 Forbidden - Rate limit or API key needed. Skipping Semantic Scholar.")
            else:
                logger.error(f"[Semantic Scholar] HTTP Error: {e}")
            return []
        except Exception as e:
            logger.error(f"[Semantic Scholar] Search error: {e}")
            return []

    def _format_paper(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format Semantic Scholar result to standard format

        Args:
            result: Raw result from API

        Returns:
            Formatted paper dictionary
        """
        # Extract authors
        authors = []
        for author_data in result.get('authors', []):
            name = author_data.get('name', '')
            if name:
                authors.append(name)

        # Parse publication date
        pub_date = result.get('publicationDate', '')
        year = result.get('year', 0)

        paper = {
            'id': result.get('paperId', ''),
            'title': result.get('title', ''),
            'authors': authors,
            'abstract': result.get('abstract', ''),
            'year': year,
            'published_date': pub_date,
            'citations': result.get('citationCount', 0),
            'url': result.get('url', f"https://www.semanticscholar.org/paper/{result.get('paperId', '')}"),
            'venue': result.get('venue', ''),
            'doi': (result.get('externalIds') or {}).get('DOI', ''),
            'source': 'semantic_scholar'
        }

        return paper

    def get_paper(self, paper_id: str, fields: str = None) -> Dict[str, Any]:
        """Get a specific paper by ID

        Args:
            paper_id: Semantic Scholar paper ID
            fields: Fields to return

        Returns:
            Paper dictionary
        """
        if fields is None:
            fields = "paperId,title,abstract,authors,year,citationCount,url,venue,publicationDate,references,citations"

        logger.debug(f"[Semantic Scholar] Fetching paper: {paper_id}")

        url = f"{self.BASE_URL}/paper/{paper_id}"
        params = {'fields': fields}

        try:
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            return self._format_paper(result)

        except Exception as e:
            logger.error(f"[Semantic Scholar] Error fetching paper {paper_id}: {e}")
            return {}

    def get_citations(self, paper_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get papers that cite this paper

        Args:
            paper_id: Semantic Scholar paper ID
            limit: Maximum citations to return

        Returns:
            List of citing papers
        """
        logger.debug(f"[Semantic Scholar] Fetching citations for: {paper_id}")

        url = f"{self.BASE_URL}/paper/{paper_id}/citations"
        params = {
            'limit': limit,
            'fields': 'paperId,title,year,citationCount'
        }

        try:
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            citations = []

            for item in data.get('data', []):
                citing_paper = item.get('citingPaper', {})
                if citing_paper:
                    citations.append(self._format_paper(citing_paper))

            return citations

        except Exception as e:
            logger.error(f"[Semantic Scholar] Error fetching citations: {e}")
            return []

    def get_references(self, paper_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get papers referenced by this paper

        Args:
            paper_id: Semantic Scholar paper ID
            limit: Maximum references to return

        Returns:
            List of referenced papers
        """
        logger.debug(f"[Semantic Scholar] Fetching references for: {paper_id}")

        url = f"{self.BASE_URL}/paper/{paper_id}/references"
        params = {
            'limit': limit,
            'fields': 'paperId,title,year,citationCount'
        }

        try:
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            references = []

            for item in data.get('data', []):
                cited_paper = item.get('citedPaper', {})
                if cited_paper:
                    references.append(self._format_paper(cited_paper))

            return references

        except Exception as e:
            logger.error(f"[Semantic Scholar] Error fetching references: {e}")
            return []
