"""
Competitive Intelligence Report Schema Models (Pydantic v2 Compatible)

This module defines the complete Pydantic model structure for competitive intelligence
reports, ensuring type safety and validation for all report components.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator, model_validator
import re

logger = logging.getLogger(__name__)


# Helper functions for formatting
def format_percentage(value: float) -> str:
    """Convert decimal to percentage string (0.1553 → '15.53%')"""
    return f"{value * 100:.2f}%"


def normalize_percentage_display(value: float) -> float:
    """Normalize percentage for display (0.1553 → 15.53)"""
    return round(value * 100, 2)


# Enums for controlled vocabularies
class DataQuality(str, Enum):
    """Data quality indicators"""
    VALID = "valid"
    ESTIMATED = "estimated"
    INSUFFICIENT = "insufficient"


class RecommendationPriority(str, Enum):
    """Priority levels for recommendations"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecommendationCategory(str, Enum):
    """Categories for actionable recommendations"""
    DO = "do"
    SAY = "say"
    SHOW = "show"


# Input Models for LLM Generation
class ExecutiveSummaryInput(BaseModel):
    """
    Input data required to generate Executive Summary via LLM.
    
    This model defines all the data that must be collected (from FMP API and calculations)
    before calling the LLM to generate the executive summary narrative.
    
    Data Sources:
    - Company profile: FMP API /api/v3/profile/{symbol}
    - Financial metrics: Calculated from FMP financial statements
    - Analysis findings: Generated from comparative analysis modules
    """
    # Company identification
    symbol: str = Field(..., description="Stock ticker symbol (e.g., 'WRB')")
    company_name: str = Field(..., description="Full company name (e.g., 'W.R. Berkley Corporation')")
    industry: str = Field(..., description="Industry classification (e.g., 'Property & Casualty Insurance')")
    sector: str = Field(..., description="Sector classification (e.g., 'Financials')")
    report_date: str = Field(..., description="Report generation date (ISO format)")
    
    # Peer group context
    peer_count: int = Field(..., ge=1, description="Number of peer companies analyzed")
    peer_symbols: List[str] = Field(..., description="List of peer company symbols")
    
    # Valuation metrics (can be negative for unprofitable companies)
    market_cap: float = Field(..., ge=0, description="Target company market capitalization in USD")
    current_pe: float = Field(..., description="Target company P/E ratio (negative if unprofitable)")
    peer_average_pe: float = Field(..., description="Peer group average P/E ratio")
    valuation_gap: float = Field(..., description="P/E gap (current_pe - peer_average_pe)")
    gap_percentage: float = Field(..., description="P/E gap as percentage")
    
    # Target valuation (from comparative analysis)
    target_pe: float = Field(..., description="Target P/E ratio from valuation analysis (e.g., 19.75x)")
    target_market_cap_change: float = Field(..., description="Market cap change if target_pe achieved (positive = increase, negative = decrease)")
    target_gap_percentage: float = Field(..., description="Percentage change to target valuation (positive = increase, negative = decrease)")
    is_trading_at_premium: bool = Field(..., description="True if current P/E > peer average (trading at premium)")
    valuation_direction: str = Field(..., description="Either 'premium' or 'discount' indicating valuation scenario")
    
    # Profitability metrics
    target_roe: float = Field(..., description="Target company ROE percentage")
    peer_average_roe: float = Field(..., description="Peer group average ROE percentage")
    
    # Industry-specific metrics (optional, depends on sector)
    target_combined_ratio: Optional[float] = Field(None, description="Target combined ratio (insurance)")
    peer_combined_ratio: Optional[float] = Field(None, description="Peer average combined ratio (insurance)")
    target_revenue_growth: Optional[float] = Field(None, description="Target revenue growth percentage")
    peer_revenue_growth: Optional[float] = Field(None, description="Peer average revenue growth percentage")
    
    # Competitive position analysis (from comparative analysis modules)
    target_rank: int = Field(..., ge=1, description="Target company's overall ranking (1 = best)")
    areas_of_excellence: List[str] = Field(..., description="Metrics where target outperforms peers")
    areas_of_improvement: List[str] = Field(..., description="Metrics where target underperforms peers")
    perception_gaps: List[str] = Field(..., description="Identified perception gaps affecting valuation")
    perception_gap_count: int = Field(default=0, ge=0, description="Count of perception gaps (auto-calculated from list length)")
    
    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v):
        return v.upper().strip()
    
    @field_validator('valuation_gap')
    @classmethod
    def validate_valuation_gap(cls, v, info):
        """Ensure valuation gap matches calculation"""
        if 'current_pe' in info.data and 'peer_average_pe' in info.data:
            expected_gap = info.data['current_pe'] - info.data['peer_average_pe']
            if abs(v - expected_gap) > 0.01:  # Allow small rounding differences
                raise ValueError(f"Valuation gap {v} doesn't match calculation {expected_gap}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "WRB",
                "company_name": "W.R. Berkley Corporation",
                "industry": "Property & Casualty Insurance",
                "sector": "Financials",
                "report_date": "2025-10-22",
                "peer_count": 4,
                "peer_symbols": ["PGR", "CB", "TRV", "HIG"],
                "current_pe": 12.1,
                "peer_average_pe": 15.1,
                "valuation_gap": -3.0,
                "gap_percentage": -19.9,
                "target_roe": 18.4,
                "peer_average_roe": 19.8,
                "target_combined_ratio": 88.3,
                "peer_combined_ratio": 91.2,
                "target_revenue_growth": 8.5,
                "peer_revenue_growth": 7.8,
                "target_rank": 3,
                "areas_of_excellence": ["Combined ratio (88.3, best in group)", "Debt/equity (0.41, lowest leverage)", "ROE (18.4%, 2nd best)"],
                "areas_of_improvement": ["Market cap (12.5B, smallest)", "P/E multiple (12.1x, lowest)", "Revenue growth (8.5%, below peer avg)"],
                "perception_gaps": ["Limited technology narrative vs Progressive", "Specialty lines complexity concerns", "Insufficient communication of underwriting advantages"]
            }
        }


# Core Data Models
class ReportMetadata(BaseModel):
    """Metadata about the competitive intelligence report"""
    report_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique report identifier")
    generated_at: datetime = Field(default_factory=datetime.now, description="Report generation timestamp")
    target_symbol: str = Field(..., description="Stock symbol of the target company")
    version: str = Field(default="1.0", description="Report schema version")
    processing_time_seconds: Optional[float] = Field(None, description="Time taken to generate report")
    
    @field_validator('target_symbol')
    @classmethod
    def validate_target_symbol(cls, v):
        if not v or not v.strip():
            raise ValueError("Target symbol cannot be empty")
        return v.upper().strip()


class DataSource(BaseModel):
    """Information about data sources used in the report"""
    source_type: str = Field(..., description="Type of data source (e.g., 'financial_api', 'earnings_transcript')")
    provider: str = Field(..., description="Data provider name")
    data_date: Optional[datetime] = Field(None, description="Date of the data")
    quality: DataQuality = Field(default=DataQuality.VALID, description="Quality assessment of the data")


class CompanyProfile(BaseModel):
    """Basic company information and metrics"""
    symbol: str = Field(..., description="Stock symbol")
    company_name: str = Field(..., description="Full company name")
    sector: str = Field(..., description="Business sector")
    market_cap: Optional[float] = Field(None, description="Market capitalization in USD")
    pe_ratio: Optional[float] = Field(None, description="Price-to-earnings ratio")
    revenue_ttm: Optional[float] = Field(None, description="Trailing twelve months revenue")
    
    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v):
        if not v or not v.strip():
            raise ValueError("Symbol cannot be empty")
        return v.upper().strip()


class PeerCompany(BaseModel):
    """Information about a peer company"""
    symbol: str = Field(..., description="Stock symbol of peer company")
    company_name: str = Field(..., description="Full company name")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score to target company")
    
    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v):
        if not v or not v.strip():
            raise ValueError("Symbol cannot be empty")
        return v.upper().strip()


