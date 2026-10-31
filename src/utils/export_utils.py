"""Export utilities for research results"""

from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path
import json
import html as html_mod


def _h(text) -> str:
    """Escape text for safe HTML embedding"""
    return html_mod.escape(str(text)) if text is not None else ''


def _safe_href(url) -> str:
    """Escaped URL when it uses http or https, otherwise a placeholder"""
    text = str(url or '')
    return _h(text) if text.lower().startswith(('http://', 'https://')) else '#'


class ExportUtils:
    """Utility class for exporting research results"""

    @staticmethod
    def export_to_markdown(result: Dict[str, Any], output_path: str = None) -> str:
        """Export research results to Markdown format

        Args:
            result: Research result dictionary
            output_path: Optional path to save file

        Returns:
            Markdown formatted string
        """
        query = result.get('query', 'Research')
        papers_found = result.get('papers_found', 0)
        papers_analyzed = result.get('papers_analyzed', 0)
        confidence = result.get('metadata', {}).get('average_confidence', 0)
        review = result.get('literature_review', '')
        papers = result.get('must_read_papers', [])

        # Build markdown
        md = f"""# Research Report: {query}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary Statistics

- **Papers Found:** {papers_found}
- **Papers Analyzed:** {papers_analyzed}
- **Confidence Level:** {int(confidence * 100)}%
- **Data Sources:** {', '.join(result.get('metadata', {}).get('sources_searched', []))}

---

## Literature Review

{review}

---

## Must-Read Papers

"""

        # Add papers
        for i, paper in enumerate(papers, 1):
            md += f"""
### {i}. {paper.get('title', 'Unknown')}

**Authors:** {', '.join(paper.get('authors', ['Unknown']))}
**Year:** {paper.get('year', 'N/A')}
**DOI:** {paper.get('doi', 'N/A')}
**Citations:** {paper.get('citations', 'N/A')}
**Venue:** {paper.get('venue', 'N/A')}

**URL:** [{paper.get('url', '#')}]({paper.get('url', '#')})

**Summary:** {paper.get('summary', 'No summary available')}

---
"""

        # Save if path provided
        if output_path:
            Path(output_path).write_text(md, encoding='utf-8')

        return md

    @staticmethod
    def export_to_html(result: Dict[str, Any], output_path: str = None) -> str:
        """Export research results to HTML format

        Args:
            result: Research result dictionary
            output_path: Optional path to save file

        Returns:
            HTML formatted string
        """
        query = _h(result.get('query', 'Research'))
        papers_found = result.get('papers_found', 0)
        papers_analyzed = result.get('papers_analyzed', 0)
        confidence = result.get('metadata', {}).get('average_confidence', 0)
        review = _h(result.get('literature_review', '')).replace('\n', '<br>')
        papers = result.get('must_read_papers', [])

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Research Report: {query}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 40px;
            line-height: 1.6;
        }}
        h1 {{ color: #2563eb; }}
        h2 {{ color: #1d4ed8; border-bottom: 2px solid #2563eb; padding-bottom: 10px; }}
        h3 {{ color: #3b82f6; }}
        .stats {{
            background: #f0f9ff;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .paper {{
            border: 1px solid #e5e7eb;
            padding: 20px;
            margin: 15px 0;
            border-radius: 8px;
            background: #f9fafb;
        }}
        .paper-title {{ font-weight: bold; font-size: 1.1em; }}
        .metadata {{ color: #6b7280; font-size: 0.9em; }}
        a {{ color: #2563eb; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>Research Report: {query}</h1>
    <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

    <div class="stats">
        <h2>Summary Statistics</h2>
        <ul>
            <li><strong>Papers Found:</strong> {papers_found}</li>
            <li><strong>Papers Analyzed:</strong> {papers_analyzed}</li>
            <li><strong>Confidence Level:</strong> {int(confidence * 100)}%</li>
            <li><strong>Data Sources:</strong> {_h(', '.join(result.get('metadata', {}).get('sources_searched', [])))}</li>
        </ul>
    </div>

    <h2>Literature Review</h2>
    <div>{review}</div>

    <h2>Must-Read Papers</h2>
"""

        # Add papers
        for i, paper in enumerate(papers, 1):
            html += f"""
    <div class="paper">
        <div class="paper-title">{i}. {_h(paper.get('title', 'Unknown'))}</div>
        <div class="metadata">
            <strong>Authors:</strong> {_h(', '.join(paper.get('authors', ['Unknown'])))}<br>
            <strong>Year:</strong> {_h(paper.get('year', 'N/A'))} |
            <strong>Citations:</strong> {_h(paper.get('citations', 'N/A'))} |
            <strong>Venue:</strong> {_h(paper.get('venue', 'N/A'))}<br>
            <strong>DOI:</strong> {_h(paper.get('doi', 'N/A'))}<br>
            <strong>URL:</strong> <a href="{_safe_href(paper.get('url', '#'))}">{_h(paper.get('url', 'N/A'))}</a>
        </div>
        <p><strong>Summary:</strong> {_h(paper.get('summary', 'No summary available'))}</p>
    </div>
"""

        html += """
</body>
</html>
"""

        # Save if path provided
        if output_path:
            Path(output_path).write_text(html, encoding='utf-8')

        return html

    @staticmethod
    def export_to_json(result: Dict[str, Any], output_path: str = None) -> str:
        """Export research results to JSON format

        Args:
            result: Research result dictionary
            output_path: Optional path to save file

        Returns:
            JSON formatted string
        """
        # Add timestamp
        export_data = {
            'exported_at': datetime.now().isoformat(),
            'research_result': result
        }

        json_str = json.dumps(export_data, indent=2, ensure_ascii=False)

        # Save if path provided
        if output_path:
            Path(output_path).write_text(json_str, encoding='utf-8')

        return json_str

    @staticmethod
    def generate_citations(papers: List[Dict[str, Any]], format: str = 'bibtex') -> str:
        """Generate citations in various formats

        Args:
            papers: List of paper dictionaries
            format: Citation format ('bibtex', 'apa', 'mla', 'chicago')

        Returns:
            Formatted citations string
        """
        if format.lower() == 'bibtex':
            return ExportUtils._generate_bibtex(papers)
        elif format.lower() == 'apa':
            return ExportUtils._generate_apa(papers)
        elif format.lower() == 'mla':
            return ExportUtils._generate_mla(papers)
        elif format.lower() == 'chicago':
            return ExportUtils._generate_chicago(papers)
        else:
            return "Unsupported citation format"

    @staticmethod
    def _generate_bibtex(papers: List[Dict[str, Any]]) -> str:
        """Generate BibTeX citations"""
        citations = []

        for i, paper in enumerate(papers, 1):
            # Create citation key
            first_author = paper.get('authors', ['Unknown'])[0].split()[-1] if paper.get('authors') else 'Unknown'
            year = paper.get('year', 'n.d.')
            key = f"{first_author}{year}"

            bibtex = f"""@article{{{key},
  title = {{{paper.get('title', 'Unknown')}}},
  author = {{{' and '.join(paper.get('authors', ['Unknown']))}}},
  year = {{{year}}},
  doi = {{{paper.get('doi', '')}}},
  url = {{{paper.get('url', '')}}},
  journal = {{{paper.get('venue', '')}}},
  abstract = {{{paper.get('abstract', '')[:200]}...}}
}}"""
            citations.append(bibtex)

        return '\n\n'.join(citations)

    @staticmethod
    def _generate_apa(papers: List[Dict[str, Any]]) -> str:
        """Generate APA format citations"""
        citations = []

        for paper in papers:
            authors = paper.get('authors', ['Unknown'])
            if len(authors) == 1:
                author_str = authors[0]
            elif len(authors) == 2:
                author_str = f"{authors[0]} & {authors[1]}"
            else:
                author_str = f"{authors[0]} et al."

            year = paper.get('year', 'n.d.')
            title = paper.get('title', 'Unknown')
            venue = paper.get('venue', '')
            doi = paper.get('doi', '')

            citation = f"{author_str} ({year}). {title}."
            if venue:
                citation += f" {venue}."
            if doi:
                citation += f" https://doi.org/{doi}"

            citations.append(citation)

        return '\n\n'.join(citations)

    @staticmethod
    def _generate_mla(papers: List[Dict[str, Any]]) -> str:
        """Generate MLA format citations"""
        citations = []

        for paper in papers:
            authors = paper.get('authors', ['Unknown'])
            if authors:
                author_str = f"{authors[0]}."
                if len(authors) > 1:
                    author_str += " et al."
            else:
                author_str = "Unknown."

            title = paper.get('title', 'Unknown')
            venue = paper.get('venue', '')
            year = paper.get('year', 'n.d.')
            url = paper.get('url', '')

            citation = f'{author_str} "{title}."'
            if venue:
                citation += f" {venue},"
            citation += f" {year}."
            if url:
                citation += f" {url}."

            citations.append(citation)

        return '\n\n'.join(citations)

    @staticmethod
    def _generate_chicago(papers: List[Dict[str, Any]]) -> str:
        """Generate Chicago format citations"""
        citations = []

        for paper in papers:
            authors = paper.get('authors', ['Unknown'])
            if authors:
                author_str = authors[0]
                if len(authors) > 1:
                    author_str += " et al."
            else:
                author_str = "Unknown"

            year = paper.get('year', 'n.d.')
            title = paper.get('title', 'Unknown')
            venue = paper.get('venue', '')
            doi = paper.get('doi', '')

            citation = f'{author_str}. {year}. "{title}."'
            if venue:
                citation += f" {venue}."
            if doi:
                citation += f" https://doi.org/{doi}."

            citations.append(citation)

        return '\n\n'.join(citations)
