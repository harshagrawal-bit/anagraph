from fastapi import APIRouter, HTTPException

from app.models.research import ReportRequest, ReportResponse
from app.services.edgar import fetch_10k
from app.services.report_generator import generate_report

router = APIRouter()


@router.post("/report", response_model=ReportResponse, summary="Generate research report")
async def create_report(req: ReportRequest):
    """
    Pull the latest 10-K for a ticker from SEC EDGAR and generate a
    fully-cited equity research memo using Claude.
    """
    ticker = req.ticker.upper().strip()
    try:
        text, filing = await fetch_10k(ticker)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"EDGAR fetch failed: {e}")

    try:
        result = generate_report(text, filing)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {e}")

    return result


@router.get("/report/{ticker}", response_model=ReportResponse, summary="Generate report by ticker")
async def get_report(ticker: str):
    """GET convenience endpoint — same pipeline as POST /report."""
    ticker = ticker.upper().strip()
    try:
        text, filing = await fetch_10k(ticker)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"EDGAR fetch failed: {e}")

    try:
        result = generate_report(text, filing)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {e}")

    return result
