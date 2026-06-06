"""
main.py — CLI entry point for SnapReport.
Usage:
  python3 main.py --zip 90210
  python3 main.py --zip 90210 --agent-name "Sarah Chen" --agent-phone "310-555-0190" --agent-email "sarah@realty.com" --agent-company "Premier Realty"
"""

import argparse
import sys
from data_fetcher import fetch_market_data
from llm_writer import generate_narrative
from pdf_generator import generate_pdf


def run(zip_code: str, output_dir: str = "./output", agent: dict = None) -> str:
    """
    Full pipeline: fetch data -> generate narrative -> render PDF.
    Returns the path to the generated PDF.
    """
    print(f"\nSnapReport -- Generating market report for ZIP {zip_code}")
    print("-" * 52)

    print("Fetching data...")
    market_data = fetch_market_data(zip_code)
    print(f"  Median price    : ${market_data['median_price']:,}")
    print(f"  Active listings : {market_data['active_listings']}")
    print(f"  Recent sales    : {len(market_data['recent_sales'])}")

    print("\nWriting narrative...")
    narrative = generate_narrative(market_data)
    print(f"  Narrative generated ({len(narrative)} chars)")

    print("\nGenerating PDF...")
    output_path = generate_pdf(market_data, narrative, output_dir, agent=agent)
    print(f"  Saved: {output_path}")
    print("\n" + "-" * 52)
    print(f"Done. Report saved -> {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="SnapReport -- AI-powered real estate market report generator"
    )
    parser.add_argument("--zip", required=True,
                        help="US ZIP code (e.g. 90210)")
    parser.add_argument("--output", default="./output",
                        help="Output directory (default: ./output)")
    parser.add_argument("--agent-name",    default="", help="Agent full name")
    parser.add_argument("--agent-phone",   default="", help="Agent phone number")
    parser.add_argument("--agent-email",   default="", help="Agent email address")
    parser.add_argument("--agent-company", default="", help="Brokerage / company name")
    args = parser.parse_args()

    if not args.zip.isdigit() or len(args.zip) != 5:
        print("ERROR: Please provide a valid 5-digit US ZIP code.")
        sys.exit(1)

    agent = {
        "name":    args.agent_name,
        "phone":   args.agent_phone,
        "email":   args.agent_email,
        "company": args.agent_company,
    }

    run(args.zip, args.output, agent=agent)


if __name__ == "__main__":
    main()
