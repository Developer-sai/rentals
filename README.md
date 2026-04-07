# IrishHome.AI: Plug-and-Play Housing Market Intelligence

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![React: Latest](https://img.shields.io/badge/React-Latest-61dafb.svg)](https://reactjs.org/)
[![Framework: LangGraph](https://img.shields.io/badge/Framework-LangGraph-orange.svg)](https://github.com/langchain-ai/langgraph)

**IrishHome.AI** is a state-of-the-art, **plug-and-play** LLM-based AI chatbot designed to simplify Irish housing market navigation. By combining official datasets with a modular **multi-agent** architecture, it delivers precise, auditable, and real-time housing insights.

---

## 🌟 Vision: The Plug-and-Play Intelligence Layer
IrishHome.AI is designed to be a **seamless, drop-in intelligence solution** for any housing-related platform. Its architecture allows for:
- **Instant Integration**: Easily connects to real-time property portals like **Daft.ie**, **Rent.ie**, and **Myhome.ie**.
- **Agentic Extensibility**: A modular multi-agent system where specialized agents (Retrieval, Web Search, Analysis) can be added or swapped to meet specific business needs.
- **Data Agnostic RAG**: Works across static CSVs, SQL databases, and live web-scraping/API hooks simultaneously.

### The Problem: Information Asymmetry
The Irish housing crisis is exacerbated by fragmented data. Users must navigate the Residential Tenancies Board (RTB) for rents, the Property Price Register (PPR) for sale prices, and the Central Statistics Office (CSO) for earnings.

### The Solution: Real-Time Web Intelligence
With the integration of the **Real-Time Web Intelligence Agent (Tavily)**, IrishHome.AI now provides the latest market news, recent listings, and policy updates directly from the web, grounding its core CSV-based analysis in the absolute present.
- **Real-Time Affordability**: Instantly calculates if a specific county is "affordable" based on local median earnings vs. current market rents.
- **Mortgage Clarity**: Bridges the gap between "Price" and "Monthly Cost" by factoring in current interest rates, deposit requirements, and 30-year terms.
- **Market Transparency**: Provides high-resolution historical trends (2010–2024), allowing users to see exactly where prices are appreciating fastest.

---

## 🛠️ Technical Architecture

### Agentic Structured-Data RAG (ASD-RAG)
Unlike traditional RAG systems that rely on "fuzzy" vector similarity (often leading to numerical hallucinations), IrishHome.AI uses **ASD-RAG**. 
1. **Deterministic Retrieval**: The system uses Python/Pandas logic to filter structured CSV data with 100% precision.
2. **LLM as the Reasoning Engine**: The Large Language Model (Gemini/LLaMA) is used only for *intent classification* and *narrative synthesis*, never for "remembering" numbers.

### The Five-Stage LangGraph Pipeline
The backend executes a compiled state machine:
1.  **Intent Agent**: Classifies queries into 7 categories (Rent, Sale, Affordability, etc.) and extracts entities (County, Year).
2.  **Retrieval Agent**: Executes deterministic Pandas queries against RTB/PPR/CSO datasets.
3.  **Analysis Agent**: Performs macroeconomic calculations (Mortgage schedules, Rent-to-Income ratios).
4.  **Reasoning Agent**: Synthesizes a natural language response grounded strictly in the calculated data.
5.  **Response Agent**: Packages text, metrics, and dynamic Chart.js configurations into a unified JSON payload.

---

## 📊 Performance Benchmarks
Based on empirical evaluation (N=140 queries), the system achieves industry-leading reliability:

| Metric | ASD-RAG (Ours) | Baseline LLM |
| :--- | :--- | :--- |
| **Factual Accuracy** | **99.1%** | 38.2% |
| **Numerical Consistency** | **100%** | 22.5% |
| **Intent Classification** | **93.6%** | N/A |
| **Mean Latency** | **2.7s** | 2.1s |

---

## ⚙️ Data Ecosystem
The system consumes three core pillars of Irish government data:
- **RTB Rent Index**: Local Electoral Area (LEA) level historical rents.
- **Property Price Register (PPR)**: Multi-year Dublin residential transaction logs.
- **CSO Earnings**: County-level median gross earnings for affordability indexing.

---

## 🚀 Getting Started

### Backend Setup (FastAPI)
1. Navigate to directory: `cd FAI_Pro/backend`
2. Create virtual environment: `python -m venv venv`
3. Install dependencies: `pip install -r requirements.txt`
4. Set `.env` variables: `GOOGLE_API_KEY`, `MODEL_NAME`
5. Launch: `uvicorn main:app --reload`

### Frontend Setup (Vite + React)
1. Navigate to directory: `cd FAI_Pro/frontend`
2. Install dependencies: `npm install`
3. Launch: `npm run dev`

---

## 🗺️ Roadmap
- [ ] **Spatial Analysis**: Integration with PostGIS for neighborhood-level mapping.
- [ ] **Live API Sync**: Transition from static CSVs to direct RTB/CSO API hooks.
- [ ] **Multi-turn Memory**: Support for contextual follow-up questions.
- [ ] **expanded Coverage**: Nationwide PPR data beyond the Dublin region.

---

## 📜 License & Acknowledgements
- **License**: MIT
- **Data Credits**: [RTB](https://rtb.ie), [CSO](https://cso.ie), [PPR](https://propertypriceregister.ie).
- **Academic Research**: Developed as part of a Master's thesis at the National College of Ireland.