class PeerSelectionRationale(BaseModel):
    """
    Explanation of peer selection methodology and structural caveats.
    
    Addresses potential criticism about comparing companies across different subsectors
    (e.g., equipment suppliers vs foundries vs fabless).
    """
    methodology: str = Field(
        ...,
        min_length=50,
        max_length=500,
        description="Explanation of how peers were selected (e.g., 'Market cap proximity within same sector')"
    )
    structural_differences: str = Field(
        ...,
        min_length=100,
        max_length=800,
        description="Acknowledgment of business model differences across peer set "
                    "(e.g., 'Peer set includes equipment suppliers, foundries, and fabless companies with different margin profiles')"
    )
    interpretation_guidance: str = Field(
        ...,
        min_length=50,
        max_length=500,
        description="How to interpret comparisons given structural differences "
                    "(e.g., 'Premium partially reflects monopoly position, not solely perception gaps')"
    )
    alternative_peer_considerations: Optional[str] = Field(
        None,
        max_length=300,
        description="Optional: Alternative peer sets considered and why current set was chosen"
    )


class ReportMethodology(BaseModel):
    """
    Explanation of report methodology for transparency.
    
    Describes data sources, analytical approach, limitations, and how findings should be interpreted.
    """
    overview: str = Field(
        default=(
            "This competitive intelligence report combines quantitative financial analysis with AI-assisted "
            "qualitative interpretation to identify valuation gaps and actionable opportunities. The methodology "
            "prioritizes transparency, data-driven insights, and sector-agnostic applicability."
        ),
        min_length=100,
        max_length=500,
        description="High-level summary of the analytical approach"
    )
    
    data_sources_description: str = Field(
        default=(
            "Financial data sourced from FinancialModelingPrep (FMP) API, including: (1) company profiles "
            "and market data (quote, market cap, P/E); (2) quarterly financial statements (income statement, "
            "balance sheet, cash flow) for trailing 5 quarters; (3) key financial ratios and metrics; "
            "(4) analyst ratings and consensus data; (5) earnings call transcripts for linguistic analysis. "
            "Company overviews and industry context augmented via web search (OpenAI). All financial metrics "
            "calculated to ensure accuracy and consistency."
        ),
        min_length=200,
        max_length=800,
        description="Detailed explanation of data sources and collection methods"
    )
    
    peer_selection_process: str = Field(
        default=(
            "Peers identified via automated screening based on: (1) sector match (same GICS sector), "
            "(2) market capitalization proximity (within ±70% of target), and (3) industry relevance. "
            "Selection prioritizes scale comparability and sector alignment over perfect business model fit. "
            "Typically 3-5 peers selected to balance statistical robustness with focused analysis. Peer selection "
            "rationale includes structural differences acknowledgment when cross-subsector comparisons occur."
        ),
        min_length=200,
        max_length=600,
        description="How peer companies are identified and selected"
    )
    
    analytical_framework: str = Field(
        default=(
            "Analysis combines: (1) Quantitative benchmarking across 8-11 financial metrics (market cap, P/E, "
            "ROE, ROA, revenue growth, margins, leverage) with competitive rankings (1=best); (2) Valuation gap analysis "
            "comparing target P/E to peer average, with directional assessment (premium vs discount). "
            "VALUATION FORMULAS: implied_market_cap = current_market_cap × (peer_benchmark_pe / current_pe); "
            "premium_vs_peer_percent = ((current_pe - peer_benchmark_pe) / peer_benchmark_pe) × 100 (basis: peer); "
            "downside_to_peer_multiple_percent = ((implied_market_cap - current_market_cap) / current_market_cap) × 100 (basis: current). "
            "(3) AI-assisted market perception classification (e.g., 'Undervalued', 'Hidden strength', 'Root cause') "
            "based on metric rankings vs valuation multiples; (4) Linguistic analysis of earnings transcripts to "
            "identify messaging patterns and sentiment correlations; (5) Multi-factor P/E decomposition to separate "
            "fundamental vs perception-driven valuation components."
        ),
        min_length=300,
        max_length=1200,
        description="Core analytical methods and frameworks applied"
    )
    
    llm_role_and_transparency: str = Field(
        default=(
            "Large language models (LLMs) used for: (1) generating narrative explanations of pre-calculated metrics, "
            "(2) identifying market perception gaps by analyzing metric rankings vs valuation, (3) synthesizing "
            "earnings call themes and competitor messaging patterns, and (4) formulating actionable recommendations. "
            "All quantitative calculations (rankings, percentages, valuation impacts) performed in Python prior to "
            "LLM involvement to eliminate math errors. LLM outputs validated against input data and schema constraints. "
            "Model: OpenAI GPT-4 family (gpt-5-mini for structured outputs)."
        ),
        min_length=300,
        max_length=800,
        description="How AI/LLMs are used and what safeguards are in place"
    )
    
    limitations_and_caveats: str = Field(
        default=(
            "Limitations: (1) Peer comparisons may span different subsectors with varying business models, margins, "
            "and capital structures—interpretation guidance provided when applicable; (2) Market perception analysis "
            "is inferential, not based on direct investor surveys; (3) Valuation gap decomposition uses industry-standard "
            "heuristics and regression models, not company-specific proprietary models; (4) Earnings transcript analysis "
            "limited to most recent available transcripts (typically 1-2 quarters); (5) Recommendations are directional "
            "and require company-specific contextualization before implementation; (6) Historical data and peer comparisons "
            "do not guarantee future performance or valuation outcomes."
        ),
        min_length=300,
        max_length=1000,
        description="Known limitations, assumptions, and important caveats"
    )
    
    intended_use: str = Field(
        default=(
            "This report is intended for internal strategic planning, investor relations assessment, and competitive "
            "positioning analysis. It is NOT investment advice and should not be used as the sole basis for investment "
            "decisions. Findings represent analytical perspectives based on available data and may not reflect all "
            "material factors affecting valuation. Users should conduct independent verification and consult qualified "
            "financial advisors before making strategic or investment decisions."
        ),
        min_length=200,
        max_length=600,
        description="Intended use and important disclaimers"
    )


class PeerGroup(BaseModel):
    """Collection of peer companies"""
    target_company: CompanyProfile = Field(..., description="The target company being analyzed")
    peers: List[PeerCompany] = Field(..., min_length=1, description="List of peer companies")
    discovery_method: str = Field(..., description="Method used to discover peers")
    selection_rationale: Optional[PeerSelectionRationale] = Field(
        None,
        description="Explanation of why these peers were selected and how to interpret cross-subsector comparisons"
    )
    
    @field_validator('peers')
    @classmethod
    def validate_peers(cls, v):
        if len(v) == 0:
            raise ValueError("At least one peer company must be provided")
        return v


class MetricComparison(BaseModel):
    """Comparison of a single metric across companies"""
    metric_name: str = Field(..., description="Name of the metric being compared")
    target_value: Optional[float] = Field(None, description="Target company's value for this metric")
    peer_values: Dict[str, float] = Field(default_factory=dict, description="Peer companies' values")
    target_ranking: Optional[int] = Field(None, description="Target company's ranking (1 = best)")
    analysis: str = Field(..., description="Analysis of the comparison")


# Valuation Context Summary
class ValuationContext(BaseModel):
    """
    Summary of valuation metrics for quick reference.
    Provides context for P/E gap and implied market cap scenarios.
    """
    current_pe: float = Field(..., description="Current P/E ratio of target company")
    peer_average_pe: float = Field(..., description="Peer group average P/E ratio")
    target_pe: float = Field(..., description="Target/fair value P/E ratio (from analysis)")
    current_market_cap: float = Field(..., ge=0, description="Current market capitalization in USD")
    implied_market_cap: float = Field(..., ge=0, description="Implied market cap at target P/E")
    valuation_gap_percent: float = Field(..., description="Valuation gap as percentage (positive = upside)")
    valuation_gap_dollars: float = Field(..., description="Valuation gap in dollars (implied - current)")
    
    @field_validator('target_pe')
    @classmethod
    def validate_target_pe(cls, v, info):
        """Ensure target P/E is reasonable"""
        if v <= 0:
            raise ValueError("Target P/E must be positive")
        if v > 100:
            logger.warning(f"Target P/E unusually high: {v}x")
        return v


