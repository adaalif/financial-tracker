# Financial Tracker Web App & AI Receipt Scanner

A comprehensive, unified application for end-to-end multi-currency expense management. Built on an SQL backend, this application allows users to process receipt images with extreme accuracy through an AI multimodal pipeline, alongside managing a complete enterprise-grade history ledger, manual entry pipelines, and category normalization directly from a dynamic interactive Web frontend.

## Key Features

- **AI-Powered Receipt Parsing:** Automatically process receipt images to extract line items, merchant details, prices, and categories via integration with the highly-optimized Groq Vision API.
- **Unified Master Ledger (History):** A robust, Excel-style interactive data grid aggregating all historical purchases, fully sortable and filterable to gain a consolidated view of finances.
- **Two-Phase Human Verification Pipeline:** The scanner parses data in the background, rendering a dedicated preview page so you can intercept and edit data before writing securely to the robust SQL database.
- **Manual Data Entry Engine:** Dynamic, multi-level localized HTML5 web forms seamlessly mapped to an underlying normalized Database allowing insertion of custom items under dynamically allocated categories on-the-fly.
- **Automated Category Mapping:** The backend will automatically map items to new classifications on the fly. Dropdowns are intuitively rendered via custom Brutalist-style interactive Web Components, ensuring obsolete categories organically drop out of visibility.

## Technology Stack

- **Backend / Routing:** [Python 3.12+] & [FastAPI](https://fastapi.tiangolo.com)
- **Database / ORM:** [SQLModel](https://sqlmodel.tiangolo.com) serving PostgreSQL / local SQLite setups with Alembic for structural migrations.
- **AI Processing Engine:** Custom parser bridging [Groq](https://groq.com/) Vision APIs (`gemma-2-9b` or `Llama-3` multimodal architecture). 
- **Frontend Layer:** Rendered statically yet dynamically driven natively via Jinja2 Templating, modern TailwindCSS utilities, HTML5 custom Datalists, and custom Vanilla Object-Oriented Javascript Components.
- **Server:** ASGI deployment via Uvicorn.
- **Dependency Management:** [uv](https://astral.sh/blog/uv) (by Astral).

## Project Structure

```
.
├── ai/                # Modules communicating with multi-modal LLMs (Groq)
├── alembic/           # Relational schema history mapping configurations
├── api/
│   └── routers/       # Core HTTP API & Web endpoints including web.py forms logic
├── bot/               # Legacy Telegram bot interoperability implementations
├── cache/             # Transient RAM cache state before transactions are persisted
├── database/          # Database connection pipelines and SQLModel architecture paradigms
├── parser/            # Multi-layer parser including Regex Fallback integrations
├── static/            # Static Assets, CSS design tokens, & dynamic JS UI Components
├── templates/         # Raw localized Jinja2 HTML layout blueprints  
└── config.py          # Unified Pydantic base configuration
```

## Getting Started

### 1. Prerequisites 

Ensure you have [uv installed](https://docs.astral.sh/uv/) on your native host environment.

### 2. Environment Configuration

Copy the example configuration to establish environmental references:
```bash
cp .env.example .env
```
Populate `.env` completely. You'll strictly need a valid `GROQ_API_KEY` for the AI functionality hook. 

### 3. Execution & Deployment Setup

Pull robust backend dependencies directly with `uv`.

```bash
uv sync 
```

Run the FastAPI Uvicorn deployment stack synchronously:
```bash
uv run uvicorn api.main:app --reload
```
By default, the UI will bind strictly to `http://127.0.0.1:8000/`.

## Architecture Note
This monolithic service implements dual pipelines. Users historically relying on Telegram processing (`main.py`) concurrently share schema footprints mapping into the newly integrated unified Web App UI router schemas (`api.main`). This ensures zero data loss between asynchronous input variants.

## Testing Guidelines

```bash
uv run pytest
```
Test iterations rely comprehensively on integration bounds testing validation against mocked AI extractions and transactional database rollbacks to guarantee financial ledger integrity is consistently resilient.
