# SnapReport — PRD to Issues

> **Note:** After writing the PRD, I broke it down into concrete engineering issues — the actual tasks I needed to build. This was my personal pre-build ticket list so I could work through the build in a logical order without losing track of what needed to exist. Written before coding started; checked off mentally as I went.

---

## How to read this

Each issue maps to a specific PRD requirement (F# or NF#). They are ordered by dependency — you cannot build later issues without completing earlier ones. Status reflects what was done during the hackathon build.

---

## ISSUE-01 — Project scaffold and environment setup

**Linked to:** NF3, NF4
**Priority:** P0 — nothing else works without this

**What:**
Create the project folder structure, `requirements.txt`, `.env.example`, and `.gitignore`. Confirm that API keys load from `.env` via `python-dotenv` and are never committed.

**Acceptance criteria:**
- [ ] `snapreport/` folder exists with all planned files stubbed
- [ ] `.env.example` lists `REAPI_KEY` and `GROQ_API_KEY`
- [ ] `.gitignore` excludes `.env` and `output/`
- [ ] `pip install -r requirements.txt` runs clean

**Status: Done**

---

## ISSUE-02 — Data fetcher: market summary call

**Linked to:** F2, F3
**Priority:** P0 — all content in the PDF comes from this

**What:**
Implement Call 1 to RealEstateAPI.com in `data_fetcher.py`. POST to `/v2/PropertySearch` with `{ "count": true, "summary": true, "zip": "<ZIP>" }`. Extract: medianListingPrice, medianDaysOnMarket, mlsActive, mlsPending, highEquity, vacant, ownerOccupied.

**Acceptance criteria:**
- [ ] Returns a dict with all 7 fields populated
- [ ] Handles HTTP errors with a clear print and `sys.exit(1)`
- [ ] Costs 0 credits (summary endpoint)

**Status: Done**

---

## ISSUE-03 — Data fetcher: recent sales call

**Linked to:** F4
**Priority:** P0 — sales table requires this

**What:**
Implement Call 2 in `data_fetcher.py`. POST with `{ "size": 10, "zip": "<ZIP>", "last_sale_date_min": "<90 days ago>", "last_sale_date_max": "<today>" }`. Extract list of `{ address, saleAmount, saleDate }` from `data[]`.

**Acceptance criteria:**
- [ ] Returns list of up to 10 dicts with address, saleAmount, saleDate
- [ ] Dates calculated dynamically (not hardcoded)
- [ ] Combined with Issue-02 output into a single return dict

**Status: Done**

---

## ISSUE-04 — LLM narrative writer

**Linked to:** F5
**Priority:** P0 — narrative block is a core PDF section

**What:**
Implement `llm_writer.py` using Groq (Llama 3.3 70B) via their OpenAI-compatible REST endpoint. Format a prompt with the market dict and request a 3–4 sentence professional market summary characterising market temperature and advising buyers/sellers.

**Acceptance criteria:**
- [ ] Returns a non-empty string narrative
- [ ] System prompt enforces tone: plain English, no jargon, specific numbers
- [ ] Temperature set to 0.7
- [ ] HTTP errors handled with clear message and exit

**Status: Done** *(Note: Originally built with Gemini, switched to Groq after persistent 403 errors on Google Cloud free tier. No SDK needed — uses `requests` directly against Groq's API.)*

---

## ISSUE-05 — PDF generator: header, title, footer

**Linked to:** F6, NF2
**Priority:** P0 — structural PDF elements

**What:**
Implement `pdf_generator.py` using ReportLab canvas API (not Platypus). Draw on A4 page (595 × 842pt). Implement:
- Navy header bar with "SNAPHOMZ" left, subtitle right, gold accent line below
- ZIP title (28pt navy bold), report date subtitle, horizontal rule
- Navy footer bar with Snaphomz attribution left, data source + generation date right

**Acceptance criteria:**
- [ ] PDF opens without error
- [ ] Header and footer render on the correct position (top/bottom of page)
- [ ] No layout elements overlap
- [ ] Renders identically on Linux and Mac

**Status: Done**

---

## ISSUE-06 — PDF generator: stats grid

**Linked to:** F6 (stats grid)
**Priority:** P1 — key visual element of the report

**What:**
Draw a 2×3 grid of stat cards. Each card: light blue background, navy left accent bar, 3 text lines (label 7pt grey uppercase, value 20pt navy bold, sub-label 7pt grey italic). Cards: Median List Price, Days on Market, Active Listings, Pending Listings, Sold (90d), Owner Occupied %.

**Acceptance criteria:**
- [ ] All 6 cards render with correct values from market data dict
- [ ] Cards are evenly spaced across usable page width
- [ ] Values formatted correctly (prices with $, DOM as decimal, percentages as %)

**Status: Done**

---

## ISSUE-07 — PDF generator: narrative and sales table

**Linked to:** F6 (narrative, sales table)
**Priority:** P1 — content sections

**What:**
- Narrative: Draw text wrapped to usable width with grey left border and light background card
- Sales table: Header row (navy fill, white text), alternating data rows (white / #F3F4F6), max 8 rows, columns: Address | Sale Price | Date

**Acceptance criteria:**
- [ ] Narrative wraps correctly for long text
- [ ] Table header renders in navy
- [ ] Rows alternate correctly
- [ ] No text overflows cell bounds

**Status: Done**

---

## ISSUE-08 — PDF generator: optional agent card

**Linked to:** F11, F12
**Priority:** P2 — stretch feature

**What:**
If agent dict has a non-empty `name`, draw a styled card between the title and stats grid with "PREPARED BY" label, agent name (12pt navy bold), and contact info line (phone | email | company).

**Acceptance criteria:**
- [ ] Card renders if agent name provided
- [ ] Card is skipped entirely if no agent name
- [ ] Contact info only shows non-empty fields

**Status: Done**

---

## ISSUE-09 — CLI entry point

**Linked to:** F1, F10
**Priority:** P0 — required by hackathon spec

**What:**
Implement `main.py` with `argparse`. Required flag: `--zip`. Optional flags: `--output`, `--agent-name`, `--agent-phone`, `--agent-email`, `--agent-company`. Wire all three modules in sequence with progress print statements.

**Acceptance criteria:**
- [ ] `python3 main.py --zip 90210` runs end-to-end and saves PDF
- [ ] Invalid ZIP (non-numeric, wrong length) exits with clear error
- [ ] Agent flags pass through to PDF generator

**Status: Done**

---

## ISSUE-10 — Flask web UI: backend routes

**Linked to:** F7, F8, F9
**Priority:** P0 — required for web demo

**What:**
Implement `app.py` with three routes:
- `GET /` — renders `index.html`
- `POST /generate` — accepts zip + agent fields, runs pipeline, returns PDF as download
- `GET /health` — returns `{ "status": "ok" }`

Handle errors with JSON responses. Use `PORT` env variable for Railway deployment.

**Acceptance criteria:**
- [ ] `/generate` returns a PDF file download on success
- [ ] Returns 400 for invalid ZIP, 500 for pipeline errors with descriptive JSON
- [ ] `PORT` env var respected (defaults to 5000 locally)

**Status: Done**

---

## ISSUE-11 — Web UI: HTML/CSS/JS

**Linked to:** F8, NF5
**Priority:** P0 — visible to judges

**What:**
Build `templates/index.html` with:
- Dark navy card design, gold "SnapReport" heading
- ZIP input (digit-only, 5 chars max)
- Optional agent fields section (checkbox toggle)
- Loading spinner with rotating step messages
- Green download button that appears on success
- Error message display
- Footer attributing Groq and RealEstateAPI

**Acceptance criteria:**
- [ ] UI loads on `localhost:5000`
- [ ] Digit-only enforcement on ZIP field
- [ ] Agent section hidden by default, revealed on checkbox
- [ ] Download button appears after successful generation
- [ ] Footer says "Llama 3.3 70B via Groq" (not Gemini)

**Status: Done**

---

## ISSUE-12 — Deployment

**Linked to:** NF4
**Priority:** P1 — needed for public demo URL

**What:**
Prepare for Railway deployment: add `Procfile` (`web: python app.py`), update `app.run` to use `PORT` env var and `host="0.0.0.0"`, set `debug=False`. Deploy via Railway CLI and set env vars remotely.

**Acceptance criteria:**
- [ ] `railway up` deploys successfully
- [ ] `railway domain` generates a public URL
- [ ] API keys set via `railway variables set`
- [ ] App accessible at public URL and generates PDFs

**Status: Done** — live at https://snapreport-production.up.railway.app

---

## ISSUE-13 — Documentation

**Linked to:** NF3
**Priority:** P2 — polish

**What:**
Write `README.md` covering: what it does, how the pipeline works, tech stack, setup instructions (where to get each key), CLI usage, web usage, deployment steps, key numbers, business case.

**Acceptance criteria:**
- [ ] Someone can clone and run locally following only the README
- [ ] API key sources are clearly documented
- [ ] No secrets in the README

**Status: Done**

---

## Issue Summary

| Issue | Description | Priority | Status |
|---|---|---|---|
| ISSUE-01 | Project scaffold and environment | P0 | Done |
| ISSUE-02 | Data fetcher: market summary | P0 | Done |
| ISSUE-03 | Data fetcher: recent sales | P0 | Done |
| ISSUE-04 | LLM narrative writer | P0 | Done |
| ISSUE-05 | PDF: header, title, footer | P0 | Done |
| ISSUE-06 | PDF: stats grid | P1 | Done |
| ISSUE-07 | PDF: narrative and sales table | P1 | Done |
| ISSUE-08 | PDF: optional agent card | P2 | Done |
| ISSUE-09 | CLI entry point | P0 | Done |
| ISSUE-10 | Flask routes | P0 | Done |
| ISSUE-11 | Web UI | P0 | Done |
| ISSUE-12 | Deployment | P1 | Done |
| ISSUE-13 | Documentation | P2 | Done |

All 13 issues shipped in the hackathon build.
