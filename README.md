# AlphaOS (anagraph)

> An AI analyst that learns how your fund thinks — and finds the edges your team hasn't seen yet.

Agentic AI research platform for hedge funds. Automates deep-dive company research, surfaces market edges, and adapts to each fund's investment style.

---

## Project Structure

```
anagraph/
├── backend/
│   ├── app/
│   │   ├── api/routes/        # FastAPI route handlers
│   │   ├── core/config.py     # Settings (env vars)
│   │   ├── services/
│   │   │   ├── edgar.py       # SEC EDGAR scraper
│   │   │   └── report_generator.py  # Claude AI report engine
│   │   ├── models/research.py # Pydantic models
│   │   └── db/database.py     # DB setup (Phase 1 placeholder)
│   ├── scripts/test_mvp.py    # ← START HERE
│   ├── requirements.txt
│   └── .env.example
├── frontend/                  # Next.js dashboard (Phase 1)
└── docs/
```

---

## Getting Started (Phase 0 MVP)

### 1. Set up the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env — paste your ANTHROPIC_API_KEY
```

### 2. Run the MVP smoke test

```bash
python scripts/test_mvp.py AAPL
```

This pulls Apple's latest 10-K from SEC EDGAR and generates a full research memo with inline citations. If this works, the pipeline is validated.

### 3. Start the API server

```bash
uvicorn app.main:app --reload
```

- API docs: http://localhost:8000/docs
- Generate a report: `POST /api/v1/report` with body `{"ticker": "AAPL"}`
- Or via GET: `GET /api/v1/report/AAPL`

---

## Phase Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| 0 | SEC EDGAR pipeline + MVP report (CLI + API) | ✅ Done |
| 1 | Report storage, fund tenancy, Next.js dashboard | 🔨 Next |
| 2 | Edge detection — anomaly detection, sentiment shifts | ⏳ Planned |
| 3 | Style adaptation — learn each fund's thesis format | ⏳ Planned |
| 4 | Pilot fund + GTM | ⏳ Planned |

---

## Critical Rules (do not skip)

- **Every claim must cite the source.** The report engine enforces this in the system prompt.
- **Track cost per report from day one.** Each report response includes `estimated_cost_usd`.
- **Fund data is completely isolated.** No cross-tenant data, ever (enforced in Phase 1 DB design).
- **This is not investment advice.** Legal disclaimer is appended to every report.
- **Audit trail.** Every report includes ticker, company, filing date, model version, and timestamp.
