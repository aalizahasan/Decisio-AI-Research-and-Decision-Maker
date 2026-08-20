# AI Research & Decision Platform

> An evidence-based decision-making platform designed to help users analyze complex problems, evaluate trade-offs, and make data-driven decisions.

## 📌 Project Overview

**AI Research & Decision Platform** is a modern full-stack web application designed to guide individuals and organizations through multi-criteria decision analysis (e.g., choosing between React Native vs. Flutter, evaluating AWS vs. Azure cloud migrations, or assessing new market entries).

This repository is being engineered **incrementally** to serve as a high-quality portfolio project and learning baseline for production AI application engineering.

---

## 🚀 Current Development Stage: Task 1 — Foundation

The project is currently at **Task 1 (Project Foundation)**:
- **Clean Monorepo Structure**: Complete separation of concerns between `frontend/` and `backend/`.
- **Frontend SPA**: Built with React, Vite, TypeScript, and modern CSS. Features a clean landing layout, dynamic health indicator, and roadmap placeholders.
- **Backend REST API**: Built with Python, FastAPI, CORS middleware, environment configuration, and a `/health` endpoint.
- **Frontend-Backend Integration**: The frontend verifies backend connectivity by polling `GET /health` on startup.

---

## 🗺️ High-Level Planned Evolution

The platform will evolve incrementally across future releases:

1. **Task 1 (Current)**: Monorepo Foundation & Health Communication.
2. **Phase 2 (Structured Decision Analysis)**: Interactive decision input forms, weighting matrix algorithms, and criteria evaluation models.
3. **Phase 3 (RAG & Knowledge Workspace)**: Document ingestion (PDFs, docs), vector embeddings, and contextual retrieval.
4. **Phase 4 (Multi-Agent Research Workflows)**: Autonomous AI agents running parallel research, risk discovery, and counter-argument synthesis.
5. **Phase 5 (Evaluation & Reliability)**: Continuous response evaluation, factual grounding benchmarks, and confidence metrics.

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | React 18+ | UI Component Library |
| **Frontend Tooling** | Vite | Lightning-fast dev server and bundler |
| **Language** | TypeScript | Strong client-side static typing |
| **Styling** | Modern CSS | Minimal slate/dark design system |
| **Backend** | Python 3.11+ | Server language |
| **API Framework** | FastAPI | High-performance async REST framework |
| **ASGI Server** | Uvicorn | Server runner for FastAPI |
| **Config & Env** | python-dotenv | Environment variable loading |

---

## 📂 Project Structure

```text
ai-research-decision-platform/
│
├── frontend/                   # React + Vite + TypeScript application
│   ├── src/
│   │   ├── components/         # Modular React components
│   │   │   ├── Header.tsx      # Top bar with branding & status badge
│   │   │   ├── HealthStatus.tsx# Fetches GET /health endpoint
│   │   │   ├── Hero.tsx        # Mission statement & headline
│   │   │   ├── FeatureGrid.tsx # Roadmap vision placeholders
│   │   │   └── Footer.tsx      # Footer note
│   │   ├── App.tsx             # Root React component
│   │   ├── index.css           # Global CSS variables & styles
│   │   ├── main.tsx            # React DOM entry point
│   │   └── types.ts            # TypeScript interfaces
│   ├── index.html              # Single Page App HTML container
│   ├── package.json            # Node dependencies and scripts
│   ├── tsconfig.json           # TypeScript configuration
│   └── vite.config.ts          # Vite build & dev server setup
│
├── backend/                    # Python + FastAPI REST API server
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py           # Environment variable settings
│   │   ├── routes.py           # API endpoints (/health)
│   │   └── main.py             # FastAPI entry point & CORS
│   └── requirements.txt        # Python package dependencies
│
├── .env.example                # Environment template guide
├── .gitignore                  # Git exclusion rules
└── README.md                   # Project documentation
```

---

## ⚡ Quick Start & Setup Instructions

### Prerequisites
- **Node.js**: `v18+` (Verify with `node -v`)
- **Python**: `3.10+` (Verify with `python --version`)

---

### 1. Running the Backend (FastAPI)

1. Open a terminal and navigate to `backend/`:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   # On Windows PowerShell / Command Prompt:
   python -m venv .venv
   .venv\Scripts\activate

   # On macOS/Linux:
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

5. Verify Backend Health:
   - Open browser at `http://127.0.0.1:8000/health`
   - You should receive:
     ```json
     {
       "status": "healthy",
       "service": "AI Research & Decision Platform API",
       "environment": "development",
       "version": "0.1.0"
     }
     ```
   - Interactive Swagger API docs are available at `http://127.0.0.1:8000/docs`.

---

### 2. Running the Frontend (React + Vite)

1. Open a second terminal and navigate to `frontend/`:
   ```bash
   cd frontend
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```

4. Open the web app:
   - Visit `http://localhost:5173` in your browser.
   - The top header will show **"API Online"** in green when connected to the backend.

---

## 🔒 Security & Environment Variables

Environment configuration is managed via `.env.example`. When integrating external LLM APIs (OpenAI, Anthropic) or database credentials in future tasks, create a local `.env` file based on `.env.example`.

`.env` files are ignored by `.gitignore` to protect credentials.
