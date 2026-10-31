"""arXiv API client"""

import arxiv
from typing import List, Dict, Any
from loguru import logger


class ArxivClient:
    """Client for searching arXiv papers"""

    def __init__(self, max_results: int = 50):
        """Initialize arXiv client

        Args:
            max_results: Maximum number of results per search
        """
        self.max_results = max_results
        self.client = arxiv.Client()

    def search(
        self,
        query: str,
        max_results: int = None,
        sort_by: str = "relevance"
    ) -> List[Dict[str, Any]]:
        """Search arXiv for papers

        Args:
            query: Search query
            max_results: Maximum results to return
            sort_by: Sort criterion (relevance, lastUpdatedDate, submittedDate)

        Returns:
            List of paper dictionaries
        """
        if max_results is None:
            max_results = self.max_results

        logger.info(f"[arXiv] Searching for: {query} (max: {max_results})")

        # Map sort_by to arxiv.SortCriterion
        sort_criterion = arxiv.SortCriterion.Relevance
        if sort_by == "lastUpdatedDate":
            sort_criterion = arxiv.SortCriterion.LastUpdatedDate
        elif sort_by == "submittedDate":
            sort_criterion = arxiv.SortCriterion.SubmittedDate

        try:
            # Create search
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=sort_criterion
            )

            # Execute search
            results = list(self.client.results(search))

            # Convert to standard format
            papers = []
            for result in results:
                paper = {
                    'id': result.entry_id.split('/')[-1],  # Extract ID from URL
                    'title': result.title,
                    'authors': [author.name for author in result.authors],
                    'abstract': result.summary,
                    'year': result.published.year,
                    'published_date': result.published.strftime('%Y-%m-%d'),
                    'updated_date': result.updated.strftime('%Y-%m-%d'),
                    'url': result.entry_id,
                    'pdf_url': result.pdf_url,
                    'categories': result.categories,
                    'primary_category': result.primary_category,
                    'doi': getattr(result, 'doi', None) or '',
                    'venue': 'arXiv preprint',
                    'source': 'arxiv'
                }

                # arXiv doesn't provide citation counts directly
                paper['citations'] = 0

                papers.append(paper)

            logger.info(f"[arXiv] Found {len(papers)} papers")
            return papers

        except Exception as e:
            logger.error(f"[arXiv] Search error: {e}")
            return []

    def get_paper(self, paper_id: str) -> Dict[str, Any]:
        """Get a specific paper by ID

        Args:
            paper_id: arXiv paper ID

        Returns:
            Paper dictionary
        """
        logger.debug(f"[arXiv] Fetching paper: {paper_id}")

        try:
            search = arxiv.Search(id_list=[paper_id])
            result = next(self.client.results(search))

            paper = {
                'id': result.entry_id.split('/')[-1],
                'title': result.title,
                'authors': [author.name for author in result.authors],
                'abstract': result.summary,
                'year': result.published.year,
                'published_date': result.published.strftime('%Y-%m-%d'),
                'url': result.entry_id,
                'pdf_url': result.pdf_url,
                'categories': result.categories,
                'source': 'arxiv'
            }

            return paper

        except Exception as e:
            logger.error(f"[arXiv] Error fetching paper {paper_id}: {e}")
            return {}
