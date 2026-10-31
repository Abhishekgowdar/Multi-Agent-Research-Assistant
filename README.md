# Multi-Agent AI Research Assistant

An intelligent research tool that uses **4 specialized AI agents** to search academic papers across **9 databases**, analyze findings, verify claims, and generate comprehensive literature reviews — completely **FREE** to run.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- **4 AI Agents** working collaboratively (Searcher, Analyzer, Fact-Checker, Synthesizer)
- **9 Academic Databases** — Google Scholar, IEEE Xplore, arXiv, PubMed, Semantic Scholar, CORE, CrossRef, bioRxiv, PLOS ONE
- **Vector Memory** — ChromaDB for semantic search and context retention across sessions
- **Real-time Progress** — WebSocket-powered live updates in the browser
- **Export** — Download results as Markdown, HTML, or JSON
- **Citation Generator** — BibTeX, APA, MLA, and Chicago formats
- **Search History** — Auto-saved with statistics dashboard
- **Web UI** — Modern responsive dark theme
- **100% FREE** — Runs on Groq free tier, 7 of 9 data sources need no API key

## Architecture

```
User Query
    |
    v
+-------------------------------+
|      Master Orchestrator      |
|   (Coordinates all agents)    |
+------+--------+-------+------+
       |        |       |      |
       v        v       v      v
  Searcher  Analyzer  Fact-   Synthe-
   Agent     Agent   Checker  sizer
       |                        |
       v                        v
  9 Data Sources         Literature Review
```

**4-Phase Workflow:**

| Phase | Agent | Action |
|-------|-------|--------|
| 1. Search | Searcher | Generates search strategy, queries databases, ranks papers |
| 2. Analyze | Analyzer | Extracts findings, methodology, contributions, limitations |
| 3. Verify | Fact-Checker | Assesses credibility, assigns confidence scores |
| 4. Synthesize | Synthesizer | Generates structured literature review |

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python, FastAPI |
| AI / LLM | Groq API (Qwen 3.8-27B) |
| Vector DB | ChromaDB |
| Frontend | HTML, CSS, JavaScript, WebSockets |
| Data Sources | Google Scholar, IEEE, arXiv, PubMed, Semantic Scholar, CORE, CrossRef, bioRxiv, PLOS ONE |

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/Abhishekgowdar/multi-agent-research-assistant.git
cd multi-agent-research-assistant
```

### 2. Create virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API key

Create a `.env` file:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
```

Get a FREE Groq API key at: https://console.groq.com/keys

### 5. Run the web server

```bash
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

Or on Windows:

```bash
run_web.bat
```

### 6. Open in browser

Navigate to http://localhost:8000

## Usage

1. Enter your research topic (e.g., "deep learning for object detection")
2. Select data sources (Google Scholar, arXiv, PubMed, etc.)
3. Set maximum number of papers (3-5 recommended for free tier)
4. Click **Start Research**
5. Watch real-time progress as agents work
6. View the generated literature review
7. Export results or citations as needed

## Data Sources

| Source | API Key Required | Best For |
|--------|:---:|---------|
| Google Scholar | No | All fields (most comprehensive) |
| arXiv | No | Physics, Math, CS preprints |
| PubMed | No | Medical and life sciences |
| CORE | No | Open access papers |
| CrossRef | No | Metadata, 130M+ papers |
| bioRxiv | No | Biology preprints |
| PLOS ONE | No | Peer-reviewed open access |
| Semantic Scholar | No | AI-powered search |
| IEEE Xplore | Yes (free) | Engineering, CS, Electronics |

7 out of 9 sources work without any API key.

## Export Options

- **Markdown** (.md) — For GitHub, Notion, Obsidian
- **HTML** (.html) — Formatted report viewable in any browser
- **JSON** (.json) — Structured data for further processing
- **Citations** — BibTeX, APA, MLA, Chicago formats

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Web UI |
| GET | `/health` | Health check |
| POST | `/api/research` | Run research (REST) |
| WS | `/ws` | Real-time research (WebSocket) |
| GET | `/api/history` | Search history |
| GET | `/api/history/stats` | History statistics |
| DELETE | `/api/history/{id}` | Delete a search |
| POST | `/api/export/markdown` | Export as Markdown |
| POST | `/api/export/html` | Export as HTML |
| POST | `/api/export/json` | Export as JSON |
| POST | `/api/export/citations/{format}` | Export citations |

## Project Structure

```
multi-agent-research-assistant/
├── src/
│   ├── agents/                # 4 specialized AI agents
│   │   ├── base_agent.py
│   │   ├── searcher_agent.py
│   │   ├── analyzer_agent.py
│   │   ├── fact_checker_agent.py
│   │   └── synthesizer_agent.py
│   ├── integrations/          # 9 data source clients
│   │   ├── google_scholar_client.py
│   │   ├── ieee_client.py
│   │   ├── arxiv_client.py
│   │   ├── pubmed_client.py
│   │   ├── semantic_scholar_client.py
│   │   ├── core_client.py
│   │   ├── crossref_client.py
│   │   ├── biorxiv_client.py
│   │   └── plos_client.py
│   ├── llm/                   # LLM client wrappers
│   │   └── groq_client.py
│   ├── memory/                # Vector database
│   │   └── vector_memory.py
│   ├── orchestrator/          # Agent coordinator
│   │   └── master_orchestrator.py
│   ├── api/                   # FastAPI backend
│   │   └── main.py
│   ├── utils/                 # Export, history, config
│   │   ├── export_utils.py
│   │   ├── history_manager.py
│   │   └── config.py
│   └── main.py                # CLI interface
├── web/
│   └── index.html             # Web UI
├── prompts/                   # Agent prompt templates
├── config/
│   └── settings.yaml
├── requirements.txt
└── run_web.bat
```

## Free Tier Tips

- Use **3-5 papers** per search (not 10+)
- Select **2-4 sources** at a time
- Wait **1-2 minutes** between searches (Groq resets every 60 seconds)
- Google Scholar + arXiv + CORE gives great coverage

## License

MIT License
