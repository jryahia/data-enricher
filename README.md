# AI Data Enricher

**Enrichment pipeline that reads CSV, JSON or text files, enriches each row with AI (classify, describe, sentiment, extract, translate) and exports CSV, JSON or Excel.**

![Python](https://img.shields.io/badge/Python-161b22?style=for-the-badge&labelColor=161b22&color=161b22) ![FastAPI](https://img.shields.io/badge/FastAPI-161b22?style=for-the-badge&labelColor=161b22&color=161b22) ![OpenAI](https://img.shields.io/badge/OpenAI-161b22?style=for-the-badge&labelColor=161b22&color=161b22) ![pandas](https://img.shields.io/badge/pandas-161b22?style=for-the-badge&labelColor=161b22&color=161b22) ![Docker](https://img.shields.io/badge/Docker-161b22?style=for-the-badge&labelColor=161b22&color=161b22)

```mermaid
flowchart LR
    S0["CSV / JSON / text upload"]
    S1["Column detection"]
    S2["Batched AI enrichment"]
    S3["Progress + cost estimate"]
    S4["CSV / JSON / Excel export"]
    S0 --> S1 --> S2 --> S3 --> S4
```

## Problem it solves

Enriching thousands of rows by hand, or with one-off scripts, is slow and costs are unpredictable. This pipeline batches the work, estimates cost before running and exports clean files.

A powerful AI-powered data enrichment pipeline that reads CSV/JSON/text files, enriches each row using AI (classification, description, sentiment analysis, entity extraction, custom prompts), and exports the enriched data.

## Features

- **Multiple file formats**: CSV, JSON, and plain text
- **6 enrichment types**: Classify, Describe, Sentiment, Extract, Translate, Custom Prompt
- **Auto column detection**: Automatically finds the right columns to enrich
- **Batch processing**: Process rows in parallel with configurable batch size
- **Progress tracking**: See X/Y rows processed with ETA
- **Multiple export formats**: CSV, JSON, Excel (.xlsx)
- **Cost estimation**: Know the cost before you run
- **CLI & API**: Use from command line or as a web service
- **Web UI**: Simple browser-based upload interface
- **Docker support**: Run anywhere with containerization

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

Set your OpenAI API key:

```bash
export OPENAI_API_KEY="sk-..."
```

### CLI Usage

```bash
# Classify companies by name
python main.py examples/companies.csv --enrich classify --column name --output enriched.csv

# Multiple enrichment types
python main.py examples/companies.csv --enrich describe,sentiment --column name,description --batch-size 10

# Dry run (estimate cost without running)
python main.py examples/companies.csv --enrich classify --column name --dry-run

# Custom prompt
python main.py examples/companies.csv --enrich custom --custom-prompt "Summarize the business {name} in one word" --output summary.csv

# JSON input
python main.py examples/products.json --enrich describe --column title --output enriched.json
```

### API Server

```bash
# Start the server
python api.py

# Open web UI: http://localhost:8000

# Upload and enrich via API
curl -X POST http://localhost:8000/enrich \
  -F "file=@examples/companies.csv" \
  -F "enrichment_type=classify" \
  -F "columns=name"

# Check job status
curl http://localhost:8000/jobs/<job_id>

# Download enriched file
curl http://localhost:8000/jobs/<job_id>/download
```

### Docker

```bash
docker-compose up -d
```

## Enrichment Types

| Type | Description | Example Output |
|------|-------------|---------------|
| `classify` | Assign category/tag | `Technology`, `Healthcare` |
| `describe` | Generate AI description | `A leading AI company...` |
| `sentiment` | Analyze sentiment | `positive`, `negative`, `neutral` |
| `extract` | Extract entities | `{"companies": [...], "people": [...]}` |
| `custom` | User-defined prompt | Based on your template |

## Project Structure

```
data-enricher/
├── main.py              # CLI entry point
├── api.py               # API server entry point
├── requirements.txt     # Python dependencies
├── Dockerfile
├── docker-compose.yml
├── README.md
├── src/
│   ├── core/
│   │   ├── reader.py    # File reading
│   │   ├── enricher.py  # Enrichment engine
│   │   ├── batcher.py   # Batch processing
│   │   ├── exporter.py  # Export functions
│   │   └── columns.py   # Column detection
│   ├── llm/
│   │   └── client.py    # LLM API client
│   ├── prompts/         # Prompt templates
│   ├── server/          # FastAPI server
│   └── ui/              # Web interface
├── tests/               # Unit tests
└── examples/            # Sample data files
```

## License

MIT
