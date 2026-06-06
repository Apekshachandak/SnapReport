# SnapReport — Grilled Design Decisions and Answers

> **Context:** This document was created as a brainstorming and planning exercise *before* any code was written. I gave the AI assistant the initial project brief — the hackathon prompt for Project 10 (SnapReport) from the Snaphomz Hackathon 2.0 project menu — and then invoked a structured design-grilling skill to stress-test my thinking on every major decision before starting to build. The AI asked the questions; I answered them. The goal was to surface blind spots, lock down tech choices, and clarify scope so the actual build hour could be focused and confident. The answers below reflect my reasoning at that pre-build stage.


1) What exactly are we building, who is the primary user, and what are the top 3 success metrics?

- Recommended: Build a web service that generates professional market report PDFs from a ZIP code for real estate agents. Metrics: (1) report generation time <= 90s, (2) report accuracy (numbers match source), (3) agent adoption / repeat usage.

- My answer: I'm building SnapReport to let busy real estate agents produce polished monthly market PDFs without manual data gathering — they enter a ZIP, get a branded PDF. Our primary users are local agents and small brokerages. We'll judge success by keeping generation fast (under 90 seconds), ensuring the numbers and narrative faithfully reflect the data source, and getting agents to reuse the tool month after month as part of their client outreach.

2) What APIs and credentials are required, and what are the rate/credit constraints?

- Recommended: Use `REAPI_KEY` for RealEstateAPI (summary free, property search uses credits) and `GROQ_API_KEY` for Groq Llama 3.3 (14,400 req/day free tier). Track quotas and set timeouts.

- My answer: We rely on RealEstateAPI for authoritative market numbers and Groq for the narrative. I've put both keys into a `.env` for the hackathon. RealEstateAPI’s summary endpoint is free so we only call the property search sparingly; Groq gives us a generous free quota, but we still need to be mindful of spikes — sensible timeouts and per-ZIP caching should keep costs low.

3) Synchronous vs asynchronous report generation — which UX do we pick?

- Recommended: Keep synchronous for MVP only if latency is reliably <= 90s with caching; otherwise implement background jobs and delivery links/email.

- My answer: For the hackathon MVP I kept it synchronous so agents wait on a single screen and download immediately — that’s simplest and works given our average pipeline times. For production I'd switch to background jobs (Celery/RQ) with status indicators and email/download links to improve reliability and scalability.

4) How do we ensure numeric accuracy and avoid LLM hallucination?

- Recommended: Treat RealEstateAPI as source of truth, constrain the LLM prompt to only use provided numbers, set low temperature, validate generated narrative for presence of key numeric tokens, and fall back to a template if validation fails.

- My answer: The numbers always come from RealEstateAPI. I tightened the prompt so the model can only summarize the passed metrics, lowered temperature to reduce creative output, and added a quick validation check — if the narrative doesn’t include expected tokens we use a deterministic template so agents still receive an accurate report.

5) Should we add caching and what level (MVP vs production)?

- Recommended: MVP — local filesystem per-ZIP cache with 24h TTL; Production — Redis for fast TTL caching + S3 for persistent fallback PDFs.

- My answer: For now I implemented a simple filesystem cache per ZIP (24 hours) so repeat requests don't hit APIs and complete much faster. In production we'd use Redis for quick lookups and S3 to persist generated PDFs as a fallback and for distribution.

6) What happens when an external API fails or returns partial data?

- Recommended: Surface the failure to the user, use cached data if available, and fall back to template narrative if LLM fails; log the error for operators.

- My answer: If RealEstateAPI is down we try to serve cached market data and tell the agent when data is older than 24 hours. If the LLM errors or produces invalid output we render a template summary using the raw numbers so the agent still gets a correct, complete PDF. All failures are logged for debugging.

7) What validation rules should run on fetched market data?

- Recommended: Range checks (median price > 0), consistency checks (active + pending <= some max sanity threshold), and non-empty recent sales structure; reject obviously bogus values and surface warnings.

- My answer: I'll run simple sanity checks — median price must be positive and within a reasonable range, days-on-market should be non-negative, and recent sales should be an array. If anything looks off we either fall back to cache or show a clear warning in the generated PDF so the agent knows to verify.