# Report Section Models
class ExecutiveSummary(BaseModel):
    """
    Executive summary section of the report (Section 1).
    
    This section provides a high-level narrative overview with key findings
    and actionable recommendations. Requires narrative generation via LLM.
    
    Narrative Generation:
    - Primary Tool: src.metis.assistants.generic_llm_agent.py
    - Prompt File: prompts/narrative_generation/executive_summary.txt
    - Method: generate_text_sync() for narrative content
    """
    company_overview: str = Field(
        ..., 
        min_length=200, 
        max_length=2000,
        description="Target company overview (1 paragraph narrative). "
                    "GENERATED BY LLM using executive_summary.txt prompt with inputs: "
                    "symbol, company_name, industry, financial metrics (P/E, ROE, etc.). "
                    "LLM synthesizes company profile from its training data + provided metrics."
    )
    
    key_finding: str = Field(
        ...,
        min_length=50,
        description="Valuation gap with specific numbers. "
                    "Must include P/E comparisons (e.g., 'trades at 12.1x vs peer avg 14.5x'). "
                    "Calculated from financial data, then formatted as narrative."
    )
    
    root_cause: str = Field(
        ...,
        min_length=50,
        description="Number of perception gaps identified with explanation. "
                    "Example: '3 perception gaps: analyst complexity concerns, "
                    "limited technology narrative, insufficient communication'."
    )
    
    top_recommendations: List[str] = Field(
        ...,
        min_items=3,
        max_items=3,
        description="Exactly 3 actionable recommendations with impact estimates. "
                    "Generated via LLM synthesis of analysis findings."
    )
    
    @field_validator('company_overview')
    @classmethod
    def validate_company_overview_length(cls, v):
        """Ensure company overview meets narrative requirements"""
        if not v or not v.strip():
            raise ValueError("Company overview cannot be empty")
        
        clean_text = v.strip()
        if len(clean_text) < 200:
            raise ValueError(f"Company overview too short: {len(clean_text)} chars (minimum 200)")
        if len(clean_text) > 2000:
            raise ValueError(f"Company overview too long: {len(clean_text)} chars (maximum 2000)")
        
        return clean_text
    
    @field_validator('key_finding')
    @classmethod
    def validate_key_finding_has_numbers(cls, v):
        """Ensure key finding contains specific numerical comparisons"""
        if not v or not v.strip():
            raise ValueError("Key finding cannot be empty")
        
        # Must contain at least one number (for P/E ratios)
        if not any(char.isdigit() for char in v):
            raise ValueError("Key finding must include specific numerical comparisons (P/E ratios)")
        
        # Should mention P/E or valuation concepts
        valuation_keywords = ['p/e', 'pe', 'multiple', 'trades at', 'vs', 'peer']
        has_valuation_context = any(keyword in v.lower() for keyword in valuation_keywords)
        
        if not has_valuation_context:
            raise ValueError("Key finding should reference valuation metrics (P/E, multiples, etc.)")
        
        return v.strip()
    
    @field_validator('root_cause')
    @classmethod
    def validate_root_cause(cls, v):
        """Ensure root cause provides meaningful explanation"""
        if not v or not v.strip():
            raise ValueError("Root cause cannot be empty")
        
        clean_text = v.strip()
        if len(clean_text) < 50:
            raise ValueError(f"Root cause too brief: {len(clean_text)} chars (minimum 50)")
        
        return clean_text
    
    @field_validator('top_recommendations')
    @classmethod
    def validate_recommendations_count(cls, v):
        """Ensure exactly 3 recommendations are provided"""
        if len(v) != 3:
            raise ValueError(f"Must provide exactly 3 recommendations, got {len(v)}")
        
        # Check each recommendation is not empty
        for i, rec in enumerate(v, 1):
            if not rec or not rec.strip():
                raise ValueError(f"Recommendation {i} cannot be empty")
            if len(rec.strip()) < 20:
                raise ValueError(f"Recommendation {i} too brief: '{rec}' (minimum 20 chars)")
        
        return [rec.strip() for rec in v]
    
    class Config:
        json_schema_extra = {
            "example": {
                "company_overview": "W.R. Berkley Corporation operates as a specialty insurance company "
                                  "focused on commercial lines with a diversified portfolio across property, "
                                  "casualty, and specialty segments. The company maintains a decentralized "
                                  "operating model with 50+ autonomous business units, enabling deep market "
                                  "expertise and underwriting discipline that has delivered consistent profitability "
                                  "through insurance cycles.",
                "key_finding": "WRB has best combined ratio (88.3) and 2nd-best ROE (18.4%) yet trades at "
                             "lowest multiple (12.1x vs peer avg 14.5x), representing a 19.9% valuation discount",
                "root_cause": "3 perception gaps identified: analyst complexity concerns about specialty lines, "
                            "limited technology narrative compared to peers, insufficient communication of "
                            "underwriting advantages",
                "top_recommendations": [
                    "Rebrand specialty underwriting as AI-powered risk assessment to align with market preferences",
                    "Adopt Progressive's quantitative guidance style (80% statements include specific numbers)",
                    "Highlight debt advantage (0.41 vs 0.50 peer avg) in all investor materials"
                ]
            }
        }


class MarketPerception(str, Enum):
    """Market perception categories for competitive positioning"""
    UNDERVALUED = "Undervalued"
    UNDERAPPRECIATED = "Underappreciated"
    HIDDEN_STRENGTH = "Hidden strength"
    NOT_COMMUNICATED = "Not communicated"
    ADEQUATE = "Adequate"
    OVERVALUED = "Overvalued"
    ROOT_CAUSE = "Root cause"


class CompetitiveMetric(BaseModel):
    """
    Individual metric in the competitive dashboard table.
    
    Each metric tracks target company performance vs peers with ranking and
    market perception analysis (LLM-generated explanation of why the metric matters).
    """
    model_config = {"extra": "forbid"}  # Strict schema for OpenAI Agents SDK
    
    metric_name: str = Field(..., description="Name of the metric (e.g., 'P/E Ratio', 'ROE', 'Combined Ratio')")
    target_value: float = Field(..., description="Target company's value for this metric")
    peer_values: Dict[str, float] = Field(
        ..., 
        description="Dictionary mapping peer symbols to their metric values (e.g., {'PGR': 20.5, 'CB': 15.2})"
    )
    target_rank: int = Field(
        ..., 
        ge=1,
        description="Target company's ranking for this metric (1 = best). Lower is better for most metrics."
    )
    rank_qualifier: Optional[str] = Field(
        None,
        description="Optional qualifier for rank (e.g., 'best', 'worst', '2nd best')"
    )
    market_perception: MarketPerception = Field(
        ...,
        description="How the market perceives this metric. GENERATED BY LLM analyzing "
                    "whether metric indicates undervaluation, hidden strength, or perception gap."
    )
    perception_explanation: str = Field(
        ...,
        min_length=20,
        max_length=500,
        description="LLM-generated explanation of why this perception exists and its valuation impact. "
                    "Example: 'Best-in-class combined ratio (88.3) demonstrates superior underwriting "
                    "discipline but market perception gap exists due to insufficient communication '."
    )
    
    @field_validator('peer_values')
    @classmethod
    def validate_peer_values_not_empty(cls, v):
        """Ensure at least one peer value is provided"""
        if not v or len(v) == 0:
            raise ValueError("At least one peer value must be provided")
        return v
    
    @field_validator('perception_explanation')
    @classmethod
    def validate_perception_explanation(cls, v):
        """Ensure perception explanation is meaningful"""
        if not v or not v.strip():
            raise ValueError("Perception explanation cannot be empty")
        
        clean_text = v.strip()
        if len(clean_text) < 20:
            raise ValueError(f"Perception explanation too brief: {len(clean_text)} chars (minimum 20)")
        if len(clean_text) > 500:
            raise ValueError(f"Perception explanation too long: {len(clean_text)} chars (maximum 500)")
        
        return clean_text


