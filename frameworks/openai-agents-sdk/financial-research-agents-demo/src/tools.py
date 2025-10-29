"""
Tool implementations for the Financial Research Agent System.

This module defines all the function tools that agents can use to:
- Search for financial information
- Analyze company financials
- Assess risks
- Gather market data
"""

from typing import Optional, Dict, Any, List
from agents import function_tool, RunContextWrapper
from .context import FinancialResearchContext
import random
from datetime import datetime


@function_tool(
    name_override="web_search_tool",
    description_override="Search the web for financial information, company data, and market analysis"
)
async def web_search_tool(query: str) -> str:
    """
    Search for financial information on the web.

    This is a mock implementation for testing. In production, this would
    integrate with a real search API (Google, Bing, etc.).

    Args:
        query: Search query string

    Returns:
        str: Search results summary
    """
    # Mock search results based on query keywords
    results = []

    if "apple" in query.lower():
        results.append("Apple Inc. (AAPL) Q4 2024 Results: Revenue $89.5B, up 6% YoY. iPhone sales strong in emerging markets. Services revenue reached $22.3B.")
        results.append("Apple's AI strategy focuses on on-device processing with new M4 chip capabilities.")
    elif "tesla" in query.lower():
        results.append("Tesla (TSLA) deliveries reached 1.8M vehicles in 2024. Cybertruck production ramping up.")
        results.append("Tesla's energy storage business grew 150% YoY to $6B revenue.")
    elif "ai semiconductor" in query.lower() or "ai chip" in query.lower():
        results.append("AI semiconductor market projected to reach $150B by 2027, growing at 35% CAGR.")
        results.append("NVIDIA maintains 80% market share in AI training chips. AMD gaining ground in inference.")
    elif "market trend" in query.lower():
        results.append("Tech sector shows resilience despite rate hike concerns. Cloud computing and AI driving growth.")
        results.append("Semiconductor supply chain normalizing after 2-year shortage.")
    else:
        results.append(f"Search results for '{query}': Multiple sources indicate positive market sentiment and growth trajectory.")
        results.append(f"Recent analysis suggests strong fundamentals and favorable industry dynamics.")

    # Format results
    formatted_results = "\n\n".join([f"• {result}" for result in results])
    return f"Search Results for '{query}':\n\n{formatted_results}\n\nSource: Mock Financial Data (Generated: {datetime.now().strftime('%Y-%m-%d')})"


