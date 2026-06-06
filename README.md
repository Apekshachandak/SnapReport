# SnapReport

**Auto-generated monthly market report PDFs for real estate agents.**

Agents enter a ZIP code. SnapReport pulls live MLS data, writes a plain-English AI market narrative, and renders a branded PDF in under 90 seconds — ready to send to their client list.

**Live demo:** https://snapreport-production.up.railway.app

---

## My Approach

Before writing a single line of code, I used AI to help me think — not to generate code, but to stress-test my understanding of the problem, lock down decisions, and break the work into concrete tasks. I find this makes the actual build significantly faster because there are no surprises mid-way through.

The planning happened in three stages, each captured in a document:

**[`design_decisions.md`](../design_decisions.md) — Design grilling session**
I gave the AI my initial project brief and invoked a structured "grill me" skill that asked me hard questions about every design decision — one at a time — before I'd written anything. Things like: what happens if the API is down? Why two API calls instead of one? How do you handle LLM hallucinations? Working through these questions upfront meant I went into the build with clear answers, not assumptions.

**[`prd.md`](../prd.md) — Product requirements**
Once the design decisions were settled, I wrote a PRD to formalise exactly what needed to exist. Functional requirements, non-functional requirements, what was explicitly out of scope, tech choices with reasoning, and the full PDF content spec. Writing this forced me to be precise about the scope — which is what kept the build focused during the hackathon hour.

**[`prd_to_issues.md`](../prd_to_issues.md) — Engineering issue breakdown**
Finally I broke the PRD into 13 concrete engineering issues, ordered by dependency — you can't build a PDF before you have data, you can't serve the UI before you have the PDF. Each issue had acceptance criteria so I knew exactly when it was done. This is the list I worked through during the actual build.

The actual code was written after all three documents existed. AI helped throughout — but the decisions were mine.

---

## The Problem

Real estate agents know they should send monthly market updates to their contacts. Almost none do — because pulling data, writing copy, and designing a PDF takes 3–4 hours they don't have. The agents who do it consistently out-earn those who don't.

## The Solution

One input. One click. One branded PDF.

---

## How It Works

```
ZIP code
   │
   ▼
RealEstateAPI.com  ──  2 API calls
   │  Call 1: market summary (median price, days on market, active/pending counts)
   │  Call 2: recent sales last 90 days (address, price, date)
   ▼
Groq — Llama 3.3 70B  ──  writes a 3–4 sentence plain-English market narrative
   ▼
ReportLab  ──  draws the branded PDF directly onto a canvas (no HTML/CSS)
   ▼
report_90210_2026-06-06.pdf
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask |
| Data | RealEstateAPI.com |
| AI | Groq — Llama 3.3 70B (free tier) |
| PDF | ReportLab (canvas API) |
| Frontend | Vanilla HTML / CSS / JS |
| Deployment | Railway |

---

## Project Structure

```
snapreport/
├── main.py           — CLI entry point
├── data_fetcher.py   — RealEstateAPI.com (2 calls)
├── llm_writer.py     — Groq narrative generation
├── pdf_generator.py  — ReportLab PDF rendering
├── app.py            — Flask web server
├── templates/
│   └── index.html    — Web UI
├── requirements.txt
├── Procfile          — Railway/Render deployment
└── .env.example      — Environment variable template
```

---

## PDF Report Layout

- **Header** — Navy bar with Snaphomz branding + gold accent line
- **Agent card** — Optional: name, phone, email, brokerage (if provided)
- **Stats grid** — 2×3 cards: Median Price · Days on Market · Active Listings · Pending · Sold (90d) · Owner Occupied %
- **Market narrative** — AI-written 3–4 sentence plain-English analysis
- **Recent sales table** — Up to 8 comps: address, sale price, date
- **Footer** — Data attribution + generation date

---

## Setup

### 1. Clone and install

```bash
git clone <repo-url>
cd snapreport
pip install -r requirements.txt
```

### 2. Get API keys

| Key | Where to get it |
|---|---|
| `REAPI_KEY` | [realestateapi.com](https://realestateapi.com) → Dashboard → API Keys → use the **backend/secret** key |
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) → API Keys → Create API Key (free, starts with `gsk_`) |

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in both keys
```

`.env` format:
```
REAPI_KEY=your_reapi_key
GROQ_API_KEY=your_groq_key
```

---

## Running Locally

### CLI mode
```bash
python3 main.py --zip 90210

# With agent branding stamped on the PDF:
python3 main.py --zip 90210 \
  --agent-name "Sarah Chen" \
  --agent-phone "310-555-0190" \
  --agent-email "sarah@realty.com" \
  --agent-company "Premier Realty"
```

### Web UI
```bash
python3 app.py
# Open http://localhost:5000
```

PDF saves to `./output/report_<zip>_<date>.pdf`

---

## Deployment (Railway)

```bash
# Install Railway CLI
curl -fsSL https://railway.app/install.sh | sh

# Deploy
~/.railway/bin/railway up

# Add public URL
~/.railway/bin/railway domain

# Set environment variables
~/.railway/bin/railway variables set REAPI_KEY=... GROQ_API_KEY=...
```

---

## Key Numbers

| Metric | Value |
|---|---|
| ZIP → PDF | ~90 seconds |
| Summary API call cost | 0 credits |
| Groq free tier | 14,400 requests/day |
| Time replaced for agent | 3–4 hours |
| Cost per report at scale | < $0.02 |

---

## Deliberately Not Built (v2)

- Email scheduling via SendGrid
- Agent photo upload
- Multi-ZIP batch generation
- Report caching / database

These are obvious next steps — each is ~1 day of work on top of the existing pipeline. Scoped out to validate the core pipeline first.

---

## Business Case for Snaphomz

- **Recurring engagement** — agents use it every month, not just when listing
- **Co-brand reach** — every PDF in a homeowner's inbox is a Snaphomz impression at zero media cost
- **Lead conversion** — homeowners who see their market appreciating become warm future sellers
- **Retention** — gives agents a reason to stay on the platform monthly

---

Built for Snaphomz Hackathon 2.0
