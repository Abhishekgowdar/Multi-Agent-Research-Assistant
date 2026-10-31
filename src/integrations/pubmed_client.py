"""PubMed API client"""

import requests
from typing import List, Dict, Any
from xml.etree import ElementTree as ET
from loguru import logger

from src.utils.config import settings


class PubMedClient:
    """Client for searching PubMed papers"""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self, email: str = None, max_results: int = 50):
        """Initialize PubMed client

        Args:
            email: Email for PubMed API (optional but recommended)
            max_results: Maximum number of results per search
        """
        self.email = email or settings.pubmed_email or "research_assistant@example.com"
        self.max_results = max_results

    def search(
        self,
        query: str,
        max_results: int = None
    ) -> List[Dict[str, Any]]:
        """Search PubMed for papers

        Args:
            query: Search query
            max_results: Maximum results to return

        Returns:
            List of paper dictionaries
        """
        if max_results is None:
            max_results = self.max_results

        logger.info(f"[PubMed] Searching for: {query} (max: {max_results})")

        try:
            # Step 1: Search for PMIDs
            pmids = self._search_pmids(query, max_results)

            if not pmids:
                logger.warning("[PubMed] No results found")
                return []

            # Step 2: Fetch paper details
            papers = self._fetch_papers(pmids)

            logger.info(f"[PubMed] Found {len(papers)} papers")
            return papers

        except Exception as e:
            logger.error(f"[PubMed] Search error: {e}")
            return []

    def _search_pmids(self, query: str, max_results: int) -> List[str]:
        """Search for PMIDs matching query

        Args:
            query: Search query
            max_results: Maximum results

        Returns:
            List of PMIDs
        """
        url = f"{self.BASE_URL}/esearch.fcgi"
        params = {
            'db': 'pubmed',
            'term': query,
            'retmax': max_results,
            'retmode': 'json',
            'email': self.email
        }

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        pmids = data.get('esearchresult', {}).get('idlist', [])

        return pmids

    def _fetch_papers(self, pmids: List[str]) -> List[Dict[str, Any]]:
        """Fetch paper details for PMIDs

        Args:
            pmids: List of PubMed IDs

        Returns:
            List of paper dictionaries
        """
        if not pmids:
            return []

        url = f"{self.BASE_URL}/efetch.fcgi"
        params = {
            'db': 'pubmed',
            'id': ','.join(pmids),
            'retmode': 'xml',
            'email': self.email
        }

        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()

        # Parse XML
        root = ET.fromstring(response.content)

        papers = []
        for article in root.findall('.//PubmedArticle'):
            try:
                paper = self._parse_article(article)
                if paper:
                    papers.append(paper)
            except Exception as e:
                logger.warning(f"[PubMed] Error parsing article: {e}")
                continue

        return papers

    def _parse_article(self, article: ET.Element) -> Dict[str, Any]:
        """Parse XML article element

        Args:
            article: XML element

        Returns:
            Paper dictionary
        """
        # Extract PMID
        pmid = article.findtext('.//PMID', '')

        # Extract title
        title = article.findtext('.//ArticleTitle', '')

        # Extract abstract
        abstract_texts = article.findall('.//AbstractText')
        abstract = ' '.join([elem.text or '' for elem in abstract_texts])

        # Extract authors
        authors = []
        for author in article.findall('.//Author'):
            last_name = author.findtext('LastName', '')
            fore_name = author.findtext('ForeName', '')
            if last_name:
                authors.append(f"{fore_name} {last_name}".strip())

        # Extract publication date
        year = article.findtext('.//PubDate/Year', '')
        month = article.findtext('.//PubDate/Month', '01')
        day = article.findtext('.//PubDate/Day', '01')

        # Extract journal
        journal = article.findtext('.//Journal/Title', '')

        # Extract DOI
        doi = article.findtext(".//ArticleIdList/ArticleId[@IdType='doi']", '')

        # Build paper dict
        paper = {
            'id': f"PMID:{pmid}",
            'pmid': pmid,
            'title': title,
            'authors': authors,
            'abstract': abstract,
            'year': int(year) if year.isdigit() else 0,
            'published_date': f"{year}-{month.zfill(2)}-{day.zfill(2)}" if year else '',
            'journal': journal,
            'venue': journal,
            'doi': doi,
            'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            'source': 'pubmed',
            'citations': 0  # PubMed doesn't provide citation counts
        }

        return paper

    def get_paper(self, pmid: str) -> Dict[str, Any]:
        """Get a specific paper by PMID

        Args:
            pmid: PubMed ID

        Returns:
            Paper dictionary
        """
        logger.debug(f"[PubMed] Fetching paper: {pmid}")

        papers = self._fetch_papers([pmid])
        return papers[0] if papers else {}