class CompetitiveDashboardInput(BaseModel):
    """
    Input data required to generate Competitive Dashboard via LLM.
    
    This model defines all raw financial data and rankings that must be collected
    before calling the LLM to generate market perception analysis and explanations.
    
    CALCULATION STRATEGY:
    - Top 3 strengths/weaknesses PRE-CALCULATED in Python (by rank)
    - LLM only writes narrative summaries using the provided metrics
    
    Data Sources:
    - Financial metrics: FMP API financial statements for all companies
    - Rankings: Calculated by sorting peer group for each metric
    """
    # Company identification
    target_symbol: str = Field(..., description="Stock ticker symbol")
    peer_symbols: List[str] = Field(..., min_length=1, description="List of peer company symbols")
    
    # Metrics to compare (expandable based on sector)
    metrics: List[Dict[str, Any]] = Field(
        ...,
        min_length=5,
        description="List of metrics with raw data. Each dict must contain: "
                    "{metric_name: str, target_value: float, peer_values: Dict[str, float], "
                    "target_rank: int, rank_qualifier: str}"
    )
    
    # PRE-CALCULATED top performers (LLM uses these, does not choose)
    top_3_strengths: List[Dict[str, Any]] = Field(
        ...,
        min_length=1,
        max_length=3,
        description="Top 3 metrics where target ranks best (lowest rank number). "
                    "Each dict: {metric_name: str, target_value: float, target_rank: int, rank_qualifier: str}. "
                    "Pre-calculated in Python - LLM writes summary using these exact metrics."
    )
    
    top_3_weaknesses: List[Dict[str, Any]] = Field(
        ...,
        min_length=1,
        max_length=3,
        description="Top 3 metrics where target ranks worst (highest rank number). "
                    "Each dict: {metric_name: str, target_value: float, target_rank: int, rank_qualifier: str}. "
                    "Pre-calculated in Python - LLM writes summary using these exact metrics."
    )
    
    @field_validator('metrics')
    @classmethod
    def validate_metrics_structure(cls, v):
        """Ensure each metric dict has required fields"""
        required_fields = {'metric_name', 'target_value', 'peer_values', 'target_rank', 'rank_qualifier'}
        
        for i, metric in enumerate(v, 1):
            if not isinstance(metric, dict):
                raise ValueError(f"Metric {i} must be a dictionary")
            
            missing_fields = required_fields - set(metric.keys())
            if missing_fields:
                raise ValueError(f"Metric {i} missing required fields: {missing_fields}")
            
            # Validate types
            if not isinstance(metric['metric_name'], str) or not metric['metric_name'].strip():
                raise ValueError(f"Metric {i} has invalid metric_name")
            
            if not isinstance(metric['target_value'], (int, float)):
                raise ValueError(f"Metric {i} has invalid target_value (must be number)")
            
            if not isinstance(metric['peer_values'], dict) or len(metric['peer_values']) == 0:
                raise ValueError(f"Metric {i} has invalid peer_values (must be non-empty dict)")
            
            if not isinstance(metric['target_rank'], int) or metric['target_rank'] < 1:
                raise ValueError(f"Metric {i} has invalid target_rank (must be positive integer)")
            
            if not isinstance(metric['rank_qualifier'], str) or not metric['rank_qualifier'].strip():
                raise ValueError(f"Metric {i} has invalid rank_qualifier")
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "target_symbol": "WRB",
                "peer_symbols": ["PGR", "CB", "TRV", "HIG"],
                "metrics": [
                    {
                        "metric_name": "P/E Ratio",
                        "target_value": 12.1,
                        "peer_values": {"PGR": 20.5, "CB": 15.2, "TRV": 13.8, "HIG": 14.1},
                        "target_rank": 5
                    },
                    {
                        "metric_name": "ROE",
                        "target_value": 18.4,
                        "peer_values": {"PGR": 29.1, "CB": 12.8, "TRV": 13.2, "HIG": 11.9},
                        "target_rank": 2
                    },
                    {
                        "metric_name": "Combined Ratio",
                        "target_value": 88.3,
                        "peer_values": {"PGR": 90.2, "CB": 89.1, "TRV": 92.8, "HIG": 91.4},
                        "target_rank": 1
                    }
                ]
            }
        }


class CompetitiveDashboard(BaseModel):
    """
    Competitive dashboard section (Section 2) with detailed metric-by-metric comparison.
    
    This section provides a comprehensive comparison table showing target company
    performance vs peers across key metrics, with LLM-generated market perception
    analysis explaining why each metric matters and how the market interprets it.
    
    Narrative Generation:
    - Primary Tool: src.metis.assistants.generic_llm_agent.py
    - Prompt File: prompts/comparative_analysis/competitive_dashboard.txt
    - Method: generate_structured_output() with CompetitiveMetric schema
    - Input: CompetitiveDashboardInput with raw financial data
    - Output: List of CompetitiveMetric with LLM-generated perception analysis
    """
    model_config = {"extra": "forbid"}  # Strict schema for OpenAI Agents SDK
    
    metrics: List[CompetitiveMetric] = Field(
        ...,
        min_length=5,
        max_length=20,
        description="List of competitive metrics with rankings and market perception analysis. "
                    "Minimum 5 core metrics (P/E, ROE, Revenue Growth, Margins, Debt), "
                    "maximum 20 to ensure dashboard readability."
    )
    
    overall_target_rank: int = Field(
        ...,
        ge=1,
        description="Target company's overall competitive ranking based on weighted average "
                    "of all metrics (1 = best). Calculated from individual metric ranks."
    )
    
    key_strengths_summary: str = Field(
        ...,
        min_length=50,
        max_length=500,
        description="LLM-generated summary using ONLY the top_3_strengths provided in input. "
                    "Write narrative about these specific metrics - DO NOT choose different ones. "
                    "Example: 'CCL leads in scale (#1 market cap: $38.5B), operational efficiency (#1 net margin: 22.7%), "
                    "and profitability (#2 ROE: 15.5%)'."
    )
    
    key_weaknesses_summary: str = Field(
        ...,
        min_length=50,
        max_length=500,
        description="LLM-generated summary using ONLY the top_3_weaknesses provided in input. "
                    "Write narrative about these specific metrics - DO NOT choose different ones. "
                    "Example: 'CCL trails in leverage (#4 debt/equity: 5.21x), asset efficiency (#3 ROA: 3.45%), "
                    "and capital intensity (#3 asset turnover: 0.52x)'."
    )
    
    perception_gap_count: int = Field(
        default=0,
        ge=0,
        description="AUTO-CALCULATED: Count of metrics where market_perception indicates a gap "
                    "(Undervalued, Underappreciated, Hidden strength, Not communicated, Root cause). "
                    "Computed in Python after LLM generation by counting matching perception tags. "
                    "Represents opportunities to close valuation gaps through better communication. "
                    "DEFAULT: 0 (will be auto-corrected by validator)."
    )
    
    @field_validator('metrics')
    @classmethod
    def validate_metrics_minimum(cls, v):
        if len(v) < 5:
            raise ValueError(f"Dashboard must include at least 5 metrics, got {len(v)}")
        if len(v) > 20:
            raise ValueError(f"Dashboard should not exceed 20 metrics for readability, got {len(v)}")
        return v
    
    @model_validator(mode='after')
    def validate_perception_gap_count(self):
        """Validate perception_gap_count matches actual gaps in metrics"""
        gap_perceptions = {'Undervalued', 'Underappreciated', 'Hidden strength', 'Not communicated', 'Root cause', 'Overvalued'}
        
        actual_gap_count = sum(
            1 for metric in self.metrics 
            if metric.market_perception in gap_perceptions
        )
        
        if self.perception_gap_count != actual_gap_count:
            # Auto-correct instead of failing
            logger.warning(
                f"perception_gap_count mismatch: LLM said {self.perception_gap_count}, "
                f"actual count is {actual_gap_count}. Auto-correcting."
            )
            self.perception_gap_count = actual_gap_count
        
        return self
    
    @field_validator('key_strengths_summary')
    @classmethod
    def validate_strengths_summary(cls, v):
        """Ensure strengths summary is meaningful"""
        if not v or not v.strip():
            raise ValueError("Key strengths summary cannot be empty")
        
        clean_text = v.strip()
        if len(clean_text) < 50:
            raise ValueError(f"Strengths summary too brief: {len(clean_text)} chars (minimum 50)")
        
        return clean_text
    
    @field_validator('key_weaknesses_summary')
    @classmethod
    def validate_weaknesses_summary(cls, v):
        """Ensure weaknesses summary is meaningful"""
        if not v or not v.strip():
            raise ValueError("Key weaknesses summary cannot be empty")
        
        clean_text = v.strip()
        if len(clean_text) < 50:
            raise ValueError(f"Weaknesses summary too brief: {len(clean_text)} chars (minimum 50)")
        
        return clean_text


# ============================================================================
# Section 2.5: Analyst Consensus (NEW)
# ============================================================================

