"""
Phase 4 — Multi-Agent System
DATA AGENT: Fetches, validates, and structures raw data from all five sources.
First agent to run — all others depend on its output.
"""

from crewai import Agent, Task
from crewai.tools import tool


@tool("market_data_tool")
def get_market_data(ticker: str) -> str:
    """Fetch market price, valuation multiples, short interest, and analyst data for a ticker."""
    import asyncio, json, sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    from data_fetcher import fetch_market_data
    result = asyncio.run(fetch_market_data(ticker))
    return json.dumps(result, default=str, indent=2)


@tool("sec_data_tool")
def get_sec_data(ticker: str) -> str:
    """Fetch SEC EDGAR filings (10-K, 10-Q, 8-K) for a ticker."""
    import asyncio, json, sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    from data_fetcher import fetch_sec_data
    result = asyncio.run(fetch_sec_data(ticker))
    return json.dumps(result, default=str, indent=2)


@tool("trends_tool")
def get_google_trends(company_and_ticker: str) -> str:
    """Fetch Google Trends for a company. Input format: 'CompanyName|TICKER'"""
    import asyncio, json, sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    from data_fetcher import fetch_google_trends
    parts = company_and_ticker.split("|")
    company = parts[0].strip()
    ticker = parts[1].strip() if len(parts) > 1 else company
    result = asyncio.run(fetch_google_trends(company, ticker))
    return json.dumps(result, default=str, indent=2)


@tool("reddit_tool")
def get_reddit_sentiment(company_and_ticker: str) -> str:
    """Fetch Reddit sentiment. Input format: 'TICKER|CompanyName'"""
    import asyncio, json, sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    from data_fetcher import fetch_reddit_sentiment
    parts = company_and_ticker.split("|")
    ticker = parts[0].strip()
    company = parts[1].strip() if len(parts) > 1 else ticker
    result = asyncio.run(fetch_reddit_sentiment(ticker, company))
    return json.dumps(result, default=str, indent=2)


def create_data_agent(llm) -> Agent:
    return Agent(
        role="Senior Data Analyst",
        goal=(
            "Fetch, validate, and structure comprehensive data for the target company "
            "from SEC EDGAR, market data, Google Trends, Reddit, and web intelligence. "
            "Ensure data quality and flag missing or unreliable data."
        ),
        backstory=(
            "You are a data specialist at a $10B hedge fund. You've built data pipelines "
            "for 15 years. You validate every number before passing it downstream. "
            "Wrong inputs lead to wrong investment decisions."
        ),
        tools=[get_market_data, get_sec_data, get_google_trends, get_reddit_sentiment],
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )


def create_data_task(agent: Agent, ticker: str, company: str) -> Task:
    return Task(
        description=f"""
        Fetch and validate all available data for {company} ({ticker}).

        1. Use market_data_tool for price, fundamentals, analyst data
        2. Use sec_data_tool for 10-K, 10-Q, 8-K filing dates
        3. Use trends_tool with input "{company}|{ticker}" for Google Trends
        4. Use reddit_tool with input "{ticker}|{company}" for sentiment

        Output: Structured data package with MARKET_DATA, SEC_DATA, TRENDS_DATA,
        REDDIT_DATA sections. Flag any data quality issues.
        """,
        agent=agent,
        expected_output=(
            "Structured data package with sections: MARKET_DATA, SEC_DATA, "
            "TRENDS_DATA, REDDIT_DATA. Each with availability status and key metrics."
        ),
    )
