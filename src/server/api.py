"""FastAPI server for the enrichment pipeline."""
import os
import json
import asyncio
import shutil
import tempfile
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.server.models import EnrichRequest, EnrichResponse, JobStatus
from src.server.jobs import JobManager
from src.core.reader import read_file
from src.core.enricher import Enricher
from src.core.exporter import export_data
from src.core.columns import detect_name_columns, detect_text_columns
from src.llm.client import LLMConfig

app = FastAPI(title="Data Enricher API", version="1.0.0")
job_manager = JobManager()
enricher = Enricher()

# Ensure upload directory exists
UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

OUTPUT_DIR = Path(__file__).parent.parent.parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


def get_file_extension(filename: str) -> str:
    return Path(filename).suffix.lower().lstrip(".") or "csv"


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the web UI."""
    ui_path = Path(__file__).parent.parent / "ui" / "templates" / "index.html"
    if ui_path.exists():
        return ui_path.read_text(encoding="utf-8")
    return HTMLResponse("<h1>Data Enricher API</h1><p>UI template not found.</p>")


@app.post("/enrich", response_model=EnrichResponse)
async def enrich_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    enrichment_type: str = Form("classify"),
    columns: Optional[str] = Form(None),
    batch_size: int = Form(10),
    output_format: str = Form("csv"),
    custom_prompt: Optional[str] = Form(None),
):
    """Upload a file and start enrichment."""
    # Save uploaded file
    ext = get_file_extension(file.filename or "data.csv")
    input_path = UPLOAD_DIR / f"{os.urandom(4).hex()}_{file.filename or 'data'}"
    with open(input_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Read data
    try:
        rows = read_file(input_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")

    if not rows:
        raise HTTPException(status_code=400, detail="File contains no data rows")

    # Parse columns
    col_list = []
    if columns:
        col_list = [c.strip() for c in columns.split(",")]
    else:
        headers = list(rows[0].keys())
        if enrichment_type in ("sentiment", "extract"):
            col_list = detect_text_columns(headers)
        else:
            col_list = detect_name_columns(headers)
        if not col_list:
            col_list = [headers[0]]

    # Create job
    job = job_manager.create_job(
        enrichment_type=enrichment_type,
        columns=col_list,
        input_file=str(input_path),
        output_format=output_format,
        total_rows=len(rows),
        custom_prompt=custom_prompt or "",
    )

    # Start background processing
    background_tasks.add_task(
        process_job, job.job_id, rows, enrichment_type, col_list,
        batch_size, output_format, custom_prompt
    )

    return EnrichResponse(
        job_id=job.job_id,
        status="queued",
        message=f"Job {job.job_id} created for {len(rows)} rows. Enrichment: {enrichment_type} on columns: {col_list}",
    )


async def process_job(
    job_id: str,
    rows: list,
    enrichment_type: str,
    columns: list,
    batch_size: int,
    output_format: str,
    custom_prompt: Optional[str] = None,
):
    """Process an enrichment job in the background."""
    try:
        job_manager.update_job(job_id, status="running")

        etypes = [e.strip() for e in enrichment_type.split(",")]
        enriched = await enricher.enrich_batch(
            rows, etypes, columns,
            batch_size=batch_size,
            show_progress=False,
            custom_template=custom_prompt,
        )

        # Export results
        output_path = OUTPUT_DIR / f"{job_id}_enriched.{output_format}"
        export_data(enriched, str(output_path), fmt=output_format)

        job_manager.update_job(
            job_id,
            status="completed",
            processed_rows=len([r for r in enriched if "_error" not in r]),
            failed_rows=len([r for r in enriched if "_error" in r]),
            output_file=str(output_path),
            completed_at=datetime.utcnow().isoformat(),
        )
    except Exception as e:
        job_manager.update_job(
            job_id,
            status="failed",
            error=str(e),
            completed_at=datetime.utcnow().isoformat(),
        )


@app.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get the status of a job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatus(
        job_id=job["job_id"],
        status=job["status"],
        total_rows=job["total_rows"],
        processed_rows=job["processed_rows"],
        failed_rows=job["failed_rows"],
        output_file=job["output_file"],
        error=job["error"],
        created_at=job["created_at"],
        completed_at=job["completed_at"],
    )


@app.get("/jobs/{job_id}/download")
async def download_job(job_id: str):
    """Download the enriched output file."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not yet completed")
    output_path = job["output_file"]
    if not output_path or not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Output file not found")
    return FileResponse(
        output_path,
        filename=f"enriched_{job_id}.{Path(output_path).suffix}",
        media_type="application/octet-stream",
    )


@app.get("/jobs")
async def list_jobs(limit: int = 20):
    """List recent jobs."""
    jobs = job_manager.list_jobs(limit=limit)
    return {"jobs": jobs}


@app.post("/enrich/dry-run")
async def dry_run(
    file: UploadFile = File(...),
    enrichment_type: str = Form("classify"),
    columns: Optional[str] = Form(None),
):
    """Estimate cost without running enrichment."""
    # Save uploaded file
    ext = get_file_extension(file.filename or "data.csv")
    input_path = UPLOAD_DIR / f"dry_{os.urandom(4).hex()}_{file.filename or 'data'}"
    with open(input_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        rows = read_file(input_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")

    col_list = []
    if columns:
        col_list = [c.strip() for c in columns.split(",")]
    else:
        headers = list(rows[0].keys())
        if enrichment_type in ("sentiment", "extract"):
            col_list = detect_text_columns(headers)
        else:
            col_list = detect_name_columns(headers)
        if not col_list:
            col_list = [headers[0]]

    etypes = [e.strip() for e in enrichment_type.split(",")]
    estimate = enricher.estimate_total_cost(rows, etypes, col_list)
    return {
        "rows": len(rows),
        "columns": col_list,
        "enrichment_types": etypes,
        "estimates": estimate,
    }
