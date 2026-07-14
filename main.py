#!/usr/bin/env python3
"""AI Data Enrichment Pipeline - CLI Entry Point.

Usage:
  python main.py <file> --enrich <type> --column <col> --output <file>
  python main.py <file> --enrich classify,describe --batch-size 10 --dry-run
"""
import argparse
import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)

from src.core.reader import read_file
from src.core.enricher import Enricher
from src.core.exporter import export_data
from src.core.columns import (
    detect_name_columns,
    detect_text_columns,
    guess_enrichment_type,
)
from src.llm.client import LLMConfig


def main():
    parser = argparse.ArgumentParser(
        description="AI Data Enrichment Pipeline - Enrich CSV/JSON data with AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py companies.csv --enrich classify --column name --output enriched.csv
  python main.py data.json --enrich describe,sentiment --batch-size 10
  python main.py companies.csv --enrich classify --dry-run
  python main.py data.txt --enrich sentiment --output results.json
  python main.py companies.csv --enrich custom --custom-prompt "Classify {name} as tech or non-tech" --output classified.csv
        """,
    )
    parser.add_argument("file", help="Input file (CSV, JSON, or TXT)")
    parser.add_argument(
        "--enrich", "-e",
        default="",
        help="Enrichment type(s): classify, describe, sentiment, extract, custom (comma-separated)",
    )
    parser.add_argument(
        "--column", "-c",
        default="",
        help="Column(s) to enrich (comma-separated). Auto-detected if not specified.",
    )
    parser.add_argument(
        "--output", "-o",
        default="",
        help="Output file path. Auto-named if not specified.",
    )
    parser.add_argument(
        "--batch-size", "-b",
        type=int,
        default=10,
        help="Batch size for parallel processing (default: 10)",
    )
    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=5,
        help="Max concurrent API calls (default: 5)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show estimated cost and columns without running enrichment",
    )
    parser.add_argument(
        "--custom-prompt",
        default="",
        help="Custom prompt template with {column} placeholders",
    )
    parser.add_argument(
        "--api-key",
        default="",
        help="OpenAI API key (or set OPENAI_API_KEY env var)",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="LLM model to use (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--api-base",
        default="https://api.openai.com/v1",
        help="API base URL (default: https://api.openai.com/v1)",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress output",
    )

    args = parser.parse_args()

    # Validate file
    if not os.path.exists(args.file):
        logger.error("File not found: %s", args.file)
        sys.exit(1)

    # Read data
    try:
        rows = read_file(args.file)
    except Exception as e:
        logger.error("Error reading file: %s", e)
        sys.exit(1)

    if not rows:
        logger.error("No data rows found in file")
        sys.exit(1)

    headers = list(rows[0].keys())
    logger.info("Loaded %d rows with columns: %s", len(rows), ", ".join(headers))

    # Determine enrichment types
    enrichment_types = []
    if args.enrich:
        enrichment_types = [e.strip() for e in args.enrich.split(",")]
    else:
        enrichment_types = guess_enrichment_type(headers)
        logger.info("Auto-detected enrichment types: %s", ", ".join(enrichment_types))

    # Determine columns
    columns = []
    if args.column:
        columns = [c.strip() for c in args.column.split(",")]
    else:
        name_cols = detect_name_columns(headers)
        text_cols = detect_text_columns(headers)
        for etype in enrichment_types:
            if etype in ("sentiment", "extract"):
                columns.extend(text_cols)
            else:
                columns.extend(name_cols)
        columns = list(dict.fromkeys(columns))  # deduplicate, preserve order
        if not columns:
            columns = [headers[0]]
        logger.info("Auto-detected columns: %s", ", ".join(columns))

    # Setup LLM config
    llm_config = LLMConfig(
        api_key=args.api_key or os.environ.get("OPENAI_API_KEY", ""),
        model=args.model,
        base_url=args.api_base,
    )

    enricher = Enricher(llm_config=llm_config)

    # Estimate cost
    estimate = enricher.estimate_total_cost(rows, enrichment_types, columns)
    logger.info(
        "Cost Estimate — Rows: %d, Enrichments: %d (per row), "
        "Est. input tokens: %s, Est. output tokens: %s, Est. total cost: $%.6f",
        estimate["rows"],
        estimate["enrichments"],
        f"{estimate['estimated_input_tokens']:,}",
        f"{estimate['estimated_output_tokens']:,}",
        estimate["estimated_total_cost"],
    )

    if args.dry_run:
        logger.info("Dry run complete. No enrichment performed.")
        return

    # Determine output path
    output_path = args.output
    if not output_path:
        base = os.path.splitext(args.file)[0]
        ext = "csv"
        output_path = f"{base}_enriched.{ext}"
    else:
        if not os.path.splitext(output_path)[1]:
            output_path += ".csv"

    # Determine output format
    out_ext = os.path.splitext(output_path)[1].lower().lstrip(".")
    out_fmt = out_ext if out_ext in ("csv", "json", "xlsx") else "csv"

    # Run enrichment
    logger.info("Running enrichment...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        enriched = loop.run_until_complete(
            enricher.enrich_batch(
                rows,
                enrichment_types,
                columns,
                batch_size=args.batch_size,
                max_concurrency=args.max_concurrency,
                show_progress=not args.quiet,
                custom_template=args.custom_prompt if args.custom_prompt else None,
            )
        )
    finally:
        loop.close()

    # Export results
    output_file = export_data(enriched, output_path, fmt=out_fmt)
    success_count = len([r for r in enriched if "_error" not in r])
    fail_count = len([r for r in enriched if "_error" in r])

    logger.info(
        "Enrichment complete! Successfully enriched: %d rows, Failed: %d rows, Output: %s",
        success_count,
        fail_count,
        os.path.abspath(output_file),
    )

    # Show usage summary
    usage = enricher.llm.get_usage()
    if usage["total_tokens"] > 0:
        logger.info(
            "Tokens used: %s (%s prompt + %s completion)",
            f"{usage['total_tokens']:,}",
            f"{usage['prompt_tokens']:,}",
            f"{usage['completion_tokens']:,}",
        )


if __name__ == "__main__":
    main()
