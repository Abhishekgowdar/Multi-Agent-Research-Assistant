"""Searcher Agent - Finds relevant papers"""

import math
from typing import Dict, List, Any, Optional
from pathlib import Path
from loguru import logger

from src.agents.base_agent import BaseAgent
from src.utils.config import settings

_embedder = None
_embedder_failed = False


def _get_embedder():
    """ChromaDB's default embedding function, created once"""
    global _embedder, _embedder_failed
    if _embedder is None and not _embedder_failed:
        try:
            from chromadb.utils import embedding_functions
            _embedder = embedding_functions.DefaultEmbeddingFunction()
        except Exception as e:
            _embedder_failed = True
            logger.warning(f"[Searcher] Embedding model unavailable, using title overlap: {e}")
    return _embedder


def _embedding_similarities(papers: List[Dict[str, Any]], query: str) -> Optional[List[float]]:
    """Cosine similarity between the query and each paper's title and abstract"""
    if not settings.get('search.embedding_rank', True):
        return None
    embed = _get_embedder()
    if embed is None:
        return None
    try:
        texts = [query] + [f"{p.get('title') or ''}. {(p.get('abstract') or '')[:1000]}" for p in papers]
        vectors = [[float(x) for x in v] for v in embed(texts)]
    except Exception as e:
        logger.warning(f"[Searcher] Embedding failed, using title overlap: {e}")
        return None

    def cosine(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
        return max(dot / norm, 0.0) if norm else 0.0

    return [cosine(vectors[0], v) for v in vectors[1:]]


def _as_year(value: Any) -> Optional[int]:
    """Year as an int, or None when the source gave something unusable"""
    try:
        year = int(str(value).strip()[:4])
    except (TypeError, ValueError):
        return None
    return year if 1900 <= year <= 2100 else None


class SearcherAgent(BaseAgent):
    """Agent responsible for finding relevant research papers"""

    def __init__(self, memory=None, orchestrator=None):
        super().__init__("searcher", memory, orchestrator)
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """Load the searcher prompt template"""
        prompt_path = Path(__file__).parent.parent.parent / "prompts" / "searcher_prompt.txt"
        if prompt_path.exists():
            return prompt_path.read_text(encoding='utf-8')
        return ""

    def get_role_description(self) -> str:
        return "Find relevant academic papers across multiple databases"

    @staticmethod
    def _clean_terms(query: str, terms: Any) -> List[str]:
        """Original query first, then up to two distinct suggestions from the LLM"""
        cleaned = [query.strip()] if query.strip() else []
        for term in terms if isinstance(terms, list) else []:
            if isinstance(term, str) and term.strip() and term.strip().lower() not in [c.lower() for c in cleaned]:
                cleaned.append(term.strip())
        return cleaned[:3]

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute search task

        Args:
            task: Dictionary containing:
                - query: Research query string
                - max_papers: Maximum papers to find
                - sources: List of data sources to search
                - timeframe: Preferred year range

        Returns:
            Dictionary with search strategy and metadata
        """
        query = task.get('query', '')
        max_papers = task.get('max_papers', 50)
        sources = task.get('sources', ['arxiv', 'pubmed', 'semantic_scholar'])
        timeframe = task.get('timeframe', 'recent')

        self.notify("Starting search for relevant papers", {
            "query": query,
            "sources": sources
        })

        # Build search strategy using LLM
        prompt = self.prompt_template.format(
            query=query,
            max_papers=max_papers,
            timeframe=timeframe,
            sources=", ".join(sources)
        )

        logger.info(f"[Searcher] Analyzing query: {query}")

        # Get search strategy from LLM; fall back to the raw query on any failure
        try:
            strategy = await self._ask_json(prompt, temperature=0.3)
        except Exception as e:
            logger.warning(f"[Searcher] Strategy call failed: {e}")
            strategy = {}

        if not strategy:
            logger.warning("[Searcher] Failed to generate search strategy")
            # Fallback strategy
            strategy = {
                "search_terms": [query],
                "databases": sources,
                "filters": {"year_min": 2020},
                "rationale": "Using direct query as fallback"
            }

        # Store strategy in memory
        self.remember("last_search_strategy", strategy)

        result = {
            "status": "success",
            "query": query,
            "strategy": strategy,
            "search_terms": self._clean_terms(query, strategy.get("search_terms")),
            "databases": strategy.get("databases", sources),
            "filters": strategy.get("filters", {})
        }

        self.notify("Search strategy generated", {
            "terms": strategy.get("search_terms", []),
            "databases": strategy.get("databases", [])
        })

        logger.info(f"[Searcher] Generated {len(strategy.get('search_terms', []))} search terms")

        return result

    def rank_papers(self, papers: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Rank papers by similarity to the query, citations, and recency

        Args:
            papers: List of paper dictionaries
            query: Original search query

        Returns:
            Ranked list of papers (empty if there are no papers)
        """
        if not papers:
            logger.info("[Searcher] No papers to rank")
            return []

        logger.info(f"[Searcher] Ranking {len(papers)} papers")
        similarities = _embedding_similarities(papers, query)
        query_terms = set(query.lower().split())

        for index, paper in enumerate(papers):
            if similarities is not None:
                relevance = similarities[index]
            else:
                title_terms = set((paper.get('title') or '').lower().split())
                relevance = min(len(query_terms & title_terms) / max(len(query_terms), 1), 1.0)

            citations = paper.get('citations', 0)
            citation_score = min(citations / 100, 1.0) if isinstance(citations, (int, float)) else 0.0

            year = _as_year(paper.get('year'))
            recency_score = 1.0 if year is not None and year >= 2022 else 0.0

            paper['relevance_score'] = round(0.6 * relevance + 0.2 * citation_score + 0.2 * recency_score, 4)

        ranked = sorted(papers, key=lambda p: p.get('relevance_score', 0), reverse=True)
        logger.info(f"[Searcher] Ranking complete. Top paper score: {ranked[0]['relevance_score']:.2f}")
        return ranked