@function_tool(
    name_override="company_financials_tool",
    description_override="Analyze company financial metrics including revenue, profit margins, cash flow, and growth rates"
)
async def company_financials_tool(
    context: RunContextWrapper[FinancialResearchContext],
    company_name: str
) -> str:
    """
    Analyze a company's financial metrics.

    Mock implementation that generates realistic financial analysis data.

    Args:
        context: The current conversation context
        company_name: Name of the company to analyze

    Returns:
        str: Financial analysis summary
    """
    # Update context
    context.context.company_name = company_name

    # Mock financial data based on company
    company_lower = company_name.lower()

    if "apple" in company_lower:
        analysis = """
Financial Analysis: Apple Inc. (AAPL)

Key Metrics (Q4 2024):
• Revenue: $89.5B (+6% YoY)
• Gross Margin: 46.2%
• Operating Margin: 30.8%
• Net Income: $22.1B
• EPS: $1.42 (vs $1.29 prior year)
• Free Cash Flow: $28.3B

Balance Sheet Strength:
• Cash & Equivalents: $162B
• Total Debt: $108B
• Debt-to-Equity: 1.8x
• Current Ratio: 1.0x

Growth Metrics:
• Revenue Growth (3Y CAGR): 8.4%
• Services Revenue Growth: 16.2% YoY
• iPhone Revenue: 52% of total revenue
• Gross Margin Trend: Stable at 45-47%

Valuation:
• P/E Ratio: 28.5x
• P/S Ratio: 7.2x
• EV/EBITDA: 21.3x
• Dividend Yield: 0.5%
"""
    elif "tesla" in company_lower:
        analysis = """
Financial Analysis: Tesla Inc. (TSLA)

Key Metrics (Q4 2024):
• Revenue: $25.2B (+11% YoY)
• Gross Margin: 18.2% (automotive)
• Operating Margin: 10.8%
• Net Income: $2.3B
• EPS: $0.73
• Free Cash Flow: $1.8B

Balance Sheet Strength:
• Cash & Equivalents: $26B
• Total Debt: $9B
• Debt-to-Equity: 0.3x
• Current Ratio: 1.7x

Growth Metrics:
• Vehicle Deliveries Growth: 38% YoY
• Energy Storage Growth: 150% YoY
• Automotive ASP: $47,500
• Gross Margin Trend: Improving from cost reductions

Valuation:
• P/E Ratio: 65.3x
• P/S Ratio: 8.1x
• EV/EBITDA: 45.2x
• No Dividend
"""
    else:
        # Generic analysis
        analysis = f"""
Financial Analysis: {company_name}

Key Metrics (Latest Quarter):
• Revenue: ${random.randint(5, 50)}B (+{random.randint(5, 20)}% YoY)
• Gross Margin: {random.randint(25, 50)}%
• Operating Margin: {random.randint(10, 30)}%
• Net Income: ${random.randint(1, 10)}B
• Free Cash Flow: ${random.randint(1, 8)}B

Balance Sheet:
• Cash Position: Strong
• Debt Levels: Moderate
• Current Ratio: {random.uniform(1.2, 2.0):.1f}x

Growth Profile:
• Revenue CAGR (3Y): {random.randint(10, 25)}%
• Market Position: Strong in core segments
• Geographic Diversification: Good
"""

    # Store in context
    context.context.financials_analysis = analysis

    return analysis


@function_tool(
    name_override="risk_analysis_tool",
    description_override="Assess business risks including market, operational, financial, and competitive risks"
)
async def risk_analysis_tool(
    context: RunContextWrapper[FinancialResearchContext],
    company_name: str
) -> str:
    """
    Perform risk analysis for a company.

    Mock implementation that generates realistic risk assessment.

    Args:
        context: The current conversation context
        company_name: Name of the company to analyze

    Returns:
        str: Risk analysis summary
    """
    company_lower = company_name.lower()

    if "apple" in company_lower:
        analysis = """
Risk Analysis: Apple Inc. (AAPL)

Market Risks (Medium):
• China exposure (~20% of revenue) - geopolitical tensions
• Smartphone market maturation - slowing iPhone growth
• Currency fluctuations - strong dollar impact

Operational Risks (Low):
• Supply chain concentration in Asia - COVID exposure
• Manufacturing partner dependence (Foxconn, etc.)
• Component shortages - though improving

Financial Risks (Low):
• Strong balance sheet with $162B cash
• Minimal refinancing risk
• Foreign cash repatriation considerations

Competitive Risks (Medium):
• Android ecosystem competition
• Chinese smartphone makers in emerging markets
• AI services competition (Google, Microsoft)

Regulatory Risks (Medium-High):
• App Store antitrust scrutiny (EU, US)
• Privacy regulation impact on advertising
• Right-to-repair legislation

Strategic Risks (Medium):
• AR/VR market uncertain (Vision Pro)
• Services growth deceleration risk
• Innovation pipeline visibility

Overall Risk Rating: MODERATE
Key Mitigants: Strong brand, loyal customer base, ecosystem lock-in, financial strength
"""
    elif "tesla" in company_lower:
        analysis = """
Risk Analysis: Tesla Inc. (TSLA)

Market Risks (High):
• EV market competition intensifying
• Price sensitivity and margin pressure
• Regulatory credit phase-out

Operational Risks (Medium-High):
• Production ramp challenges (Cybertruck)
• Quality control issues historically
• Service network capacity

Financial Risks (Medium):
• Capital intensity of manufacturing expansion
• Working capital needs for growth
• Valuation dependent on growth delivery

Competitive Risks (High):
• Traditional OEMs entering EV market aggressively
• Chinese EV makers (BYD, NIO, XPeng)
• Battery technology race

Regulatory Risks (Medium):
• Autonomous driving regulations uncertain
• EV subsidies phase-out in some markets
• Safety investigations (NHTSA)

Strategic Risks (High):
• Key person risk (CEO concentration)
• Multiple ventures competing for capital/attention
• Autonomous driving timeline

Overall Risk Rating: ELEVATED
Key Mitigants: First-mover advantage, vertical integration, brand strength
"""
    else:
        # Generic risk analysis
        analysis = f"""
Risk Analysis: {company_name}

Market Risks: Industry cyclicality, demand fluctuations
Operational Risks: Supply chain, execution, operational efficiency
Financial Risks: Leverage, liquidity, capital allocation
Competitive Risks: Market share pressure, pricing dynamics
Regulatory Risks: Compliance, regulatory changes
Strategic Risks: M&A integration, innovation pipeline

Overall Risk Rating: MODERATE
"""

    # Store in context
    context.context.risk_analysis = analysis

    return analysis


