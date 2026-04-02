# IrishHome.AI — Project Documentation

> **An Agentic Structured-Data RAG System for Irish Housing Market Intelligence**

---

## Table of Contents
1. [What is IrishHome.AI?](#what)
2. [Problem Statement](#problem)
3. [Why This Approach?](#why)
4. [Architecture Overview](#architecture)
5. [Agent Pipeline](#agents)
6. [Features](#features)
7. [Datasets](#datasets)
8. [API Reference](#api)
9. [Tech Stack](#tech)
10. [How to Run](#howto)
11. [Plugin Integration](#plugin)
12. [Future Roadmap](#roadmap)

---

## 1. What is IrishHome.AI? <a name="what"></a>

IrishHome.AI is a conversational AI assistant that answers natural-language questions about the Irish property and rental market. It combines:

- **Groq LLM** (LLaMA 3.3 70B) for intent classification and expert contextual reasoning
- **Structured data retrieval** from real Irish datasets (RTB, CSO, PPR)
- **LangGraph multi-agent orchestration** for a reliable, auditable pipeline
- **FastAPI backend** with a dynamic frontend chat interface

Users get data-backed answers with charts, key metrics, and source attribution — not hallucinated guesses.

---

## 2. Problem Statement <a name="problem"></a>

Ireland is in a housing crisis. Renters and buyers face:

- **Opaque pricing**: No easy way to compare rents across counties over time
- **Affordability blindspots**: People don't know if their income makes renting/buying feasible
- **Data fragmentation**: RTB, CSO, and PPR publish separate datasets that aren't connected
- **Lack of accessible analysis**: Raw government data requires technical skills to interpret

IrishHome.AI bridges this gap with a plain-English interface over real public data.

---

## 3. Why This Approach (RAG vs Fine-Tuning)? <a name="why"></a>

| Approach | What It Is | Why NOT Used Here |
|---|---|---|
| **Fine-Tuning** | Retrain model weights on domain data | Expensive, static — data goes stale, needs retraining |
| **Semantic RAG** | Embed text chunks into vectors, retrieve by similarity | Overkill for structured tabular CSV data |
| **Agentic Structured RAG** ✅ | LLM + pandas queries on live CSVs via agent pipeline | Perfect for structured data; swap CSV → DB with zero LLM changes |

This system is **Agentic Structured-Data RAG**:
- The LLM is used only for *understanding the question* (intent) and *explaining the answer* (reasoning)
- The *retrieval and analysis* is done with pure Python (pandas) — deterministic, auditable, fast
- **Plugin-ready**: `data_manager.py` is the only layer that touches data. Connect it to a live PostgreSQL or RTB API and the entire agent stack works unchanged.

---

## 4. Architecture Overview <a name="architecture"></a>

```
User Query (Natural Language)
        │
        ▼
┌─────────────────────────────────────────────────────┐
│                   FastAPI Backend                    │
│  POST /api/chat                                      │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│             LangGraph State Machine                  │
│                                                      │
│  ┌──────────┐   ┌───────────┐   ┌────────────────┐  │
│  │  Intent  │──▶│ Retrieval │──▶│    Analysis    │  │
│  │  Agent   │   │  Agent    │   │    Agent       │  │
│  └──────────┘   └───────────┘   └───────┬────────┘  │
│    Groq LLM      Pandas/CSV              │            │
│                                          ▼            │
│                             ┌────────────────────┐   │
│                             │   Reasoning Agent  │   │
│                             │   (Groq LLM)       │   │
│                             └────────┬───────────┘   │
│                                      │                │
│                                      ▼                │
│                             ┌────────────────────┐   │
│                             │   Response Agent   │   │
│                             │   (chart_data,     │   │
│                             │    key_metrics)    │   │
│                             └────────────────────┘   │
└─────────────────────────────────────────────────────┘
        │
        ▼
Chat UI (HTML/CSS/JS + Chart.js)
```

---

## 5. Agent Pipeline <a name="agents"></a>

### Intent Agent
- **Input**: Raw user query
- **Output**: Structured intent JSON `{ intent, county1, county2, year, bedrooms, confidence }`
- **Model**: Groq LLaMA 3.3 70B, temp=0.1
- **Supports**: `rent_query`, `house_price_query`, `comparison`, `trend_analysis`, `affordability`, `recommendation`, `general_chat`

### Retrieval Agent
- **Input**: Classified intent + entities
- **Output**: Relevant data dict from CSV datasets
- **Method**: Pandas DataFrame filtering — no vector search needed
- **Routes**: Each intent type → specific `data_manager` function

### Analysis Agent
- **Input**: Retrieved data
- **Output**: Computed metrics (annual costs, deposit amounts, YoY trends, affordability ratings)
- **Method**: Pure Python math — deterministic and testable

### Reasoning Agent
- **Input**: Data + analysis summary
- **Output**: Conversational, contextual explanation
- **Model**: Groq LLaMA 3.3 70B, temp=0.4
- **Guardrail**: Refuses off-topic queries (coding, weather, sports, etc.)

### Response Agent
- **Input**: Full state
- **Output**: Final JSON with `answer`, `chart_data`, `key_metrics`, `sources`
- **Chart Types**: line (trends), bar (comparisons), doughnut (rent breakdown)

---

## 6. Features <a name="features"></a>

| Feature | Description |
|---|---|
| 🏠 Rent Queries | Average, median, min/max rent for any county, year, bedroom count |
| 🏷️ House Prices | Dublin property price statistics by year |
| ⚖️ County Comparison | Side-by-side rent comparison with euro and % difference |
| 📈 Trend Analysis | Year-over-year rent trends with total change % |
| 💰 Affordability | Price-to-earnings ratio, rent-to-income %, income needed |
| 📍 Recommendations | Overview of cheapest/most expensive counties |
| 📊 Dynamic Charts | Line, bar, doughnut charts rendered in the UI |
| 🔒 Guardrails | LLM refuses off-topic queries with a redirect |
| 🔍 Source Attribution | Every answer shows which dataset(s) were used |
| 🌐 REST API | `/api/chat` endpoint for third-party integration |

---

## 7. Datasets <a name="datasets"></a>

| File | Source | Contents | Size |
|---|---|---|---|
| `irish_rent_full.csv` | RTB (Residential Tenancies Board) | Full national rent data by county, area, bedrooms, year | ~5.7MB |
| `dublin_house_prices_cleaned.csv` | PPR (Property Price Register) | Dublin house sale prices with dates | ~27MB |
| `Master_Dataset.csv` | CSO (Central Statistics Office) | County-level: mean sale price, median earnings, year | Small |
| `irish_rent_by_county.csv` | RTB | County-level rent summary aggregations | Small |

All data reflects the **Irish residential market from ~2010 to 2024**.

---

## 8. API Reference <a name="api"></a>

### `POST /api/chat`
Send a natural language question.

**Request:**
```json
{ "query": "What is the average rent in Cork in 2023?", "session_id": "optional-uuid" }
```

**Response:**
```json
{
  "answer": "The average rent in Cork in 2023 was €1,450/month...",
  "intent": "rent_query",
  "chart_data": { "type": "doughnut", "title": "...", "labels": [...], "values": [...] },
  "key_metrics": { "annual_cost": 17400, "income_needed_30pct": 58000 },
  "sources": ["irish_rent_full.csv"],
  "session_id": null
}
```

### `GET /api/meta/counties`
Returns list of all available Irish counties.

### `GET /api/meta/years`
Returns list of all available years.

### `GET /health`
Returns `{ "status": "ok" }` for liveness checks.

---

## 9. Tech Stack <a name="tech"></a>

| Layer | Technology |
|---|---|
| LLM | Groq API (LLaMA 3.3 70B Versatile) |
| Agent Orchestration | LangGraph 0.1.x |
| Backend Framework | FastAPI 0.111 + Uvicorn |
| Data Processing | Pandas 2.2, NumPy 1.26 |
| Environment | Python-dotenv |
| Validation | Pydantic v2 |
| Frontend | Vanilla HTML/CSS/JS + Chart.js 4.4 |
| Fonts | Google Fonts (Inter, Fira Code) |

---

## 10. How to Run <a name="howto"></a>

### Prerequisites
- Python 3.10+
- A Groq API key (free at [console.groq.com](https://console.groq.com))

### Steps

```bash
# 1. Navigate to project
cd FAI_Pro

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment (edit .env)
GROQ_API_KEY=your_groq_key_here
GROQ_MODEL=llama-3.3-70b-versatile
DATA_DIR=../data

# 4. Start the server
# Windows:
run.bat

# Linux/Mac:
bash run.sh

# Or directly:
cd backend && python main.py
```

The application starts at **http://localhost:8000** and serves the chat UI automatically.

---

## 11. Plugin Integration <a name="plugin"></a>

IrishHome.AI is **designed as a plugin**. The data layer is fully abstracted:

```python
# data_manager.py — swap this implementation only
def get_rent_stats(county, year, bedrooms) -> dict:
    df = load_rent_data()   # ← Change this to a DB query
    ...
```

To integrate with a live database or external API:
1. Replace the CSV `load_*` functions in `data_manager.py` with database queries
2. Keep the same return schema (dict with the same keys)
3. No changes needed in any agent file

The LLM reasoning layer doesn't know or care where the data came from.

---

## 12. Future Roadmap <a name="roadmap"></a>

| Priority | Feature |
|---|---|
| 🔴 High | Live RTB API integration (replace static CSVs) |
| 🔴 High | Session memory (multi-turn conversation context) |
| 🟡 Medium | Map visualisation (county heat map by avg rent) |
| 🟡 Medium | Export to PDF / CSV |
| 🟡 Medium | Mortgage calculator with live ECB interest rates |
| 🟢 Low | User accounts with saved searches |
| 🟢 Low | Email alerts for rent change in target county |
| 🟢 Low | Landlord-side analytics (market positioning) |
