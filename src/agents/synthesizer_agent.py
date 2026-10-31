"""Synthesizer Agent - Creates comprehensive literature reviews"""

from typing import Dict, List, Any
from pathlib import Path
from loguru import logger

from src.agents.base_agent import BaseAgent

REVIEW_MAX_TOKENS = 2000  # Room for nine sections plus the must-read list


class SynthesizerAgent(BaseAgent):
    """Agent responsible for synthesizing findings into literature reviews"""

    def __init__(self, memory=None, orchestrator=None):
        super().__init__("synthesizer", memory, orchestrator)
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """Load the synthesizer prompt template"""
        prompt_path = Path(__file__).parent.parent.parent / "prompts" / "synthesizer_prompt.txt"
        if prompt_path.exists():
            return prompt_path.read_text(encoding='utf-8')
        return ""

    def get_role_description(self) -> str:
        return "Synthesize findings into comprehensive literature reviews"

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute synthesis task

        Args:
            task: Dictionary containing:
                - query: Original research query
                - analyses: List of paper analyses
                - verifications: Verification results
                - papers: Original paper data

        Returns:
            Dictionary with literature review
        """
        query = task.get('query', '')
        analyses = task.get('analyses', [])
        verifications = task.get('verifications', [])
        papers = task.get('papers', [])

        if not analyses:
            logger.warning("[Synthesizer] No analyses to synthesize")
            return {"status": "no_analyses", "review": ""}

        self.notify("Generating literature review", {"query": query})

        logger.info(f"[Synthesizer] Synthesizing {len(analyses)} analyses")

        # Prepare data for synthesis
        analyzed_papers_summary = self._format_analyses(analyses)
        verifications_summary = self._format_verifications(verifications)

        # Build synthesis prompt
        prompt = self.prompt_template.format(
            query=query,
            topic=self._extract_topic(query),
            analyzed_papers=analyzed_papers_summary,
            verifications=verifications_summary
        )

        logger.info("[Synthesizer] Generating comprehensive review...")
        review = await self._ask_text(prompt, temperature=0.6, max_tokens=REVIEW_MAX_TOKENS)

        if not review:
            logger.error("[Synthesizer] Failed to generate review")
            return {"status": "error", "review": ""}

        truncated = bool(getattr(self.llm, 'last_truncated', False))
        if truncated:
            review += "\n\n> Note: the model's output limit cut this review short."
        review += "\n\n## 🔗 References\n\n" + self._build_references(analyses)

        # Store in memory
        self.remember("last_review", review)

        # Extract must-read papers
        must_read = self._select_must_read_papers(analyses, verifications)

        logger.info(f"[Synthesizer] Review generated ({len(review)} characters)")

        result = {
            "status": "success",
            "review": review,
            "must_read_papers": must_read,
            "total_papers_reviewed": len(analyses),
            "truncated": truncated,
            "average_confidence": self._calculate_avg_confidence(verifications),
            "metadata": {
                "query": query,
                "paper_count": len(papers),
                "analysis_count": len(analyses)
            }
        }

        self.notify("Literature review complete", {
            "review_length": len(review),
            "papers_reviewed": len(analyses)
        })

        return result

    @staticmethod
    def _build_references(analyses: List[Dict[str, Any]]) -> str:
        """Reference list built from source metadata, so the model cannot invent citations"""
        lines = []
        for number, analysis in enumerate(analyses, 1):
            authors = ", ".join(str(a) for a in (analysis.get('authors') or [])[:3]) or "Unknown authors"
            year = analysis.get('year') or "n.d."
            venue = f" {analysis['venue']}." if analysis.get('venue') else ""
            link = f"https://doi.org/{analysis['doi']}" if analysis.get('doi') else (analysis.get('url') or "")
            lines.append(f"{number}. {authors} ({year}). {analysis.get('title') or 'Untitled'}.{venue} {link}".rstrip())
        return "\n".join(lines)

    def _format_analyses(self, analyses: List[Dict[str, Any]]) -> str:
        """Format analyses for the prompt

        Args:
            analyses: List of analyses

        Returns:
            Formatted string
        """
        formatted = []

        for i, analysis in enumerate(analyses, 1):
            paper_text = f"""
