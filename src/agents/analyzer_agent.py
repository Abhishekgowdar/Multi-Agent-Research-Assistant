"""Analyzer Agent - Deep analysis of research papers"""

from typing import Dict, List, Any
from pathlib import Path
from loguru import logger

from src.agents.base_agent import BaseAgent


class AnalyzerAgent(BaseAgent):
    """Agent responsible for deep analysis of research papers"""

    def __init__(self, memory=None, orchestrator=None):
        super().__init__("analyzer", memory, orchestrator)
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """Load the analyzer prompt template"""
        prompt_path = Path(__file__).parent.parent.parent / "prompts" / "analyzer_prompt.txt"
        if prompt_path.exists():
            return prompt_path.read_text(encoding='utf-8')
        return ""

    def get_role_description(self) -> str:
        return "Deep-read papers and extract key findings, methods, and insights"

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analysis task

        Args:
            task: Dictionary containing:
                - papers: List of papers to analyze
                - query: Original research query

        Returns:
            Dictionary with analysis results
        """
        papers = task.get('papers', [])
        query = task.get('query', '')

        if not papers:
            logger.warning("[Analyzer] No papers to analyze")
            return {"status": "no_papers", "analyses": []}

        self.notify(f"Analyzing {len(papers)} papers", {"count": len(papers)})

        analyses = []

        for i, paper in enumerate(papers, 1):
            logger.info(f"[Analyzer] Analyzing paper {i}/{len(papers)}: {paper.get('title', 'Unknown')[:50]}...")

            try:
                analysis = await self.analyze_paper(paper, query)
            except Exception as e:
                logger.error(f"[Analyzer] Skipping paper after error: {e}")
                analysis = None

            if analysis:
                analyses.append(analysis)
                # Store in memory
                self.remember(f"analysis:{paper.get('id', i)}", analysis)

            self.notify(f"Analyzed {i}/{len(papers)} papers", {
                "progress": f"{i}/{len(papers)}"
            })

        logger.info(f"[Analyzer] Completed analysis of {len(analyses)} papers")

        return {
            "status": "success",
            "analyses": analyses,
            "total_analyzed": len(analyses)
        }

    async def analyze_paper(self, paper: Dict[str, Any], query: str = '') -> Dict[str, Any]:
        """Analyze a single paper against the research question

        Args:
            paper: Paper dictionary with metadata
            query: Research question the paper is judged against

        Returns:
            Analysis dictionary
        """
        abstract = (paper.get('abstract') or '').strip()
        if not abstract:
            # Without an abstract the model would have to invent findings
            logger.info(f"[Analyzer] No abstract, skipping LLM analysis: {(paper.get('title') or '')[:50]}")
            return self._fallback_analysis(paper)

        # Build prompt with paper details
        prompt = self.prompt_template.format(
            query=query,
            paper_id=paper.get('id', ''),
            title=paper.get('title') or '',
            authors=", ".join(str(a) for a in (paper.get('authors') or [])[:5]),
            year=paper.get('year') or '',
            abstract=abstract,
            citations=paper.get('citations') or 0
        )

        # Get analysis from LLM (800 tokens for complete JSON)
        analysis = await self._ask_json(prompt, temperature=0.4, max_tokens=800)

        if not analysis:
            logger.warning(f"[Analyzer] Failed to analyze paper: {(paper.get('title') or '')[:50]}")
            return self._fallback_analysis(paper)

        analysis.update(self._paper_fields(paper))
        return analysis

    @staticmethod
    def _paper_fields(paper: Dict[str, Any]) -> Dict[str, Any]:
        """Metadata carried from the source record into every analysis"""
        return {
            'paper_id': paper.get('id', ''),
            'title': paper.get('title') or '',
            'year': paper.get('year') or '',
            'authors': paper.get('authors') or [],
            'url': paper.get('url') or '',
            'citations': paper.get('citations') or 0,
            'venue': paper.get('venue') or paper.get('journal') or '',
            'doi': paper.get('doi') or '',
        }

    def _fallback_analysis(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """Minimal analysis used when the model fails or the abstract is missing"""
        abstract = (paper.get('abstract') or '').strip()
        return {
            **self._paper_fields(paper),
            'summary': abstract[:200] if abstract else 'No abstract available; findings were not extracted.',
            'key_findings': [],
            'quality_score': 0.5,
            'relevance_score': 0.5,
            'abstract_missing': not abstract,
        }

    def identify_trends(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify trends across multiple paper analyses

        Args:
            analyses: List of paper analyses

        Returns:
            Dictionary of identified trends
        """
        logger.info(f"[Analyzer] Identifying trends across {len(analyses)} analyses")

        # Prepare summary for LLM
        summary = "Analyze these paper summaries and identify trends:\n\n"
        for i, analysis in enumerate(analyses[:15], 1):  # Limit to 15 for context
            summary += f"{i}. {analysis.get('title', 'Unknown')} ({analysis.get('year', '')})\n"
            summary += f"   Key findings: {', '.join(analysis.get('key_findings', [])[:2])}\n\n"

        prompt = f"""{summary}

Based on these papers, identify:
1. Common methodologies
2. Emerging trends
3. Popular research directions
4. Evolution of ideas over time

Provide your analysis in JSON format:
{{
  "common_methodologies": ["method1", "method2"],
  "emerging_trends": ["trend1", "trend2"],
  "popular_topics": ["topic1", "topic2"],
  "temporal_evolution": "How the field has evolved"
}}
"""

        trends = self.think_json(prompt, temperature=0.5)

        if not trends:
            return {
                "common_methodologies": [],
                "emerging_trends": [],
                "popular_topics": []
            }

        return trends
