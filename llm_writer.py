"""
llm_writer.py — Groq (Llama 3.3 70B) narrative generator for SnapReport.
Converts raw market data into a professional plain-English market narrative.
Free tier: 14,400 requests/day. No credit card required.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


def generate_narrative(market_data: dict) -> str:
    """
    Use Groq (Llama 3.3 70B) to write a professional market narrative
    from the structured market data dict.
    """
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not found in environment variables. Check your .env file.")

    # Strongly-constrained system prompt: only summarize provided numbers.
    system_message = (
        "You are a senior real estate market analyst. Write a professional, "
        "plain-English market narrative (3-4 sentences) strictly based on the numbers "
        "provided in the user message. Do NOT invent facts, predictions, or external "
        "information. Use the exact numeric values given when mentioning statistics."
    )

    user_message = (
        f"Generate a market summary for ZIP {market_data['zip']} as of {market_data['report_date']}. "
        f"Median listing price: ${market_data['median_price']:,}. "
        f"Average days on market: {market_data['days_on_market']}. "
        f"Active listings: {market_data['active_listings']}, Pending: {market_data['pending_listings']}. "
        f"{len(market_data['recent_sales'])} properties sold in the past 90 days. "
        f"Only use the numbers above; characterise market temperature (hot/balanced/cool) and "
        f"give concise advice for sellers and buyers in 3-4 sentences."
    )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user",   "content": user_message},
        ],
        # Low temperature to reduce hallucination
        "temperature": 0.0,
        "max_tokens": 256,
    }

    def _fallback_template(md: dict) -> str:
        return (
            f"As of {md['report_date']} in ZIP {md['zip']}, the median listing price is ${md['median_price']:,}. "
            f"Average days on market: {md['days_on_market']}. Active listings: {md['active_listings']}. "
            f"In the past 90 days {len(md['recent_sales'])} properties sold. "
            f"Contact your local agent for tailored advice."
        )

    # If API key missing, immediately return fallback template (don't exit)
    if not GROQ_API_KEY:
        print("[LLM] GROQ_API_KEY missing — using template narrative.")
        return _fallback_template(market_data)

    try:
        resp = requests.post(GROQ_URL, headers=headers, json=body, timeout=20)
        resp.raise_for_status()
        narrative = resp.json()["choices"][0]["message"]["content"].strip()

        # Simple validation: ensure key numeric tokens appear in the narrative
        checks = []
        checks.append(f"{market_data['median_price']:,}")
        checks.append(str(market_data['active_listings']))
        checks.append(str(market_data['days_on_market']))

        valid = any(token in narrative for token in checks)
        if not valid:
            print("[LLM] Validation failed — narrative does not include expected numeric tokens. Falling back to template.")
            return _fallback_template(market_data)

        return narrative
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Groq call failed -- {e}")
        return _fallback_template(market_data)
    except Exception as e:
        print(f"ERROR: Unexpected error in LLM generation -- {e}")
        return _fallback_template(market_data)

