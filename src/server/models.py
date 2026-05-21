"""Pydantic models for the API."""
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict


class EnrichRequest(BaseModel):
    """Request body for the /enrich endpoint."""
    enrichment_type: str = Field(..., description="Type of enrichment: classify, describe, sentiment, extract, translate, custom")
    columns: List[str] = Field(default_factory=list, description="Columns to enrich")
    batch_size: int = Field(default=10, ge=1, le=100, description="Batch size for processing")
    custom_prompt: Optional[str] = Field(None, description="Custom prompt template with {column} placeholders")
    output_format: str = Field(default="csv", description="Output format: csv, json, xlsx")


class EnrichResponse(BaseModel):
    """Response from an enrichment job."""
    job_id: str
    status: str = "queued"
    message: str = ""


class JobStatus(BaseModel):
    """Status of a job."""
    job_id: str
    status: str
    total_rows: int = 0
    processed_rows: int = 0
    failed_rows: int = 0
    output_file: Optional[str] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
