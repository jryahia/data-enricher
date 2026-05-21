"""Job queue management with SQLite."""
import json
import os
import uuid
import time
import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field


DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "jobs.db")


@dataclass
class Job:
    """Represents an enrichment job."""
    job_id: str
    status: str = "queued"  # queued, running, completed, failed
    enrichment_type: str = ""
    columns: str = ""  # JSON list
    input_file: str = ""
    output_file: str = ""
    output_format: str = "csv"
    total_rows: int = 0
    processed_rows: int = 0
    failed_rows: int = 0
    error: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: str = ""
    custom_prompt: str = ""


class JobManager:
    """Manages jobs using SQLite."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                status TEXT DEFAULT 'queued',
                enrichment_type TEXT,
                columns TEXT,
                input_file TEXT,
                output_file TEXT,
                output_format TEXT DEFAULT 'csv',
                total_rows INTEGER DEFAULT 0,
                processed_rows INTEGER DEFAULT 0,
                failed_rows INTEGER DEFAULT 0,
                error TEXT,
                created_at TEXT,
                completed_at TEXT,
                custom_prompt TEXT
            )
        """)
        conn.commit()
        conn.close()

    def create_job(
        self,
        enrichment_type: str,
        columns: List[str],
        input_file: str,
        output_format: str = "csv",
        total_rows: int = 0,
        custom_prompt: str = "",
    ) -> Job:
        """Create a new job and return it."""
        job_id = str(uuid.uuid4())[:8]
        job = Job(
            job_id=job_id,
            enrichment_type=enrichment_type,
            columns=json.dumps(columns),
            input_file=input_file,
            output_format=output_format,
            total_rows=total_rows,
            custom_prompt=custom_prompt,
        )
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """INSERT INTO jobs (job_id, status, enrichment_type, columns, input_file,
               output_format, total_rows, created_at, custom_prompt)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (job.job_id, job.status, job.enrichment_type, job.columns,
             job.input_file, job.output_format, job.total_rows, job.created_at, job.custom_prompt),
        )
        conn.commit()
        conn.close()
        return job

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a job by ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None

    def update_job(self, job_id: str, **kwargs):
        """Update job fields."""
        allowed = {"status", "processed_rows", "failed_rows", "error", "output_file", "completed_at"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [job_id]
        conn = sqlite3.connect(self.db_path)
        conn.execute(f"UPDATE jobs SET {set_clause} WHERE job_id = ?", values)
        conn.commit()
        conn.close()

    def list_jobs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent jobs."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
