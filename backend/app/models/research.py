from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FilingMetadata(BaseModel):
    ticker: str
    company: str
    cik: str
    accession: str
    date: str


class ReportRequest(BaseModel):
    ticker: str


class ReportResponse(BaseModel):
    ticker: str
    company: str
    filing_date: str
    report: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    model: str
    generated_at: Optional[str] = None
