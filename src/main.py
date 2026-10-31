"""Main CLI entry point"""

import asyncio
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.markdown import Markdown
from loguru import logger

from src.orchestrator.master_orchestrator import MasterOrchestrator
from src.utils.config import settings

# Configure logger
logger.remove()
logger.add(sys.stderr, level=settings.get('LOG_LEVEL', 'INFO'))

# Rich console
console = Console()


def progress_callback(message: str, data: dict):
    """Callback for progress updates"""
    console.print(f"[cyan]►[/cyan] {message}", style="dim")


@click.command()
@click.argument('query')
@click.option(
    '--max-papers',
    default=20,
    help='Maximum number of papers to analyze'
)
@click.option(
    '--sources',
    default='arxiv,pubmed,semantic_scholar',
    help='Comma-separated list of data sources'
)
@click.option(
    '--output',
    type=click.Path(),
    help='Output file path (markdown)'
)
@click.option(
    '--verbose',
    is_flag=True,
    help='Verbose output'
)
def main(query: str, max_papers: int, sources: str, output: str, verbose: bool):
    """Multi-Agent Research Assistant

    Analyzes academic papers and generates comprehensive literature reviews.

    Example:

        python -m src.main "quantum computing for drug discovery"

        python -m src.main "machine learning in healthcare" --max-papers 30 --output review.md
    """
    # Set log level
    if verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")

    # Parse sources
    source_list = [s.strip() for s in sources.split(',')]

    # Display header
    console.print()

    # Determine which AI provider is being used
    provider_text = "Google Gemini" if settings.llm_provider == "gemini" else "Groq (Llama 3.1)"

    console.print(Panel.fit(
        f"[bold cyan]🤖 Multi-Agent Research Assistant[/bold cyan]\n"
        f"[dim]Powered by {provider_text} (FREE)[/dim]",
        border_style="cyan"
    ))
    console.print()

    # Display query info
    console.print(f"[bold]Research Query:[/bold] {query}")
    console.print(f"[bold]Max Papers:[/bold] {max_papers}")
    console.print(f"[bold]Data Sources:[/bold] {', '.join(source_list)}")
    console.print()

    # Run research
    try:
        result = asyncio.run(run_research(query, max_papers, source_list))

        if result['status'] == 'success':
            # Display results
            display_results(result)

            # Save to file if requested
            if output:
                save_results(result, output)
                console.print(f"\n[green]✓[/green] Results saved to: {output}")

        else:
            console.print(f"[red]✗[/red] Research failed: {result.get('message', 'Unknown error')}")
            sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Research interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]✗ Error:[/red] {str(e)}")
        logger.exception("Fatal error")
        sys.exit(1)


async def run_research(query: str, max_papers: int, sources: list) -> dict:
    """Run research workflow

    Args:
        query: Research query
        max_papers: Maximum papers
        sources: Data sources

    Returns:
        Research results
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:

        task = progress.add_task("[cyan]Initializing...", total=None)

        # Initialize orchestrator
        orchestrator = MasterOrchestrator(progress_callback=progress_callback)

        # Update progress
        progress.update(task, description="[cyan]Searching for papers...")

        # Execute research
        result = await orchestrator.research(
            query=query,
            max_papers=max_papers,
            sources=sources
        )

        progress.update(task, description="[green]✓ Complete!")

    return result


def display_results(result: dict):
    """Display research results

    Args:
        result: Research results dictionary
    """
    console.print("\n" + "="*80 + "\n")

    # Display literature review
    review = result.get('literature_review', '')
    if review:
        md = Markdown(review)
        console.print(md)
    else:
        console.print("[yellow]No literature review generated[/yellow]")

    console.print("\n" + "="*80 + "\n")

    # Display summary
    console.print(Panel(
        f"[bold]Papers Found:[/bold] {result.get('papers_found', 0)}\n"
        f"[bold]Papers Analyzed:[/bold] {result.get('papers_analyzed', 0)}\n"
        f"[bold]Confidence:[/bold] {result.get('metadata', {}).get('average_confidence', 0):.2%}",
        title="[bold cyan]Research Summary[/bold cyan]",
        border_style="cyan"
    ))

    # Display must-read papers
    must_read = result.get('must_read_papers', [])
    if must_read:
        console.print("\n[bold cyan]📚 Must-Read Papers (Top 5):[/bold cyan]\n")
        for i, paper in enumerate(must_read[:5], 1):
            console.print(f"{i}. [bold]{paper.get('title', 'Unknown')}[/bold]")
            console.print(f"   {', '.join(paper.get('authors', [])[:3])} ({paper.get('year', '')})")
            console.print(f"   [dim]{paper.get('url', '')}[/dim]")
            console.print()


def save_results(result: dict, output_path: str):
    """Save results to file

    Args:
        result: Research results
        output_path: Output file path
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    content = f"""# Research Results

**Query:** {result.get('query', '')}

**Papers Found:** {result.get('papers_found', 0)}

**Papers Analyzed:** {result.get('papers_analyzed', 0)}

**Confidence:** {result.get('metadata', {}).get('average_confidence', 0):.2%}

---

{result.get('literature_review', '')}

---

## Must-Read Papers

"""

    for i, paper in enumerate(result.get('must_read_papers', []), 1):
        content += f"{i}. **{paper.get('title', 'Unknown')}**\n"
        content += f"   {', '.join(paper.get('authors', [])[:3])} ({paper.get('year', '')})\n"
        content += f"   {paper.get('url', '')}\n\n"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)


if __name__ == '__main__':
    main()
