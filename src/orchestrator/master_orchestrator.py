"""Master Orchestrator - Coordinates all agents"""

import asyncio
import hashlib
import math
from typing import Dict, List, Any, Optional, Callable
from loguru import logger

from src.agents.searcher_agent import SearcherAgent
from src.agents.analyzer_agent import AnalyzerAgent
from src.agents.fact_checker_agent import FactCheckerAgent
from src.agents.synthesizer_agent import SynthesizerAgent
from src.memory.vector_memory import VectorMemory
from src.utils.cache import SQLiteCache, get_cache
from src.utils.paper_keys import dedupe_papers, normalize_title
from src.integrations.arxiv_client import ArxivClient
from src.integrations.pubmed_client import PubMedClient
from src.integrations.semantic_scholar_client import SemanticScholarClient
from src.integrations.core_client import COREClient
from src.integrations.crossref_client import CrossRefClient
from src.integrations.biorxiv_client import BioRxivClient
from src.integrations.plos_client import PLOSClient
from src.integrations.ieee_client import IEEEClient
from src.integrations.google_scholar_client import GoogleScholarClient
from src.utils.config import settings


MAX_PARALLEL_SEARCHES = 6


class MasterOrchestrator:
    """Orchestrates multiple agents to complete research tasks"""

    def __init__(self, progress_callback: Optional[Callable] = None):
        """Initialize orchestrator

        Args:
            progress_callback: Optional callback for progress updates
        """
        # Initialize shared memory
        self.memory = VectorMemory()

        # Initialize agents
        self.agents = {
            'searcher': SearcherAgent(memory=self.memory, orchestrator=self),
            'analyzer': AnalyzerAgent(memory=self.memory, orchestrator=self),
            'fact_checker': FactCheckerAgent(memory=self.memory, orchestrator=self),
            'synthesizer': SynthesizerAgent(memory=self.memory, orchestrator=self)
        }

        # Initialize data source clients
        self.data_sources = {
            'arxiv': ArxivClient(),
            'pubmed': PubMedClient(),
            'semantic_scholar': SemanticScholarClient(),
            'core': COREClient(),
            'crossref': CrossRefClient(),
            'biorxiv': BioRxivClient(),
            'plos': PLOSClient(),
            'ieee': IEEEClient(),
            'google_scholar': GoogleScholarClient()
        }

        # Message queue for agent communication
        self.message_queue = asyncio.Queue()

        # Progress callback
        self.progress_callback = progress_callback

        logger.info("MasterOrchestrator initialized with 4 agents and 9 data sources")

    async def research(
        self,
        query: str,
        max_papers: int = 20,
        sources: List[str] = None
    ) -> Dict[str, Any]:
        """Execute complete research workflow

        Args:
            query: Research question
            max_papers: Maximum papers to analyze
            sources: Data sources to use

        Returns:
            Complete research results including literature review
        """
        logger.info(f"Starting research workflow for query: {query}")
        self._notify_progress("Starting research", {"query": query})

        if sources is None:
            sources = ['arxiv', 'pubmed', 'semantic_scholar', 'core', 'crossref', 'biorxiv', 'plos', 'ieee', 'google_scholar']

        # Filter available sources
        sources = [s for s in sources if s in self.data_sources]
        max_papers = max(1, min(int(max_papers or 20), 50))

        if not sources:
            return {"status": "error", "message": "No valid data sources were selected"}

        try:
            # Phase 1: Search for papers
            papers = await self._phase_search(query, max_papers, sources)

            if not papers:
                logger.warning("No papers found")
                return {"status": "no_results", "message": "No papers found for query"}

            # Phase 2: Analyze papers
            analyses = await self._phase_analyze(papers, query)

            if not analyses:
                logger.warning("No successful analyses")
                return {"status": "error", "message": "Failed to analyze papers"}

            # Phase 3: Verify findings
            verifications = await self._phase_verify(analyses, papers)

            # Phase 4: Synthesize results
            synthesis = await self._phase_synthesize(query, papers, analyses, verifications)
            if synthesis.get('status') != 'success':
                return {"status": "error", "message": "Literature review could not be generated"}

            # Build final result
            result = {
                "status": "success",
                "query": query,
                "papers_found": len(papers),
                "papers_analyzed": len(analyses),
                "literature_review": synthesis.get('review', ''),
                "truncated": synthesis.get('truncated', False),
                "must_read_papers": synthesis.get('must_read_papers', []),
                "metadata": {
                    "sources_searched": sources,
                    "average_confidence": synthesis.get('average_confidence', 0.5),
                    "total_papers": len(papers)
                }
            }

            # Store complete result in memory
            self.memory.store(
                id=f"research:{hashlib.sha256(query.encode()).hexdigest()[:16]}",
                content=result,
                metadata={"type": "research_result", "query": query}
            )

            logger.info("Research workflow completed successfully")
            self._notify_progress("Research complete", result)

            return result

        except Exception as e:
            logger.error(f"Research workflow error: {e}")
            return {"status": "error", "message": str(e)}

    async def _phase_search(
        self,
        query: str,
        max_papers: int,
        sources: List[str]
    ) -> List[Dict[str, Any]]:
        """Phase 1: Search for papers

        Args:
            query: Search query
            max_papers: Maximum papers to find
            sources: Data sources to search

        Returns:
            List of papers
        """
        logger.info(f"[Phase 1] Searching for papers across {len(sources)} sources")
        self._notify_progress("Searching for papers", {"sources": sources})

        # Get search strategy from Searcher agent
        search_task = {
            'query': query,
            'max_papers': max_papers,
            'sources': sources,
            'timeframe': 'recent'
        }

        strategy_result = await self.agents['searcher'].execute(search_task)
        search_terms = strategy_result.get('search_terms') or [query]

        logger.info(f"[Phase 1] Using search terms: {search_terms}")

        # Every term goes to every source, with a bounded number of requests in flight
        gate = asyncio.Semaphore(MAX_PARALLEL_SEARCHES)

        async def guarded_search(source: str, term: str) -> List[Dict[str, Any]]:
            async with gate:
                return await self._search_source(source, term, max_papers)

        results = await asyncio.gather(
            *(guarded_search(source, term) for term in search_terms for source in sources),
            return_exceptions=True
        )

        candidates: List[Dict[str, Any]] = []
        for result in results:
            if isinstance(result, list):
                candidates.extend(result)

        # Papers without a real title cannot be analyzed or cited meaningfully
        unique_papers = [
            paper for paper in dedupe_papers(candidates)
            if normalize_title(paper.get('title')) not in ('', 'unknown')
        ]
        if not unique_papers:
            logger.warning("[Phase 1] No papers returned by any source")
            return []

        ranked_papers = self.agents['searcher'].rank_papers(unique_papers, query)
        final_papers = self._select_balanced(ranked_papers, sources, max_papers)

        # Store in memory
        for paper in final_papers:
            self.memory.store(
                id=f"paper:{paper['id']}",
                content=paper,
                metadata={"type": "paper", "source": str(paper.get('source', ''))}
            )

        logger.info(f"[Phase 1] Found {len(final_papers)} papers")
        self._notify_progress("Papers found", {"count": len(final_papers)})

        return final_papers

    @staticmethod
    def _select_balanced(ranked: List[Dict[str, Any]], sources: List[str], max_papers: int) -> List[Dict[str, Any]]:
        """Take the best papers while giving every source a fair share"""
        cap = math.ceil(max_papers / max(len(sources), 1))
        taken: List[Dict[str, Any]] = []
        per_source: Dict[str, int] = {}
        leftovers: List[Dict[str, Any]] = []

        for paper in ranked:
            source = str(paper.get('source', ''))
            if per_source.get(source, 0) < cap and len(taken) < max_papers:
                taken.append(paper)
                per_source[source] = per_source.get(source, 0) + 1
            else:
                leftovers.append(paper)

        for paper in leftovers:
            if len(taken) >= max_papers:
                break
            taken.append(paper)
        return taken

    async def _search_source(
        self,
        source: str,
        query: str,
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Search a single data source

        Args:
            source: Source name
            query: Search query
            max_results: Maximum results

        Returns:
            List of papers
        """
        client = self.data_sources.get(source)
        if not client:
            return []

        cache = get_cache()
        key = SQLiteCache.make_key("search", source, query, max_results) if cache else None
        cached = cache.get(key) if cache else None
        if cached is not None:
            logger.info(f"[Cache] Reused {source} results for '{query}'")
            return cached

        try:
            papers = await asyncio.to_thread(client.search, query, max_results=max_results) or []
        except Exception as e:
            logger.error(f"Error searching {source}: {e}")
            return []

        if cache and papers:
            cache.set(key, papers)
        return papers

    async def _phase_analyze(
        self,
        papers: List[Dict[str, Any]],
        query: str
    ) -> List[Dict[str, Any]]:
        """Phase 2: Analyze papers

        Args:
            papers: Papers to analyze
            query: Original query

        Returns:
            List of analyses
        """
        logger.info(f"[Phase 2] Analyzing {len(papers)} papers")
        self._notify_progress("Analyzing papers", {"count": len(papers)})

        analyze_task = {
            'papers': papers,
            'query': query
        }

        result = await self.agents['analyzer'].execute(analyze_task)
        analyses = result.get('analyses', [])

        logger.info(f"[Phase 2] Completed {len(analyses)} analyses")
        self._notify_progress("Analysis complete", {"count": len(analyses)})

        return analyses

    async def _phase_verify(
        self,
        analyses: List[Dict[str, Any]],
        papers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Phase 3: Verify findings

        Args:
            analyses: Paper analyses
            papers: Original papers

        Returns:
            List of verifications
        """
        logger.info(f"[Phase 3] Verifying {len(analyses)} analyses")
        self._notify_progress("Verifying findings", {"count": len(analyses)})

        verify_task = {
            'analyses': analyses,
            'papers': papers
        }

        result = await self.agents['fact_checker'].execute(verify_task)
        verifications = result.get('verifications', [])

        logger.info(f"[Phase 3] Completed {len(verifications)} verifications")
        self._notify_progress("Verification complete", {
            "count": len(verifications),
            "avg_confidence": result.get('average_confidence', 0.5)
        })

        return verifications

    async def _phase_synthesize(
        self,
        query: str,
        papers: List[Dict[str, Any]],
        analyses: List[Dict[str, Any]],
        verifications: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Phase 4: Synthesize results

        Args:
            query: Original query
            papers: All papers
            analyses: Paper analyses
            verifications: Verification results

        Returns:
            Synthesis result with literature review
        """
        logger.info("[Phase 4] Synthesizing results")
        self._notify_progress("Generating literature review", {})

        synthesis_task = {
            'query': query,
            'papers': papers,
            'analyses': analyses,
            'verifications': verifications
        }

        result = await self.agents['synthesizer'].execute(synthesis_task)

        logger.info("[Phase 4] Synthesis complete")
        self._notify_progress("Synthesis complete", {})

        return result

    def route_message(self, from_agent: str, to_agent: str, content: Dict[str, Any]) -> None:
        """Route message between agents

        Args:
            from_agent: Sender agent name
            to_agent: Recipient agent name
            content: Message content
        """
        logger.debug(f"Message: {from_agent} -> {to_agent}")
        # For now, messages are logged. Can be extended for complex coordination.

    def on_agent_update(self, agent_name: str, status: str, data: Dict[str, Any]) -> None:
        """Handle agent status updates

        Args:
            agent_name: Agent name
            status: Status message
            data: Status data
        """
        logger.info(f"[{agent_name.upper()}] {status}")
        self._notify_progress(f"{agent_name}: {status}", data)

    def _notify_progress(self, message: str, data: Dict[str, Any]) -> None:
        """Notify progress via callback

        Args:
            message: Progress message
            data: Progress data
        """
        if self.progress_callback:
            self.progress_callback(message, data)

    def get_agent(self, agent_name: str):
        """Get agent by name

        Args:
            agent_name: Agent name

        Returns:
            Agent instance
        """
        return self.agents.get(agent_name)

    def clear_memory(self) -> None:
        """Clear all memory"""
        self.memory.clear()
        logger.info("Memory cleared")