@function_tool(
    name_override="market_data_tool",
    description_override="Get current market data including stock prices, market cap, and trading volumes"
)
async def market_data_tool(ticker: str) -> str:
    """
    Retrieve current market data for a stock.

    Mock implementation that generates realistic market data.

    Args:
        ticker: Stock ticker symbol

    Returns:
        str: Market data summary
    """
    # Mock market data
    base_prices = {
        "AAPL": 178.50,
        "TSLA": 242.80,
        "NVDA": 495.20,
        "AMD": 148.30,
        "MSFT": 378.90
    }

    price = base_prices.get(ticker.upper(), random.uniform(50, 300))
    change = random.uniform(-5, 5)
    change_pct = random.uniform(-2, 2)
    volume = random.randint(50, 200)

    market_data = f"""
Market Data: {ticker.upper()}

Current Price: ${price:.2f}
Change: ${change:+.2f} ({change_pct:+.2f}%)
Day Range: ${price * 0.98:.2f} - ${price * 1.02:.2f}

Volume: {volume}M shares
Avg Volume (3M): {volume * 1.1:.0f}M shares
Market Cap: ${price * random.randint(500, 3000) / 1000:.1f}T

52-Week Range: ${price * 0.70:.2f} - ${price * 1.15:.2f}
YTD Return: {random.uniform(-10, 50):+.1f}%

Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Source: Mock Market Data
"""

    return market_data


# Helper function to validate company names
def is_valid_company_name(name: str) -> bool:
    """
    Validate if a company name seems reasonable.

    Args:
        name: Company name to validate

    Returns:
        bool: True if valid format
    """
    return len(name) >= 2 and not name.isdigit()


# Helper function to generate mock search terms
def generate_search_terms(query: str) -> List[str]:
    """
    Generate search terms based on a research query.

    Args:
        query: User's research query

    Returns:
        List of search terms
    """
    terms = []

    # Extract company/topic
    query_lower = query.lower()

    if "apple" in query_lower:
        terms = [
            "Apple Inc Q4 2024 earnings",
            "Apple iPhone sales trends",
            "Apple services revenue growth",
            "Apple AI strategy"
        ]
    elif "tesla" in query_lower:
        terms = [
            "Tesla Q4 2024 deliveries",
            "Tesla Cybertruck production",
            "Tesla energy storage business",
            "Tesla competition analysis"
        ]
    elif "ai" in query_lower and "semiconductor" in query_lower:
        terms = [
            "AI semiconductor market size",
            "NVIDIA AI chip market share",
            "AI inference chip competition",
            "AI chip supply chain"
        ]
    else:
        # Generic terms
        terms = [
            f"{query} financial performance",
            f"{query} market analysis",
            f"{query} competitive landscape",
            f"{query} growth trends"
        ]

    return terms[:4]  # Return up to 4 terms
