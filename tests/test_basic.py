"""Basic tests for the research assistant"""

import pytest
from src.llm.gemini_client import GeminiClient
from src.memory.vector_memory import VectorMemory
from src.agents.searcher_agent import SearcherAgent
from src.integrations.arxiv_client import ArxivClient


def test_memory_basic():
    """Test basic memory operations"""
    memory = VectorMemory(collection_name="test_collection")

    # Store
    memory.store("test_id", {"content": "test data"}, {"type": "test"})

    # Retrieve
    result = memory.get("test_id")
    assert result is not None
    assert result['id'] == "test_id"

    # Clean up
    memory.clear()


def test_arxiv_search():
    """Test arXiv search"""
    client = ArxivClient(max_results=5)

    papers = client.search("machine learning", max_results=5)

    assert isinstance(papers, list)
    assert len(papers) <= 5

    if papers:
        paper = papers[0]
        assert 'title' in paper
        assert 'authors' in paper
        assert 'abstract' in paper
        assert paper['source'] == 'arxiv'


@pytest.mark.asyncio
async def test_searcher_agent():
    """Test searcher agent"""
    memory = VectorMemory(collection_name="test_searcher")
    agent = SearcherAgent(memory=memory)

    task = {
        'query': 'quantum computing',
        'max_papers': 10,
        'sources': ['arxiv'],
        'timeframe': 'recent'
    }

    result = await agent.execute(task)

    assert result['status'] == 'success'
    assert 'strategy' in result
    assert 'search_terms' in result

    # Clean up
    memory.clear()


def test_gemini_client():
    """Test Gemini client basic functionality"""
    try:
        client = GeminiClient()

        response = client.generate("Say 'Hello, World!' and nothing else.", temperature=0.1)

        assert isinstance(response, str)
        assert len(response) > 0

    except Exception as e:
        pytest.skip(f"Gemini API not configured: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