8) What logging, monitoring, and alerting do we add for production readiness?

- Recommended: Request/response logging (no secrets), error reports, request latency metrics, API quota monitoring, and basic alerting for repeated failures or high error rates.

- My answer: For MVP we log to stdout and a local file; for production we should push structured logs to a centralized system (e.g., Datadog/ELK), track pipeline latency, LLM failure rates, and RealEstateAPI quota usage, and set alerts for spikes in failures or long tail latencies.

9) How do we handle secrets and API keys in deployment?

- Recommended: Use environment variables and a secrets manager (HashiCorp Vault / cloud KMS) in production; never commit keys to source control and document required env vars in README.

- My answer: Locally I use a `.env` loaded by `python-dotenv`, but in production I would put `REAPI_KEY` and `GROQ_API_KEY` in cloud secret storage and ensure the deployment system injects them at runtime — no keys in git, and access is role-limited.

10) What are the main scalability bottlenecks and how to address them?

- Recommended: LLM latency and API rate limits; mitigations: caching, batching, background jobs, autoscaling workers, and request queuing.

- My answer: The LLM call and property-search API are the slow/expensive parts. We mitigate by caching per ZIP, queuing longer requests, moving to asynchronous workers for heavy loads, and horizontally scaling worker instances behind a job queue in production.

11) Where do we store generated PDFs and how are they served?

- Recommended: MVP — local filesystem; Production — S3 (or object storage) with time-limited signed URLs for download.

- My answer: For the hackathon everything lives on disk under `snapreport/output/` and we send the file directly. In production I'd upload PDFs to S3 and serve signed URLs so we can offload bandwidth and revoke access if needed.

12) What testing strategy should we use before shipping?

- Recommended: Unit tests for data parsing and validation, integration tests that mock external APIs, and end-to-end smoke tests for report generation; add CI to run tests on PRs.

- My answer: I'll start with unit tests around `data_fetcher` parsing and `llm_writer` fallback behavior, add an integration test that mocks RealEstateAPI and Groq, and configure GitHub Actions to run these tests on every commit so we don't regress critical behavior.

13) How will we measure agent adoption and retention?

- Recommended: Track number of unique agents, repeat report generation per agent, and open/download rates; add simple analytics events and periodic review.

- My answer: Initially I'll add lightweight event logging (report_generated with agent identifier) and aggregate reuse over 7/30/90-day windows. Adoption looks like frequent repeat reports per agent, so we'll prioritize features that improve repeat usage.

14) What privacy or compliance concerns should we consider?

- Recommended: Avoid storing PII unnecessarily, secure agent contact info, provide a retention policy, and verify local laws (e.g., CCPA/GDPR) if operating in regulated regions.

- My answer: We only store minimal agent contact information for report branding; in production I'd document a retention policy, secure storage with encryption, and consider a consent flow before saving or reusing client data. If we expand internationally we'll consult legal for data protection rules.

15) What is the go-to-market / business model for SnapReport?

- Recommended: Freemium for low-volume agents, paid subscriptions for higher usage / team features, and white-labeling for brokerages.

- My answer: I'd launch with a free tier for single agents generating a few reports per month to build traction, then offer paid subscriptions for heavier users and broker-level features like team accounts and branded templates. Our initial focus is adoption and retention rather than monetization.

16) How should we handle upgrades, CI/CD and deployment?

- Recommended: Use Docker images, CI builds for tests, push to registry, and automated deploys; staging environment for smoke testing before production.

- My answer: I containerized the app for easy deploys. I'll add CI to run tests, build the Docker image, and push to a registry; deployments should go to a staging environment for smoke tests and then to production with blue/green or rolling updates.

17) What are key UX improvements to prioritize after the MVP?

- Recommended: Background job UX with status pages, email delivery, scheduled recurring reports, customizable templates, and agent analytics dashboard.

- My answer: After proving the core flow, I'd add scheduled monthly reporting, a job queue with a status page so agents can request many ZIPs, and a simple dashboard showing generated reports and engagement metrics — these features will make SnapReport part of agents' monthly routines.


