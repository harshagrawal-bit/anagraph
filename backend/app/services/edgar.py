"""
SEC EDGAR data service.
Fetches 10-K filings using SEC's public EDGAR API.
No API key required — SEC requires a User-Agent header with contact info.
"""

import re
import httpx
from bs4 import BeautifulSoup

from app.core.config import settings
from app.models.research import FilingMetadata

EDGAR_BASE = "https://data.sec.gov"
EDGAR_ARCHIVES = "https://www.sec.gov/Archives/edgar/data"

HEADERS = {"User-Agent": settings.SEC_USER_AGENT}


async def get_cik(ticker: str) -> str:
    """Resolve a ticker symbol to its SEC CIK (10-digit zero-padded)."""
    url = "https://www.sec.gov/files/company_tickers.json"
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(url, headers=HEADERS)
        r.raise_for_status()
        data = r.json()

    ticker_upper = ticker.upper()
    for entry in data.values():
        if entry["ticker"] == ticker_upper:
            return str(entry["cik_str"]).zfill(10)

    raise ValueError(f"Ticker '{ticker}' not found in SEC EDGAR. Check the symbol.")


async def get_latest_10k(cik: str) -> FilingMetadata:
    """Return metadata for the most recent 10-K filing for the given CIK."""
    url = f"{EDGAR_BASE}/submissions/CIK{cik}.json"
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(url, headers=HEADERS)
        r.raise_for_status()
        data = r.json()

    filings = data["filings"]["recent"]
    forms = filings["form"]
    accessions = filings["accessionNumber"]
    dates = filings["filingDate"]
    company_name = data["name"]

    for i, form in enumerate(forms):
        if form == "10-K":
            return FilingMetadata(
                ticker="",  # caller fills this in
                company=company_name,
                cik=cik,
                accession=accessions[i].replace("-", ""),
                date=dates[i],
            )

    raise ValueError(f"No 10-K filing found for CIK {cik}")


def _accession_with_dashes(accession: str) -> str:
    """Convert 18-char bare accession to the dashed format (XXXXXXXXXX-YY-NNNNNN)."""
    return f"{accession[:10]}-{accession[10:12]}-{accession[12:]}"


async def _get_primary_doc_url(cik: str, accession: str) -> str:
    """Get the URL of the primary 10-K document using the EDGAR filing index HTML."""
    cik_int = int(cik)
    acc_dashed = _accession_with_dashes(accession)

    # The index HTML has a table with document type, filename, and description
    idx_url = (
        f"https://www.sec.gov/Archives/edgar/data/{cik_int}"
        f"/{accession}/{acc_dashed}-index.html"
    )

    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(idx_url, headers=HEADERS)
        r.raise_for_status()

    soup = BeautifulSoup(r.text, "lxml")

    # The index table has columns: Seq, Description, Document, Type, Size
    for row in soup.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 4:
            continue
        doc_type = cells[3].get_text(strip=True)
        if doc_type == "10-K":
            link = cells[2].find("a", href=True)
            if link:
                href = link["href"]
                # href may be relative or absolute
                if href.startswith("/"):
                    return f"https://www.sec.gov{href}"
                return href

    raise ValueError(f"Primary 10-K document not found in filing index: {idx_url}")


def _clean_html(html: str) -> str:
    """Strip HTML/XBRL tags and normalize whitespace, preserving structure."""
    # Use html.parser — lxml mishandles inline XBRL namespaces common in SEC filings
    soup = BeautifulSoup(html, "html.parser")

    # Remove non-content blocks (XBRL hidden section, scripts, styles)
    for tag in soup(["script", "style", "head", "ix:header", "ix:hidden"]):
        tag.decompose()

    text = soup.get_text(separator=" ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


async def download_10k_text(cik: str, accession: str) -> str:
    """Download the 10-K filing and return clean plain text."""
    doc_url = await _get_primary_doc_url(cik, accession)

    # The EDGAR filing index often links to the inline XBRL viewer (/ix?doc=...)
    # which requires JavaScript. Strip the wrapper to get the raw document URL.
    if "/ix?doc=" in doc_url:
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(doc_url)
        doc_path = parse_qs(parsed.query).get("doc", [None])[0]
        if doc_path:
            doc_url = f"https://www.sec.gov{doc_path}"

    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        r = await client.get(doc_url, headers=HEADERS)
        r.raise_for_status()
        return _clean_html(r.text)


async def fetch_10k(ticker: str) -> tuple[str, FilingMetadata]:
    """
    Full pipeline: ticker symbol → (plain-text 10-K, filing metadata).
    This is the main entry point for the EDGAR service.
    """
    cik = await get_cik(ticker)
    filing = await get_latest_10k(cik)
    filing.ticker = ticker.upper()
    text = await download_10k_text(cik, filing.accession)
    return text, filing