Paper {i}: {analysis.get('title', 'Unknown')} ({analysis.get('year', '')})
Authors: {', '.join(analysis.get('authors', [])[:3])}
Summary: {analysis.get('summary', '')}
Key Findings:
{chr(10).join(f'- {finding}' for finding in analysis.get('key_findings', [])[:3])}
Methodology: {analysis.get('methodology', 'Not specified')}
Limitations: {', '.join(analysis.get('limitations', [])[:2])}
Quality Score: {analysis.get('quality_score', 0):.2f}
"""
            formatted.append(paper_text.strip())

        return "\n\n".join(formatted)

    def _format_verifications(self, verifications: List[Dict[str, Any]]) -> str:
        """Format verifications for the prompt

        Args:
            verifications: List of verifications

        Returns:
            Formatted string
        """
        if not verifications:
            return "No verifications available"

        formatted = []

        for v in verifications:
            status = v.get('verification_status', 'uncertain')
            confidence = v.get('confidence', 0.5)
            recommendation = v.get('recommendation', 'caution')

            text = f"- {v.get('paper_title', 'Unknown')}: {status} (confidence: {confidence:.2f}, {recommendation})"
            formatted.append(text)

        return "\n".join(formatted)

    def _extract_topic(self, query: str) -> str:
        """Extract clean topic from query

        Args:
            query: Research query

        Returns:
            Clean topic string
        """
        # Simple extraction - can be enhanced
        topic = query.replace("latest advances in", "").replace("recent progress in", "")
        topic = topic.replace("what are", "").replace("how do", "").strip()
        return topic.title()

    def _select_must_read_papers(
        self,
        analyses: List[Dict[str, Any]],
        verifications: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Select must-read papers based on quality and relevance

        Args:
            analyses: List of analyses
            verifications: List of verifications

        Returns:
            List of must-read papers
        """
        # Create verification lookup
        verification_map = {
            v.get('paper_id'): v.get('confidence', 0.5)
            for v in verifications
        }

        # Score each paper
        scored_papers = []
        for analysis in analyses:
            paper_id = analysis.get('paper_id', '')

            # Base scores
            quality = analysis.get('quality_score', 0.5)
            relevance = analysis.get('relevance_score', 0.5)
            verification = verification_map.get(paper_id, 0.5)

            # Combined score
            total_score = (quality * 0.4) + (relevance * 0.4) + (verification * 0.2)

            scored_papers.append({
                "paper_id": paper_id,
                "title": analysis.get('title', ''),
                "authors": analysis.get('authors', []),
                "year": analysis.get('year', ''),
                "url": analysis.get('url', ''),
                "score": total_score,
                "summary": analysis.get('summary', ''),
                "key_takeaway": analysis.get('key_findings', [''])[0] if analysis.get('key_findings') else ''
            })

        # Sort by score and return top papers
        scored_papers.sort(key=lambda p: p['score'], reverse=True)

        return scored_papers[:10]  # Top 10 must-read papers

    def _calculate_avg_confidence(self, verifications: List[Dict[str, Any]]) -> float:
        """Calculate average confidence from verifications

        Args:
            verifications: List of verifications

        Returns:
            Average confidence score
        """
        if not verifications:
            return 0.5

        confidences = [v.get('confidence', 0.5) for v in verifications]
        return sum(confidences) / len(confidences)

    def identify_research_gaps(self, analyses: List[Dict[str, Any]]) -> List[str]:
        """Identify research gaps from analyses

        Args:
            analyses: List of paper analyses

        Returns:
            List of identified research gaps
        """
        logger.info("[Synthesizer] Identifying research gaps")

        # Collect all limitations and future work
        limitations = []
        future_work = []

        for analysis in analyses:
            limitations.extend(analysis.get('limitations', []))
            if 'future_work' in analysis:
                future_work.append(analysis['future_work'])

        # Use LLM to synthesize gaps
        prompt = f"""
Based on these limitations and future work suggestions from multiple research papers:

LIMITATIONS:
{chr(10).join(f'- {lim}' for lim in limitations[:10])}

FUTURE WORK MENTIONED:
{chr(10).join(f'- {fw}' for fw in future_work[:5])}

Identify 3-5 significant research gaps in this field. Provide as JSON:
{{
  "gaps": [
    "Gap 1: Description",
    "Gap 2: Description"
  ]
}}
"""

        result = self.think_json(prompt, temperature=0.5)

        return result.get('gaps', []) if result else []