class AnalystAction(BaseModel):
    """
    Individual analyst rating action (upgrade, downgrade, maintain, initiate).
    """
    symbol: str = Field(..., description="Stock ticker symbol")
    date: str = Field(..., description="Action date (YYYY-MM-DD)")
    grading_company: str = Field(..., description="Name of analyst firm (e.g., 'Wells Fargo')")
    previous_grade: Optional[str] = Field(None, description="Previous rating (e.g., 'Hold')")
    new_grade: str = Field(..., description="New rating (e.g., 'Buy', 'Overweight')")
    action: str = Field(..., description="Action type: 'upgrade', 'downgrade', 'maintain', 'initiate'")


class AnalystConsensusMetric(BaseModel):
    """
    Analyst consensus metrics for a single company (target or peer).
    """
    symbol: str = Field(..., description="Stock ticker symbol")
    company_name: str = Field(..., description="Full company name")
    
    # 90-day recent activity
    recent_actions_90d: int = Field(..., ge=0, description="Total analyst actions in last 90 days")
    upgrades_90d: int = Field(..., ge=0, description="Number of upgrades in last 90 days")
    downgrades_90d: int = Field(..., ge=0, description="Number of downgrades in last 90 days")
    maintains_90d: int = Field(..., ge=0, description="Number of maintains in last 90 days")
    initiates_90d: int = Field(0, ge=0, description="Number of initiates in last 90 days")
    
    # Sentiment analysis
    net_sentiment: str = Field(
        ...,
        description="Overall sentiment from recent actions: 'Bullish' (more upgrades), "
                    "'Bearish' (more downgrades), 'Neutral' (balanced or no activity)"
    )
    
    # Coverage metrics
    coverage_breadth: int = Field(..., ge=0, description="Number of unique analyst firms covering in last 12 months")
    
    # Valuation metrics
    current_pe: float = Field(..., gt=0, description="Current P/E ratio for valuation context")
    
    # Most recent action
    latest_action: Optional[AnalystAction] = Field(None, description="Most recent analyst action")
    
    @field_validator('net_sentiment')
    @classmethod
    def validate_sentiment(cls, v):
        """Ensure sentiment is one of allowed values"""
        allowed = {'Bullish', 'Bearish', 'Neutral'}
        if v not in allowed:
            raise ValueError(f"net_sentiment must be one of {allowed}, got '{v}'")
        return v


class AnalystConsensusInput(BaseModel):
    """
    Input data required to generate Analyst Consensus section via LLM.
    
    This model defines all analyst rating/action data that must be collected
    from FMP before calling the LLM to generate perception gap analysis.
    
    Data Sources:
    - FMP API /stable/grades?symbol={SYMBOL}
    - Calculations: Count actions by type, determine sentiment, identify coverage gaps
    """
    target_analysis: AnalystConsensusMetric = Field(..., description="Target company analyst metrics")
    peer_analysis: List[AnalystConsensusMetric] = Field(..., description="Peer companies analyst metrics")
    
    # Additional context for LLM
    fundamental_strengths: List[str] = Field(
        ...,
        description="List of fundamental metrics where target outperforms (from Dashboard/Hidden Strengths). "
                    "Used to identify perception gaps: 'Strong net margin but low analyst coverage'"
    )
    
    @field_validator('peer_analysis')
    @classmethod
    def validate_peer_count(cls, v):
        """Ensure we have peer data"""
        if len(v) < 1:
            raise ValueError("Must have at least 1 peer for comparison")
        if len(v) > 10:
            raise ValueError(f"Too many peers for readability: {len(v)} (max 10)")
        return v


class AnalystConsensusOutput(BaseModel):
    """
    LLM-generated narrative output for Analyst Consensus section.
    
    This is what the LLM generates - just the 3 narrative fields.
    The full AnalystConsensusSection merges this with the input data.
    """
    relative_positioning: str = Field(
        ...,
        min_length=100,
        max_length=800,
        description="LLM analysis of target's position relative to peers in analyst coverage and sentiment"
    )
    
    perception_gap_narrative: str = Field(
        ...,
        min_length=150,
        max_length=1000,
        description="LLM explanation of WHY analyst attention/sentiment diverges from fundamental performance"
    )
    
    contrarian_opportunity_score: str = Field(
        ...,
        description="Overall score: 'High', 'Moderate', or 'Low'"
    )
    
    @field_validator('contrarian_opportunity_score')
    @classmethod
    def validate_contrarian_score(cls, v):
        """Ensure contrarian score is one of allowed values (with optional context in parentheses)"""
        allowed = {'High', 'Moderate', 'Low'}
        # Extract base score (before any parenthetical context)
        base_score = v.split('(')[0].strip()
        if base_score not in allowed:
            raise ValueError(f"contrarian_opportunity_score must start with one of {allowed}, got '{v}'")
        return v


class AnalystConsensusSection(BaseModel):
    """
    Analyst Consensus section (Section 2.5) showing how Wall Street attention differs from fundamentals.
    
    This section reveals coverage gaps, sentiment biases, and momentum disconnects
    that explain valuation discrepancies. Key insights:
    - Is target ignored while peers get attention? (coverage gap)
    - Are analysts bullish on expensive peers but bearish on cheap target? (sentiment bias)
    - Recent upgrades driving peer momentum despite weaker fundamentals? (narrative premium)
    """
    target_analysis: AnalystConsensusMetric = Field(..., description="Target company analyst metrics")
    peer_analysis: List[AnalystConsensusMetric] = Field(..., description="Peer companies analyst metrics")
    
    # LLM-generated comparative analysis
    relative_positioning: str = Field(
        ...,
        min_length=100,
        max_length=800,
        description="LLM analysis of target's position relative to peers in analyst coverage and sentiment. "
                    "Examples: 'Target is significantly under-covered (3 firms) vs peer average (9 firms)', "
                    "'PLNT received 5 upgrades vs 1 for CCL despite weaker fundamentals', "
                    "'Analyst momentum favors peers while fundamentals favor target - contrarian opportunity'"
    )
    
    perception_gap_narrative: str = Field(
        ...,
        min_length=150,
        max_length=1000,
        description="LLM explanation of WHY analyst attention/sentiment diverges from fundamental performance. "
                    "Must connect to metrics from Dashboard/Hidden Strengths. "
                    "Examples: 'Despite CCL's superior net margin (+35% vs HAS), analysts favor HAS (8 recent actions vs 2), "
                    "likely due to growth narrative bias in leisure sector', "
                    "'Coverage gap (3 firms vs 12 for peers) creates institutional blind spot despite #1 market cap ranking'"
    )
    
    # Key actionable insight
    contrarian_opportunity_score: str = Field(
        ...,
        description="Qualitative assessment of contrarian opportunity: 'High' (large divergence between fundamentals and "
                    "analyst sentiment), 'Moderate' (some divergence), 'Low' (analyst views align with fundamentals)"
    )
    
    @field_validator('contrarian_opportunity_score')
    @classmethod
    def validate_opportunity_score(cls, v):
        """Ensure score is one of allowed values (with optional context in parentheses)"""
        allowed = {'High', 'Moderate', 'Low'}
        # Extract base score (before any parenthetical context)
        base_score = v.split('(')[0].strip()
        if base_score not in allowed:
            raise ValueError(f"contrarian_opportunity_score must start with one of {allowed}, got '{v}'")
        return v
    
    @field_validator('relative_positioning')
    @classmethod
    def validate_relative_positioning(cls, v):
        """Ensure positioning analysis is meaningful"""
        if not v or not v.strip():
            raise ValueError("Relative positioning cannot be empty")
        
        clean_text = v.strip()
        if len(clean_text) < 100:
            raise ValueError(f"Relative positioning too brief: {len(clean_text)} chars (minimum 100)")
        
        return clean_text
    
    @field_validator('perception_gap_narrative')
    @classmethod
    def validate_perception_gap(cls, v):
        """Ensure perception gap narrative is meaningful"""
        if not v or not v.strip():
            raise ValueError("Perception gap narrative cannot be empty")
        
        clean_text = v.strip()
        if len(clean_text) < 150:
            raise ValueError(f"Perception gap narrative too brief: {len(clean_text)} chars (minimum 150)")
        
        return clean_text


# ============================================================================
# Section 3: Hidden Strengths
# ============================================================================

