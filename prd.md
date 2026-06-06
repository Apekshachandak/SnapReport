# SnapReport — Product Requirements Document

> **Note:** I wrote this PRD before starting to build, as a way to structure my own thinking. I gave the AI the hackathon prompt for Project 10 and invoked the `grill-me` skill to stress-test my understanding of requirements. This document captures what I decided the product must do, must not do, and how success would be measured — before a single line of code was written.

---

## 1. Problem Statement

Real estate agents know they should send a monthly market update to their contact list. Almost none actually do it. The barrier is not motivation — it is time and skill. Producing a professional market report requires:

- Manually pulling data from MLS or public sources (30–60 min)
- Writing a readable market summary (30–60 min)
- Formatting it into a PDF that looks professional (60–90 min)

Total: 3–4 hours per report, per month, per ZIP code. Most agents skip it entirely.

The agents who consistently send market updates out-earn those who don't, because they stay top-of-mind when a homeowner is ready to list.

---

## 2. Goal

Build a tool where a real estate agent types in one ZIP code and gets back a professionally branded PDF market report in under 90 seconds — containing live data, an AI-written narrative, and Snaphomz co-branding — ready to forward to their client list.

---

## 3. Primary User

**Real estate agents and small brokerages** who are active on the Snaphomz platform. They are not technical. They want a simple one-input → one-output tool they can use monthly without thinking about it.

Secondary: the Snaphomz brand itself benefits from co-brand impressions in every PDF that gets sent.

---

## 4. User Story

> As a real estate agent, I want to generate a professional market report for any ZIP code I serve, so that I can send it to my client list every month without spending hours on research and design.

---

## 5. Functional Requirements

### Core (must work at demo time)

| # | Requirement |
|---|---|
| F1 | Accept a 5-digit US ZIP code as input via web UI and CLI |
| F2 | Fetch live market data for that ZIP from RealEstateAPI.com |
| F3 | Extract: median listing price, days on market, active listings, pending listings, owner occupied %, vacant count, high equity count |
| F4 | Fetch up to 10 recent sales (last 90 days): address, sale price, sale date |
| F5 | Generate a 3–4 sentence plain-English market narrative using an LLM |
| F6 | Render a branded PDF with: header, stats grid (6 cards), narrative, sales table, footer |
| F7 | Return PDF as a download within 90 seconds of ZIP input |
| F8 | Web UI: ZIP input form, loading state with spinner, download button on success |
| F9 | Error handling: invalid ZIP, API failure, LLM failure — all show a clear message |
| F10 | CLI mode: `python3 main.py --zip 90210` works end-to-end |

### Agent branding (stretch, added during build)

| # | Requirement |
|---|---|
| F11 | Optional agent name, phone, email, brokerage on the web form |
| F12 | If provided, render an agent info card in the PDF under the title section |
| F13 | CLI flags: `--agent-name`, `--agent-phone`, `--agent-email`, `--agent-company` |

---

## 6. Non-Functional Requirements

| # | Requirement |
|---|---|
| NF1 | Report generation time ≤ 90 seconds end-to-end |
| NF2 | PDF must render identically on any OS (no browser-based rendering) |
| NF3 | API keys must never be committed to source control |
| NF4 | App must be deployable to a public URL with a single command |
| NF5 | No frameworks on the frontend — vanilla HTML/CSS/JS only |
| NF6 | Total cost per report at demo scale: effectively $0 |

---

## 7. Out of Scope (v1)

These were deliberately excluded to focus the build on the core pipeline:

- Email scheduling / SendGrid delivery
- Agent photo upload
- Multi-ZIP batch generation
- Report caching or database
- User authentication
- PDF preview in browser

Each of these is a clear v2 feature — not cut because they're hard, but because proving the pipeline first is the right engineering priority.

---

## 8. Tech Choices (decided before building)

| Decision | Choice | Reason |
|---|---|---|
| Backend language | Python | Clean API integration, ReportLab support |
| Web framework | Flask | Zero boilerplate for single-route demo |
| Data source | RealEstateAPI.com | Developer-first, pay-as-you-go, real MLS data |
| LLM | Groq — Llama 3.3 70B | Free tier, 14,400 req/day, no billing setup |
| PDF library | ReportLab (canvas) | OS-consistent, pixel-precise, no HTML dependency |
| Frontend | Vanilla HTML/CSS/JS | Zero build step, instantly deployable |
| Deployment | Railway | Free tier, CLI deploy, public URL in minutes |

---

## 9. Success Metrics

| Metric | Target |
|---|---|
| ZIP → PDF time | ≤ 90 seconds |
| Summary API call cost | $0 (free endpoint) |
| Works across 3+ test ZIPs | Yes |
| PDF renders cleanly | Yes (no layout breaks) |
| Web UI download works | Yes |
| Deployable to public URL | Yes |

---

## 10. PDF Content Specification

Section order and content:

1. **Header bar** — Navy (#1B3F72), "SNAPHOMZ" left, "Market Intelligence Report" right, gold accent line below
2. **Title** — ZIP code large (28pt), subtitle with report date, horizontal rule
3. **Agent card** (optional) — "PREPARED BY" with name, phone, email, brokerage
4. **Stats grid** — 2 rows × 3 columns: Median List Price · Days on Market · Active Listings · Pending Listings · Sold (90d) · Owner Occupied %
5. **Market overview** — AI narrative with grey left border
6. **Recent sales table** — Address, Sale Price, Date; max 8 rows; alternating row colour
7. **Footer bar** — Navy, "Powered by Snaphomz" left, data attribution + date right
