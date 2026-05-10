# 🔬 ResearchMind — Multi-Agent Research Pipeline

> An end-to-end AI research assistant powered by **four specialised agents** that search, read, write, and critique — all orchestrated through a real-time streaming UI.

---



## 🧠 How It Works — The Multi-Agent Architecture

The pipeline is made up of **four agents** running in strict sequence. Each agent has a single responsibility, and the output of one feeds directly into the next.

```
User Query
    │
    ▼
┌─────────────────────┐
│  1. Search Agent    │  ── Tavily Web Search ──► Top 5 URLs + snippets
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│  2. Reader Agent    │  ── BeautifulSoup Scraper ──► Deep content from best URL
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│  3. Writer Agent    │  ── LLM Chain ──► Structured research report
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│  4. Critic Agent    │  ── LLM Chain ──► Score, strengths, improvements
└─────────────────────┘
    │
    ▼
Final Report + Feedback
```

### Agent Breakdown

| # | Agent | Role | Tool Used |
|---|-------|------|-----------|
| 1 | **Search Agent** | Finds recent, reliable web sources for the topic | `web_search` via Tavily API |
| 2 | **Reader Agent** | Picks the most relevant URL and scrapes its full content | `scrap_url` via BeautifulSoup |
| 3 | **Writer Agent** | Combines all research into a structured report (Intro → Findings → Conclusion → Sources) | Gemini 2.5 Flash LLM Chain |
| 4 | **Critic Agent** | Reviews the report and gives a score, strengths, and areas to improve | Gemini 2.5 Flash LLM Chain |

---

## 🗂️ Project Structure

```
research-pipeline/
│
├── agents.py          # Defines all 4 agents and LLM chains
├── tools.py           # web_search (Tavily) and scrap_url (BeautifulSoup) tools
├── pipeline.py        # Orchestrates agents in sequence, manages state
├── main.py            # FastAPI backend — exposes /research/stream SSE endpoint
├── index.html         # Frontend UI — real-time agent status, typewriter output
├── requirements.txt   # Python dependencies
└── .env               # API keys (not committed)
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|-------|------------|
| LLM | Gemini 2.5 Flash (`google-genai`) |
| Agent Framework | LangChain (`create_agent`, `ChatPromptTemplate`) |
| Web Search | Tavily API |
| Web Scraping | BeautifulSoup4 + Requests |
| Backend | FastAPI + Uvicorn (SSE streaming) |
| Frontend | Vanilla HTML / CSS / JavaScript |
| Env Management | `python-dotenv` |

---

## 🔑 Key Design Decisions

**Sequential over parallel** — Agents run one after another because each depends on the previous agent's output. The Search Agent must finish before the Reader can pick a URL; the Writer needs scraped content before drafting.

**Server-Sent Events (SSE)** — Instead of waiting for the full pipeline to finish, the FastAPI backend streams an event for every agent state change (`agent_start`, `agent_done`, `pipeline_done`). The frontend updates in real time without polling.

**Separation of concerns** — `tools.py` holds raw tool logic, `agents.py` assembles agents and chains, `pipeline.py` manages state, and `main.py` only handles HTTP. Each file has one job.

**LLM Chains for Writer and Critic** — Writer and Critic don't need tool access, so they use lightweight `prompt | model | StrOutputParser()` chains instead of full agents, which is faster and cheaper.

---

## 🚀 Getting Started

### 1. Clone and set up the environment

```bash
git clone https://github.com/your-username/research-pipeline.git
cd research-pipeline

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac / Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
pip install fastapi uvicorn
```

### 3. Add your API keys

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

> Get Gemini key → [Google AI Studio](https://aistudio.google.com/)  
> Get Tavily key → [Tavily](https://tavily.com/)

### 4. Start the backend

```bash
uvicorn main:app --reload
```

Backend runs at `http://localhost:8000`. API docs available at `http://localhost:8000/docs`.

### 5. Open the frontend

```bash
python -m http.server 3000
```

Then visit `http://localhost:3000` in your browser.

---

## 🖥️ UI Features

- **Sequential agent cards** — each agent lights up one at a time as it works
- **Live skeleton loader** — animated shimmer while the agent is processing
- **Typewriter output** — results type out word-by-word as they arrive
- **Glowing timeline spine** — vertical connector line fills with colour as agents complete
- **Pass labels** — shows exactly what data is handed from one agent to the next
- **Live timer** — tracks how long each agent takes
- **Final output tabs** — view Report, Critic Feedback, and Raw JSON separately
- **Copy button** — one-click copy for any output panel

---

## 📡 API Reference

### `POST /research/stream`
Streams Server-Sent Events as each agent finishes.

**Request body:**
```json
{ "topic": "quantum computing" }
```

**SSE events emitted:**
| Event | Payload |
|-------|---------|
| `agent_start` | `{ agent, step }` |
| `agent_done` | `{ agent, step, result }` |
| `agent_error` | `{ agent, step, error }` |
| `pipeline_done` | `{ topic, search_results, scraped_content, report, feedback }` |

### `POST /research`
Blocking endpoint — returns all results at once (useful for testing).

---

## 🧪 Test Without the UI

```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"topic": "future of renewable energy"}'
```

---

## 📋 Requirements

See `requirements.txt` for the full list. Key packages:

```
google-genai>=2.0.0
langchain>=0.2.0
langchain-core>=0.2.0
langchain-community>=0.2.0
tavily-python>=0.3.0
beautifulsoup4>=4.12.0
requests>=2.31.0
python-dotenv>=1.0.0
fastapi
uvicorn
```

---

## 🙋 Author

Built by Aman Jayswal — feel free to connect on [LinkedIn](https://www.linkedin.com/in/aman-jayswal-a74276281/​)


---

## 📄 License

MIT License — free to use, modify, and distribute.