class HiddenStrength(BaseModel):
    """
    Individual hidden strength - a metric where target excels but market does not recognize.
    
    These are operational advantages that should command valuation premium but do not
    due to communication gaps or analyst blind spots.
    """
    metric_name: str = Field(..., description="Name of the metric (e.g., 'Reserve Development', 'Capital Efficiency')")
    target_value: float = Field(..., description="Target company's value")
    peer_average: float = Field(..., description="Peer group average for comparison")
    outperformance_magnitude: str = Field(
        ...,
        description="LLM-generated quantification of advantage. Example: '40% more consistent than PGR', '2.3x better than peer avg'"
    )
    why_wall_street_ignores: str = Field(
        ...,
        min_length=50,
        max_length=500,
        description="LLM-generated explanation of why analysts miss this strength. "
                    "Common reasons: complexity, lack of communication, non-standard metric, buried in disclosures."
    )
    valuation_impact: str = Field(
        ...,
        description="Estimated impact on valuation if properly recognized. Example: '+1.5x P/E multiple', '+15% to fair value'"
    )
    
    @field_validator('why_wall_street_ignores')
    @classmethod
    def validate_explanation(cls, v):
        if not v or not v.strip():
            raise ValueError("Explanation cannot be empty")
        
        clean_text = v.strip()
        if len(clean_text) < 50:
            raise ValueError(f"Explanation too brief: {len(clean_text)} chars (minimum 50)")
        
        return clean_text


class HiddenStrengthsInput(BaseModel):
    """
    Input data for generating Hidden Strengths section via LLM.
    
    Identifies metrics where target outperforms peers but receives no valuation credit.
    
    CALCULATION STRATEGY:
    - All mathematical comparisons pre-calculated in Python (no LLM math!)
    - LLM only generates narrative context ("why wall street ignores")
    - outperformance_magnitude_calculated: EXACT comparison string from Python
    - LLM copies this verbatim, does not recalculate
    """
    target_symbol: str = Field(..., description="Stock ticker symbol")
    
    # Metrics where target leads but has low P/E
    underappreciated_metrics: List[Dict[str, Any]] = Field(
        ...,
        min_length=1,
        description="List of metrics where target ranks #1 or #2 but has below-average P/E. "
                    "Each dict MUST include: "
                    "  - metric_name: str "
                    "  - target_value: float "
                    "  - peer_average: float "
                    "  - target_rank: int "
                    "  - peer_values: Dict[str, float] "
                    "  - outperformance_magnitude_calculated: str (PRE-CALCULATED comparison, LLM uses verbatim) "
                    "  - estimated_pe_impact: str (PRE-CALCULATED valuation impact) "
                    "  - peers_excluded: Optional[str] (Note about excluded peers due to data issues)"
    )
    
    # Peer company details for specific comparisons
    peer_details: List[Dict[str, Any]] = Field(
        ...,
        description="List of peer companies with their names and key data. "
                    "Each dict: {symbol: str, name: str, pe_ratio: float}"
    )
    
    # Valuation context (can be negative for unprofitable companies)
    current_pe: float = Field(..., description="Current P/E ratio (negative if unprofitable)")
    peer_average_pe: float = Field(..., description="Peer average P/E")
    
    @field_validator('underappreciated_metrics')
    @classmethod
    def validate_metrics_structure(cls, v):
        required_fields = {'metric_name', 'target_value', 'peer_average', 'target_rank'}
        
        for i, metric in enumerate(v, 1):
            if not isinstance(metric, dict):
                raise ValueError(f"Metric {i} must be a dictionary")
            
            missing = required_fields - set(metric.keys())
            if missing:
                raise ValueError(f"Metric {i} missing fields: {missing}")
        
        return v


class HiddenStrengths(BaseModel):
    """
    Section 3: Hidden Strengths - operational advantages that Wall Street ignores.
    
    This section identifies metrics where the target company significantly outperforms
    peers but receives no valuation credit, creating opportunities to close gaps through
    better investor communication and narrative positioning.
    
    Narrative Generation:
    - Primary Tool: src.metis.assistants.generic_llm_agent.py
    - Prompt File: prompts/competitive_analysis/hidden_strengths.txt
    - Method: generate_structured_output() with HiddenStrength schema
    - Input: HiddenStrengthsInput with underappreciated metrics data
    """
    strengths: List[HiddenStrength] = Field(
        ...,
        min_items=2,
        max_items=6,
        description="List of 2-6 hidden strengths. Focus on most impactful perception gaps."
    )
    
    aggregate_impact_estimate: str = Field(
        ...,
        description="LLM-generated total valuation impact if all strengths properly recognized. "
                    "Example: 'Closing these 4 perception gaps could justify +25-30% to fair value (14.5x-15x P/E)'"
    )
    
    communication_gap_summary: str = Field(
        ...,
        min_length=100,
        max_length=500,
        description="LLM-generated summary of why these strengths are missed. "
                    "Should identify common themes: complexity, disclosure gaps, non-standard metrics, etc."
    )
    
    @field_validator('communication_gap_summary')
    @classmethod
    def validate_summary(cls, v):
        if not v or not v.strip():
            raise ValueError("Summary cannot be empty")
        
        clean_text = v.strip()
        if len(clean_text) < 100:
            raise ValueError(f"Summary too brief: {len(clean_text)} chars (minimum 100)")
        
        return clean_text


class CompetitorMessagingPattern(BaseModel):
    """
    Successful messaging pattern from a peer company.
    
    Identifies specific language, narratives, and communication strategies that
    correlate with higher valuations for competitor companies.
    """
    competitor_symbol: str = Field(..., description="Peer company symbol (e.g., 'PGR', 'CB')")
    competitor_name: str = Field(..., description="Peer company name")
    
    narrative_theme: str = Field(
        ...,
        description="Core narrative theme. Example: 'tech moat', 'global diversification', 'stable and boring', 'turnaround story'"
    )
    
    key_phrases: List[str] = Field(
        ...,
        min_items=3,
        max_items=10,
        description="Exact phrases that appear frequently in earnings calls and correlate with valuation premium. "
                    "Example: ['technology platform', 'data-driven insights', 'telematics advantage']"
    )
    
    usage_frequency: str = Field(
        ...,
        description="LLM-generated frequency analysis. Example: 'PGR uses 'technology' 34x per earnings call vs WRB's 8x'"
    )
    
    analyst_adoption_rate: str = Field(
        ...,
        description="How often analysts echo this narrative. Example: 'appears in 47% of sell-side reports', 'mentioned 3.2x more than WRB'"
    )
    
    valuation_correlation: str = Field(
        ...,
        description="Estimated impact on valuation. Example: 'correlates with +6-8x P/E premium vs specialty insurers'"
    )
    
    steal_ability_assessment: str = Field(
        ...,
        min_length=50,
        max_length=300,
        description="LLM assessment of how target could adapt this narrative. "
                    "Example: 'WRB could credibly adopt tech narrative by rebranding specialty underwriting as AI-powered risk assessment'"
    )
    
    @field_validator('key_phrases')
    @classmethod
    def validate_phrases(cls, v):
        if len(v) < 3:
            raise ValueError("Must provide at least 3 key phrases")
        
        for phrase in v:
            if not phrase or not phrase.strip():
                raise ValueError("Key phrases cannot be empty")
        
        return v


class StealTheirPlaybookInput(BaseModel):
    """
    Input data for generating Steal Their Playbook section via LLM.
    
    Requires earnings transcript data and analyst report text for linguistic analysis.
    """
    target_symbol: str = Field(..., description="Stock ticker symbol")
    
    # Competitor data for analysis
    peer_companies: List[Dict[str, Any]] = Field(
        ...,
        min_length=2,
        description="Peer companies with their P/E and earnings transcript excerpts. "
                    "Each dict: {symbol: str, name: str, pe_ratio: float, transcript_text: str, analyst_mentions: int}"
    )
    
    # Target company baseline
    target_pe: float = Field(..., gt=0, description="Target P/E ratio")
    target_transcript_sample: str = Field(..., description="Sample from target's recent earnings calls")
    
    @field_validator('peer_companies')
    @classmethod
    def validate_peers(cls, v):
        required_fields = {'symbol', 'name', 'pe_ratio', 'transcript_text'}
        
        for i, peer in enumerate(v, 1):
            if not isinstance(peer, dict):
                raise ValueError(f"Peer {i} must be a dictionary")
            
            missing = required_fields - set(peer.keys())
            if missing:
                raise ValueError(f"Peer {i} missing fields: {missing}")
        
        return v


