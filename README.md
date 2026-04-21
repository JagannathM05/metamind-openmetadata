# 🧠 MetaMind — Conversational AI Agent for OpenMetadata

> Talk to your entire data catalog in plain English.

[![Hackathon](https://img.shields.io/badge/WeMakeDevs-BackToTheMetadata-blue)](https://wemakedevs.org/hackathons/openmetadata)
[![OpenMetadata](https://img.shields.io/badge/Built%20on-OpenMetadata%201.12.5-purple)](https://open-metadata.org)
[![Python](https://img.shields.io/badge/Python-3.11+-green)](https://python.org)
[![Groq](https://img.shields.io/badge/LLM-Groq%20Llama%203.3-orange)](https://groq.com)

---

## 🎯 Problem

Data teams waste hours navigating OpenMetadata UIs to find datasets, trace lineage, check compliance, and apply governance tags. Non-technical users are completely locked out. Even engineers lose 20-30 minutes per task clicking through menus.

**MetaMind eliminates this friction entirely.**

---

## 💡 Solution

MetaMind is an intelligent AI agent that lets anyone interact with their OpenMetadata catalog through natural language. Ask questions, get instant answers — no UI knowledge required.
"What tables exist in our catalog?"
"Get me the full schema of ACT_HI_PROCINST"
"Detect PII columns in ACT_EVT_LOG"
"Generate a governance report for our top 10 tables"
"Apply PII.Sensitive tag to ACT_GE_BYTEARRAY"

---

## 🏗️ Architecture
User (Natural Language)
↓
Streamlit Chat UI
↓
Groq LLM Agent (Llama 3.3 70B)
— JSON-based agentic tool calling loop —
↓
OpenMetadata Tool Layer (9 tools)
↓
OpenMetadata REST APIs (localhost:8585)
↓
Live Data Catalog (168 tables)

---

## 🛠️ Agent Tools

| Tool | OpenMetadata API | Purpose |
|------|-----------------|---------|
| `list_tables()` | Tables API | List all catalog assets |
| `search_assets()` | Search API | Natural language search |
| `get_table_details()` | Tables API | Full schema + columns |
| `get_lineage()` | Lineage API | Upstream/downstream tracing |
| `detect_pii()` | Governance API | PII column detection |
| `get_data_quality()` | Observability API | Health scores + test results |
| `apply_tags()` | Governance API | Write tags back to catalog |
| `list_pipelines()` | Pipelines API | Data pipeline listing |
| `generate_governance_report()` | Multi-API | Full compliance report |

---

## ✨ Key Features

### 🔍 Natural Language Data Discovery
Search and explore 168+ tables without knowing the UI or API structure.

### 🛡️ Automated PII Detection
Scan any table for personally identifiable information. Get risk levels (LOW/MEDIUM/HIGH) and remediation recommendations instantly.

### 📊 Governance Report Generation
Scan multiple tables in one query — get PII counts, health scores, ownership gaps, and tag coverage in a single report.

### 🏷️ Auto-Tagging (Write back to OpenMetadata)
Apply governance tags directly to datasets through conversation. Changes are immediately reflected in OpenMetadata.

### 🔗 Lineage Tracing
Trace upstream sources and downstream consumers for any table.

---

## 🚀 Quick Start

### Prerequisites
- Docker Desktop (8GB RAM allocated)
- Python 3.11+
- Groq API key (free at [console.groq.com](https://console.groq.com))
- OpenMetadata running locally

### 1. Clone & Setup
```bash
git clone https://github.com/JagannathM05/metamind-openmetadata.git
cd metamind-openmetadata
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Start OpenMetadata
```bash
docker compose up -d
# Wait 5 minutes for all containers to be healthy
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your values:
# GROQ_API_KEY=your_groq_key
# OM_TOKEN=your_openmetadata_jwt_token
# OM_HOST=http://localhost:8585
```

### 4. Run MetaMind
```bash
streamlit run ui/app.py
```

Open [http://localhost:8501](http://localhost:8501) 🎉

---

## 💬 Example Conversations

**Data Discovery:**
> "List the first 20 tables in our catalog"
> "Search for tables related to user activity"

**Schema Exploration:**
> "Get full details of ACT_HI_PROCINST table"
> "Show me all columns in ACT_EVT_LOG"

**Governance & Compliance:**
> "Detect PII in ACT_EVT_LOG table"
> "Generate a governance report for 10 tables"
> "Apply PII.Sensitive tag to ACT_GE_BYTEARRAY"

**Data Quality:**
> "Check data quality for ACT_HI_PROCINST"
> "Which tables have failing quality tests?"

---

## 🏆 Hackathon

**Event:** Back to the Metadata — WeMakeDevs × OpenMetadata
**Track:** Paradox #T-01 — MCP Ecosystem & AI Agents
**Also covers:** T-02 (Observability) + T-06 (Governance)

### Why MetaMind wins:
- **Real OpenMetadata integration** — 9 tools across 5 different API categories
- **Agentic architecture** — multi-step reasoning, tool chaining
- **Write-back capability** — applies tags directly to OpenMetadata
- **Governance report** — multi-table compliance scanning in one query
- **Instant demo value** — works out of the box, results in seconds

---

## 🔧 Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Groq (Llama 3.3 70B) — free, 500+ tok/sec |
| Agent Loop | Custom JSON-based tool calling |
| UI | Streamlit |
| Data Catalog | OpenMetadata v1.12.5 |
| Database | MySQL 8.0 (via Docker) |
| Search | Elasticsearch 9.3 |
| Language | Python 3.11 |

---

## 📁 Project Structure
metamind-openmetadata/
├── agent/
│   └── metamind_agent.py      # LLM agent with tool calling loop
├── tools/
│   └── openmetadata_tools.py  # 9 OpenMetadata API tools
├── ui/
│   └── app.py                 # Streamlit chat interface
├── docker-compose.yml         # OpenMetadata stack
├── requirements.txt
├── .env.example
└── README.md

---

## 📹 Demo

[Watch Demo Video](#) ← Add your YouTube link here

---

## 👤 Author

**Jagannath M** — Final year CS AI Engineering student
- GitHub: [@JagannathM05](https://github.com/JagannathM05)
- Built for: Back to the Metadata Hackathon 2026