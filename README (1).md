# AlphaOS

> An AI analyst that learns how your fund thinks — and finds the edges your team hasn't seen yet.

Agentic AI research platform for hedge funds. Automates deep-dive company research, surfaces market edges, and adapts to each fund's investment style.

---

## Project Structure

```
hedgefund-ai/
├── backend/               # Python FastAPI
│   ├── app/
│   │   ├── api/           # Route handlers
│   │   ├── core/          # Config, settings
│   │   ├── services/      # Business logic (scraper, report generator)
│   │   ├── models/        # SQLAlchemy models (Phase 1)
│   │   └── db/            # Database setup (Phase 1)
│   ├── scripts/
│   │   └── test_mvp.py    # ← START HERE
│   └── requirements.txt
├── frontend/              # Next.js (Phase 1)
└── docs/
```

---

## Getting Started (Phase 0 MVP)

### 1. Set up backend

```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env — add your ANTHROPIC_API_KEY
```

### 2. Run the MVP smoke test

```bash
python scripts/test_mvp.py AAPL
```

This pulls Apple's latest 10-K from SEC EDGAR and generates a full research report. If this works, the pipeline is validated.

### 3. Start the API server

```bash
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

---

## Phase Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| 0 | Data pipeline + MVP report | 🔨 Building |
| 1 | Full report engine + dashboard | ⏳ Planned |
| 2 | Edge detection layer | ⏳ Planned |
| 3 | Fund style adaptation | ⏳ Planned |
| 4 | Pilot fund + GTM | ⏳ Planned |

---

## Critical Rules (do not skip)

- **Every claim in every report must cite a source.** No exceptions.
- **Track cost per report** from day one. LLM calls on large filings add up.
- **Fund data is completely isolated** — no cross-tenant data, ever.
- **This is not investment advice.** Legal disclaimers on all output.