class StealTheirPlaybook(BaseModel):
    """
    Section 4: "Steal Their Playbook" - successful competitor messaging patterns.
    
    This section uses linguistic analysis of earnings transcripts and analyst reports
    to identify specific narratives, phrases, and positioning strategies that correlate
    with higher valuations, providing actionable templates for improving target's
    investor communication.
    
    Narrative Generation:
    - Primary Tool: src.metis.assistants.linguistic_analysis_agent.py
    - Prompt File: prompts/linguistic_analysis/competitor_messaging.txt
    - Method: analyze_competitor_messaging() with transcript text analysis
    - Input: StealTheirPlaybookInput with earnings call transcripts
    - Output: List of CompetitorMessagingPattern with linguistic evidence
    """
    messaging_patterns: List[CompetitorMessagingPattern] = Field(
        ...,
        min_items=3,
        max_items=8,
        description="List of 3-8 successful messaging patterns from peers. Prioritize patterns with strongest valuation correlation."
    )
    
    linguistic_gap_summary: str = Field(
        ...,
        min_length=100,
        max_length=500,
        description="LLM-generated summary of target's linguistic gaps vs high-multiple peers. "
                    "Example: 'WRB uses tech terminology 4.2x less than PGR, mentions 'data' 68% less than CB, "
                    "provides 23% fewer quantitative forward statements than TRV'"
    )
    
    priority_messaging_shifts: List[str] = Field(
        ...,
        min_items=3,
        max_items=5,
        description="Top 3-5 messaging changes target should prioritize. "
                    "Example: '1) Rebrand specialty underwriting as AI-powered decisioning, "
                    "2) Increase quantitative guidance statements by 80%, 3) Add monthly tech update section'"
    )
    
    @field_validator('messaging_patterns')
    @classmethod
    def validate_patterns(cls, v):
        if len(v) < 3:
            raise ValueError("Must identify at least 3 messaging patterns")
        return v


class ValuationGapFactor(BaseModel):
    """
    Individual factor contributing to P/E valuation gap.
    
    Decomposes why target trades at discount vs specific peer, isolating
    fundamental vs perception-driven components.
    """
    peer_symbol: str = Field(..., description="Peer company symbol")
    peer_name: str = Field(..., description="Peer company name")
    peer_pe: float = Field(..., gt=0, description="Peer P/E ratio")
    target_pe: float = Field(..., gt=0, description="Target P/E ratio")
    pe_gap: float = Field(..., description="P/E difference (peer_pe - target_pe)")
    
    fundamental_justified_gap: float = Field(
        ...,
        description="Portion of gap justified by fundamental differences (ROE, growth, risk). "
                    "Calculated via multi-factor regression model."
    )
    
    perception_driven_gap: float = Field(
        ...,
        description="Portion of gap driven by narrative/perception (not fundamental). "
                    "This is the actionable opportunity."
    )
    
    key_narrative_advantage: str = Field(
        ...,
        description="LLM-generated explanation of peer's narrative edge. "
                    "Example: 'simplified data company story', 'global diversification safety perception', 'turnaround momentum'"
    )
    
    gap_closure_pathway: str = Field(
        ...,
        min_length=50,
        max_length=300,
        description="LLM recommendation for closing perception gap. "
                    "Example: 'Adopt tech-centric positioning + quarterly data/analytics updates could justify +4-5x P/E recovery'"
    )


class ValuationForensicsInput(BaseModel):
    """
    Input data for generating Valuation Forensics section via LLM.
    
    Requires detailed financial metrics and transcript data for multi-factor analysis.
    """
    target_symbol: str = Field(..., description="Stock ticker symbol")
    target_pe: float = Field(..., gt=0, description="Target P/E ratio")
    
    # Peer financial data for regression
    peer_financial_data: List[Dict[str, Any]] = Field(
        ...,
        min_length=3,
        description="Financial metrics for each peer. Each dict must contain: "
                    "{symbol: str, name: str, pe_ratio: float, roe: float, revenue_growth: float, "
                    "debt_equity: float, beta: float, analyst_coverage: int}"
    )
    
    # Target fundamentals for comparison
    target_fundamentals: Dict[str, float] = Field(
        ...,
        description="Target's fundamental metrics matching peer data structure"
    )
    
    @field_validator('peer_financial_data')
    @classmethod
    def validate_peer_data(cls, v):
        required_fields = {'symbol', 'name', 'pe_ratio', 'roe', 'revenue_growth'}
        
        for i, peer in enumerate(v, 1):
            if not isinstance(peer, dict):
                raise ValueError(f"Peer {i} must be a dictionary")
            
            missing = required_fields - set(peer.keys())
            if missing:
                raise ValueError(f"Peer {i} missing required fields: {missing}")
        
        return v


class ValuationForensics(BaseModel):
    """
    Section 5: Valuation Gap Forensics - multi-factor decomposition of P/E discount.
    
    This section performs advanced valuation analysis to separate fundamental-justified
    gaps from perception-driven gaps, identifying specific actionable opportunities to
    close valuation discounts through improved narrative and investor communication.
    
    Narrative Generation:
    - Primary Tool: src.metis.assistants.valuation_gap_analyzer.py
    - Prompt File: prompts/valuation_analysis/gap_decomposition.txt
    - Method: analyze_valuation_gaps() with multi-factor regression
    - Input: ValuationForensicsInput with full financial metrics
    - Output: List of ValuationGapFactor with fundamental vs perception split
    """
    gap_factors: List[ValuationGapFactor] = Field(
        ...,
        min_items=2,
        max_items=6,
        description="Decomposition of P/E gaps vs 2-6 key peers. Focus on largest/most actionable gaps."
    )
    
    aggregate_perception_opportunity: str = Field(
        ...,
        description="LLM-generated summary of total perception-driven discount. "
                    "Example: 'Total perception gap across peer set: 4.2x P/E (35% undervaluation), "
                    "with 2.8x addressable through narrative improvements'"
    )
    
    ranked_closure_recommendations: List[str] = Field(
        ...,
        min_items=5,
        max_items=18,
        description="Ranked list of specific actions to close valuation gaps, ordered by estimated impact. "
                    "Example: '1) Quarterly tech showcase (+2.5x P/E), 2) Simplify segment reporting (+1.8x P/E), "
                    "3) Adopt PGR's guidance style (+1.2x P/E)'"
    )
    
    valuation_bridge_summary: str = Field(
        ...,
        min_length=150,
        max_length=600,
        description="LLM-generated valuation bridge narrative showing path from current to fair value. "
                    "Example: 'Current 12.1x + tech narrative adoption (2.5x) + improved disclosure (1.0x) + "
                    "market cap scale premium (0.9x) = 16.5x fair value P/E (+36% upside)'"
    )
    
    @field_validator('ranked_closure_recommendations')
    @classmethod
    def validate_recommendations(cls, v):
        if len(v) < 5:
            raise ValueError("Must provide at least 5 ranked recommendations")
        
        for i, rec in enumerate(v, 1):
            if not rec or not rec.strip():
                raise ValueError(f"Recommendation {i} cannot be empty")
        
        return v


class Recommendation(BaseModel):
    """Individual actionable recommendation in Do/Say/Show framework."""
    title: str = Field(..., min_length=10, description="Brief title of the recommendation")
    description: str = Field(..., min_length=50, description="Detailed description")
    category: RecommendationCategory = Field(..., description="Category (do/say/show)")
    priority: RecommendationPriority = Field(..., description="Priority level")
    expected_impact: str = Field(
        ...,
        description="Expected impact if implemented. Must include quantitative estimate. "
                    "Example: '+1.5x P/E multiple', '+15% to fair value', 'Reduce analyst confusion by 40%'"
    )
    implementation_effort: str = Field(
        ...,
        description="Estimated effort/timeline. Example: 'Quick win (1-2 months)', 'Medium-term (3-6 months)', 'Long-term (6-12 months)'"
    )
    peer_precedent: Optional[str] = Field(
        None,
        description="Optional reference to peer company that successfully executed similar action. Example: 'Hartford's 2022 turnaround playbook'"
    )
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError("Title too brief (minimum 10 characters)")
        return v.strip()
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if not v or len(v.strip()) < 50:
            raise ValueError("Description too brief (minimum 50 characters)")
        return v.strip()


