"""Fact-Checker Agent - Verifies claims and assesses credibility"""

from typing import Dict, List, Any
from pathlib import Path
from loguru import logger

from src.agents.base_agent import BaseAgent


class FactCheckerAgent(BaseAgent):
    """Agent responsible for verifying claims and assessing credibility"""

    def __init__(self, memory=None, orchestrator=None):
        super().__init__("fact_checker", memory, orchestrator)
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """Load the fact-checker prompt template"""
        prompt_path = Path(__file__).parent.parent.parent / "prompts" / "fact_checker_prompt.txt"
        if prompt_path.exists():
            return prompt_path.read_text(encoding='utf-8')
        return ""

    def get_role_description(self) -> str:
        return "Verify claims, cross-reference findings, and assess paper credibility"

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute fact-checking task

        Args:
            task: Dictionary containing:
                - analyses: List of paper analyses to verify
                - papers: Original paper data

        Returns:
            Dictionary with verification results
        """
        analyses = task.get('analyses', [])
        papers = task.get('papers', [])

        if not analyses:
            logger.warning("[Fact-Checker] No analyses to verify")
            return {"status": "no_analyses", "verifications": []}

        self.notify(f"Verifying {len(analyses)} analyses", {"count": len(analyses)})

        verifications = []

        for i, analysis in enumerate(analyses, 1):
            logger.info(f"[Fact-Checker] Verifying {i}/{len(analyses)}")

            # Get related analyses for cross-reference
            related_analyses = self._get_related_analyses(analysis, analyses)

            try:
                verification = await self.verify_analysis(analysis, related_analyses)
            except Exception as e:
                logger.error(f"[Fact-Checker] Verification failed, using minimal result: {e}")
                verification = self._minimal_verification(analysis)

            if verification:
                verifications.append(verification)
                self.remember(f"verification:{analysis.get('paper_id', i)}", verification)

            self.notify(f"Verified {i}/{len(analyses)} analyses", {
                "progress": f"{i}/{len(analyses)}"
            })

        # Calculate overall credibility
        avg_confidence = sum(v.get('confidence', 0.5) for v in verifications) / len(verifications) if verifications else 0.5

        logger.info(f"[Fact-Checker] Completed verification. Average confidence: {avg_confidence:.2f}")

        return {
            "status": "success",
            "verifications": verifications,
            "average_confidence": avg_confidence,
            "total_verified": len(verifications)
        }

    @staticmethod
    def _concepts(analysis: Dict[str, Any]) -> set:
        """Normalized concept set used for cross-referencing"""
        return {str(c).strip().lower() for c in (analysis.get('related_concepts') or []) if str(c).strip()}

    def _get_related_analyses(
        self,
        target_analysis: Dict[str, Any],
        all_analyses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find analyses related to target for cross-referencing

        Args:
            target_analysis: Analysis to find related papers for
            all_analyses: All available analyses

        Returns:
            List of related analyses
        """
        # Match concepts case-insensitively so "AI" and "ai " overlap
        target_concepts = self._concepts(target_analysis)

        related = []
        for analysis in all_analyses:
            same_paper = analysis is target_analysis or (
                analysis.get('paper_id') and analysis.get('paper_id') == target_analysis.get('paper_id')
            )
            if same_paper:
                continue

            concepts = self._concepts(analysis)
            overlap = len(target_concepts & concepts)

            if overlap > 0:
                related.append(analysis)

        return related[:5]  # Return top 5 related

    async def verify_analysis(
        self,
        analysis: Dict[str, Any],
        related_analyses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Verify a single analysis

        Args:
            analysis: Analysis to verify
            related_analyses: Related analyses for cross-reference

        Returns:
            Verification result
        """
        # Build context from related papers
        related_context = "\n".join([
            f"- Paper: {a.get('title', '')} ({a.get('year', '')})"
            f"\n  Findings: {', '.join(a.get('key_findings', [])[:2])}"
            for a in related_analyses[:3]
        ])

        # Get first key finding to verify
        key_findings = analysis.get('key_findings', [])
        if not key_findings:
            logger.debug("[Fact-Checker] No findings to verify")
            return self._minimal_verification(analysis)

        claim = key_findings[0] if key_findings else "No specific claim"

        # Build verification prompt
        prompt = self.prompt_template.format(
            claim=claim,
            paper_title=analysis.get('title', ''),
            authors=", ".join(str(a) for a in (analysis.get('authors') or [])[:3]),
            year=analysis.get('year', ''),
            citations=analysis.get('citations', 0),
            related_papers=related_context or "No related papers found"
        )

        # Get verification from LLM (800 tokens for complete JSON)
        verification = await self._ask_json(prompt, temperature=0.3, max_tokens=800)

        if not verification:
            logger.warning(f"[Fact-Checker] Failed to verify: {analysis.get('title', '')[:50]}")
            return self._minimal_verification(analysis)

        # Add paper reference
        verification['paper_id'] = analysis.get('paper_id', '')
        verification['paper_title'] = analysis.get('title', '')

        return verification

    def _minimal_verification(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create minimal verification when LLM fails

        Args:
            analysis: Analysis data

        Returns:
            Minimal verification
        """
        return {
            "paper_id": analysis.get('paper_id', ''),
            "paper_title": analysis.get('title', ''),
            "verification_status": "uncertain",
            "confidence": 0.5,
            "credibility_assessment": {
                "author_reputation": "unknown",
                "citation_quality": 0.5,
                "methodology_soundness": "acceptable"
            },
            "recommendation": "caution"
        }

    def assess_credibility(self, papers: List[Dict[str, Any]]) -> Dict[str, float]:
        """Assess overall credibility of paper collection

        Args:
            papers: List of papers

        Returns:
            Dictionary mapping paper IDs to credibility scores
        """
        credibility_scores = {}

        for paper in papers:
            score = 0.5  # Base score

            # Citation count factor
            citations = paper.get('citations', 0)
            if citations > 100:
                score += 0.2
            elif citations > 50:
                score += 0.1

            # Recency factor
            year = paper.get('year', 2000)
            if year >= 2023:
                score += 0.2
            elif year >= 2020:
                score += 0.1

            # Venue/journal factor (if available)
            venue = paper.get('venue', '').lower()
            prestigious_venues = ['nature', 'science', 'cell', 'pnas', 'lancet']
            if any(v in venue for v in prestigious_venues):
                score += 0.1

            credibility_scores[paper.get('id', '')] = min(score, 1.0)

        return credibility_scores
