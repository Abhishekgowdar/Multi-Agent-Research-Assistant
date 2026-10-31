"""FastAPI backend for Web UI"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, PlainTextResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import asyncio
import json
from pathlib import Path

from src.orchestrator.master_orchestrator import MasterOrchestrator
from src.utils.export_utils import ExportUtils
from src.utils.history_manager import HistoryManager
from loguru import logger

# Initialize history manager
history_manager = HistoryManager()

app = FastAPI(title="Multi-Agent Research Assistant")

# Store active WebSocket connections
active_connections: List[WebSocket] = []


class ResearchRequest(BaseModel):
    """Research request model"""
    query: str
    max_papers: int = Field(default=20, ge=1, le=50)
    sources: List[str] = ["arxiv", "pubmed", "semantic_scholar"]


class ResearchResponse(BaseModel):
    """Research response model"""
    status: str
    query: str = ""
    papers_found: int = 0
    papers_analyzed: int = 0
    literature_review: str = ""
    must_read_papers: List[dict] = []
    metadata: dict = {}
    message: Optional[str] = None


# WebSocket progress callback
async def websocket_progress_callback(message: str, data: dict):
    """Send progress updates to all connected clients"""
    update = {
        "type": "progress",
        "message": message,
        "data": data
    }

    # Send to all connected clients
    for connection in active_connections:
        try:
            await connection.send_json(update)
        except:
            pass


@app.get("/")
async def root():
    """Serve the web UI"""
    html_path = Path(__file__).parent.parent.parent / "web" / "index.html"
    if html_path.exists():
        return FileResponse(html_path)
    return {"message": "Multi-Agent Research Assistant API"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/api/research", response_model=ResearchResponse)
async def research(request: ResearchRequest):
    """Execute research workflow (synchronous endpoint)"""
    logger.info(f"Research request: {request.query}")

    try:
        # Create orchestrator
        orchestrator = MasterOrchestrator()

        # Execute research
        result = await orchestrator.research(
            query=request.query,
            max_papers=request.max_papers,
            sources=request.sources
        )

        return ResearchResponse(**result)

    except Exception as e:
        logger.error(f"Research error: {e}")
        return ResearchResponse(
            status="error",
            query=request.query,
            papers_found=0,
            papers_analyzed=0,
            literature_review=f"Error: {str(e)}",
            must_read_papers=[],
            metadata={}
        )


# Browsers skip CORS for WebSockets, so the Origin header is checked here
ALLOWED_WS_ORIGINS = {"http://localhost:8000", "http://127.0.0.1:8000"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    if websocket.headers.get("origin") not in ALLOWED_WS_ORIGINS:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            if data.get("type") == "research":
                # Execute research with real-time updates
                query = data.get("query", "")
                try:
                    max_papers = min(max(int(data.get("max_papers") or 20), 1), 50)
                except (TypeError, ValueError):
                    max_papers = 20
                sources = data.get("sources", ["arxiv", "pubmed", "semantic_scholar"])

                logger.info(f"WebSocket research request: {query}")

                # Send start message
                await websocket.send_json({
                    "type": "start",
                    "message": "Research started",
                    "query": query
                })

                try:
                    # Create orchestrator with WebSocket callback
                    orchestrator = MasterOrchestrator(
                        progress_callback=lambda msg, data: asyncio.create_task(
                            websocket.send_json({
                                "type": "progress",
                                "message": msg,
                                "data": data
                            })
                        )
                    )

                    # Execute research
                    result = await orchestrator.research(
                        query=query,
                        max_papers=max_papers,
                        sources=sources
                    )

                    # Save to history if successful
                    if result.get('status') == 'success':
                        history_manager.add_search(query, result, sources)

                    # Send complete result
                    await websocket.send_json({
                        "type": "complete",
                        "result": result
                    })

                except Exception as e:
                    logger.error(f"WebSocket research error: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })

    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info("WebSocket disconnected")


@app.get("/api/history")
async def get_history(limit: int = 20):
    """Get research history

    Args:
        limit: Maximum number of entries to return

    Returns:
        History entries
    """
    history = history_manager.get_history(limit=limit)
    return {"history": history}


@app.get("/api/history/stats")
async def get_history_stats():
    """Get history statistics"""
    stats = history_manager.get_statistics()
    return stats


@app.delete("/api/history/{search_id}")
async def delete_history_entry(search_id: int):
    """Delete a history entry

    Args:
        search_id: ID of search to delete

    Returns:
        Success status
    """
    success = history_manager.delete_search(search_id)
    if success:
        return {"status": "success", "message": f"Deleted search {search_id}"}
    return {"status": "error", "message": f"Search {search_id} not found"}


@app.delete("/api/history")
async def clear_history():
    """Clear all history"""
    history_manager.clear_history()
    return {"status": "success", "message": "History cleared"}


@app.post("/api/export/markdown")
async def export_markdown(result: dict):
    """Export research result as Markdown

    Args:
        result: Research result dictionary

    Returns:
        Markdown content
    """
    markdown = ExportUtils.export_to_markdown(result)
    return PlainTextResponse(content=markdown, media_type="text/markdown")


@app.post("/api/export/html")
async def export_html(result: dict):
    """Export research result as HTML

    Args:
        result: Research result dictionary

    Returns:
        HTML content
    """
    html = ExportUtils.export_to_html(result)
    return HTMLResponse(content=html)


@app.post("/api/export/json")
async def export_json(result: dict):
    """Export research result as JSON

    Args:
        result: Research result dictionary

    Returns:
        JSON content
    """
    json_str = ExportUtils.export_to_json(result)
    return PlainTextResponse(content=json_str, media_type="application/json")


@app.post("/api/export/citations/{format}")
async def export_citations(format: str, papers: List[dict]):
    """Export citations in specified format

    Args:
        format: Citation format (bibtex, apa, mla, chicago)
        papers: List of papers to cite

    Returns:
        Formatted citations
    """
    citations = ExportUtils.generate_citations(papers, format=format)
    return PlainTextResponse(content=citations, media_type="text/plain")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