class ActionableProblem(BaseModel):
    """Problem-solution pair structure for Actionable Roadmap."""
    problem_statement: str = Field(
        ...,
        min_length=30,
        description="Clear problem statement as question. Example: 'Why does Progressive trade at 20x when we have better metrics?'"
    )
    root_causes: List[str] = Field(
        ...,
        min_items=1,
        max_items=5,
        description="1-5 identified root causes of the problem"
    )
    solutions: List[Recommendation] = Field(
        ...,
        min_items=2,
        max_items=8,
        description="2-8 specific, actionable recommendations to address this problem"
    )
    tracking_metrics: List[str] = Field(
        ...,
        min_items=1,
        max_items=5,
        description="1-5 metrics to track progress. Example: 'Monthly analyst mention count', 'Quarterly sentiment score'"
    )
    
    @field_validator('problem_statement')
    @classmethod
    def validate_problem(cls, v):
        if not v or len(v.strip()) < 30:
            raise ValueError("Problem statement too brief (minimum 30 characters)")
        return v.strip()


class ActionableRoadmapInput(BaseModel):
    """Input data for generating Actionable Roadmap section via LLM."""
    target_symbol: str = Field(..., description="Stock ticker symbol")
    
    # Key gaps identified from previous sections
    valuation_gap_magnitude: float = Field(..., description="Total P/E gap vs peers")
    perception_gaps: List[str] = Field(..., description="Identified perception gaps from all sections")
    hidden_strengths: List[str] = Field(..., description="Underappreciated metrics from Section 3")
    successful_peer_strategies: List[str] = Field(..., description="Messaging patterns from Section 4")
    
    # Context for prioritization
    most_impactful_opportunities: List[Dict[str, Any]] = Field(
        ...,
        description="Top opportunities ranked by estimated valuation impact"
    )


class ActionableRoadmap(BaseModel):
    """
    Section 6: Actionable Fix Roadmap - problem-solution framework with ranked recommendations.
    
    This section translates all analysis findings into specific, actionable recommendations
    organized by problem areas, with clear implementation guidance, impact estimates,
    and success metrics. Uses Do/Say/Show categorization for clarity.
    
    Narrative Generation:
    - Primary Tool: src.metis.assistants.generic_llm_agent.py
    - Prompt File: prompts/recommendations/actionable_roadmap.txt
    - Method: generate_structured_output() with ActionableProblem schema
    - Input: ActionableRoadmapInput with gaps and opportunities from all sections
    - Output: List of ActionableProblem with ranked, categorized recommendations
    """
    problems: List[ActionableProblem] = Field(
        ...,
        min_items=3,
        max_items=6,
        description="3-6 key problems with solutions. Example problems: valuation gap, analyst confusion, "
                    "communication gaps, buyback timing, competitive positioning"
    )
    
    priority_quick_wins: List[str] = Field(
        ...,
        min_items=3,
        max_items=5,
        description="Top 3-5 highest-impact, lowest-effort recommendations for immediate execution. "
                    "Example: 'Add tech terminology to next earnings call (+1.2x P/E, 1 month effort)'"
    )
    
    monthly_progress_framework: str = Field(
        ...,
        min_length=100,
        max_length=500,
        description="LLM-generated framework for tracking monthly progress. "
                    "Should cover: messaging changes → sentiment shifts → analyst coverage → multiple expansion. "
                    "Example: 'Month 1-3: Deploy new tech narrative (track: mention frequency), Month 4-6: Monitor analyst adoption...' "
    )
    
    estimated_timeline_to_target_multiple: str = Field(
        ...,
        description="Estimated timeline to close valuation gap. Example: '12-18 months to reach 14.5x-15x P/E (vs current 12.1x)'"
    )
    
    @field_validator('problems')
    @classmethod
    def validate_problems(cls, v):
        if len(v) < 3:
            raise ValueError("Must identify at least 3 key problems with solutions")
        return v
    
    @field_validator('monthly_progress_framework')
    @classmethod
    def validate_framework(cls, v):
        if not v or len(v.strip()) < 100:
            raise ValueError("Progress framework too brief (minimum 100 characters)")
        return v.strip()


# Main Report Model
class CompetitiveIntelligenceReport(BaseModel):
    """
    Complete competitive intelligence report with all 6 sections.
    
    This is the top-level schema that combines all report sections into a unified,
    validated structure ready for delivery to clients or WordPress publication.
    
    Section Structure:
    1. Executive Summary - High-level findings and top recommendations
    2. Competitive Dashboard - Metric-by-metric comparison with market perception
    3. Hidden Strengths - Underappreciated operational advantages
    4. Steal Their Playbook - Successful competitor messaging patterns
    5. Valuation Forensics - Multi-factor P/E gap decomposition
    6. Actionable Roadmap - Problem-solution framework with ranked actions
    """
    metadata: ReportMetadata = Field(..., description="Report metadata and generation info")
    methodology: ReportMethodology = Field(default_factory=ReportMethodology, description="Explanation of analytical methodology and limitations")
    data_sources: List[DataSource] = Field(..., description="Data sources used in analysis")
    peer_group: PeerGroup = Field(..., description="Target company and analyzed peers")
    valuation_context: Optional[ValuationContext] = Field(None, description="Valuation summary for quick reference")
    
    # Section 1: Executive Summary
    executive_summary: ExecutiveSummary = Field(..., description="Section 1: High-level narrative overview")
    
    # Section 2: Competitive Dashboard
    competitive_dashboard: CompetitiveDashboard = Field(..., description="Section 2: Detailed metric comparisons")
    
    # Section 3: Hidden Strengths
    hidden_strengths: HiddenStrengths = Field(..., description="Section 3: Underappreciated operational advantages")
    
    # Section 4: Steal Their Playbook
    steal_their_playbook: StealTheirPlaybook = Field(..., description="Section 4: Successful competitor messaging")
    
    # Section 5: Valuation Forensics
    valuation_forensics: ValuationForensics = Field(..., description="Section 5: P/E gap decomposition")
    
    # Section 6: Actionable Roadmap
    actionable_roadmap: ActionableRoadmap = Field(..., description="Section 6: Ranked recommendations")
    
    @model_validator(mode='after')
    def validate_symbol_consistency(self) -> 'CompetitiveIntelligenceReport':
        """Ensure target symbol is consistent across all sections"""
        target_symbol = self.metadata.target_symbol
        
        if self.peer_group.target_company.symbol != target_symbol:
            raise ValueError(f"Target symbol mismatch: metadata={target_symbol} vs peer_group={self.peer_group.target_company.symbol}")
        
        # Validate peer count consistency
        peer_count = len(self.peer_group.peers)
        dashboard_peer_count = len(self.competitive_dashboard.metrics[0].peer_values) if self.competitive_dashboard.metrics else 0
        
        if peer_count != dashboard_peer_count:
            raise ValueError(f"Peer count mismatch: peer_group has {peer_count} peers but dashboard shows {dashboard_peer_count}")
        
        return self


# Export all models
__all__ = [
    # Enums
    'DataQuality',
    'RecommendationPriority', 
    'RecommendationCategory',
    'MarketPerception',
    
    # Input Models (for LLM generation)
    'ExecutiveSummaryInput',
    'CompetitiveDashboardInput',
    'HiddenStrengthsInput',
    'StealTheirPlaybookInput',
    'ValuationForensicsInput',
    'ActionableRoadmapInput',
    # Core Data Models
    'ReportMetadata',
    'ReportMethodology',
    'DataSource',
    'CompanyProfile',
    'PeerCompany',
    'PeerGroup',
    'PeerSelectionRationale',
    'MetricComparison',
    
    # Section Models (Output)
    'ExecutiveSummary',
    'CompetitiveMetric',
    'CompetitiveDashboard',
    'HiddenStrength',
    'HiddenStrengths',
    'CompetitorMessagingPattern',
    'StealTheirPlaybook',
    'ValuationGapFactor',
    'ValuationForensics',
    'Recommendation',
    'ActionableProblem',
    'ActionableRoadmap',
    
    # Main Report
    'CompetitiveIntelligenceReport'
]