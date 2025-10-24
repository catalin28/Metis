"""
Competitive Intelligence Report Schema Models

This module defines the complete Pydantic model structure for competitive intelligence
reports, ensuring type safety and validation for all report components.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator, model_validator
import re


# Enums for controlled vocabularies
class DataQuality(str, Enum):
    """Data quality indicators"""
    VALID = "valid"
    ESTIMATED = "estimated"
    OUTLIER = "outlier"
    EXCLUDED = "excluded"
    STALE = "stale"


class MarketPerceptionCategory(str, Enum):
    """Market perception categories"""
    UNDERVALUED = "undervalued"
    UNDERAPPRECIATED = "underappreciated"
    HIDDEN_STRENGTH = "hidden_strength"
    FAIR_VALUE = "fair_value"
    PREMIUM = "premium"
    OVERVALUED = "overvalued"


class RecommendationCategory(str, Enum):
    """Recommendation action categories"""
    DO = "DO"
    SAY = "SAY"
    SHOW = "SHOW"


class Priority(str, Enum):
    """Priority levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConfidenceLevel(str, Enum):
    """Confidence levels for analysis"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Base Models
class TimestampedModel(BaseModel):
    """Base model with timestamp and data quality tracking"""
    calculation_date: datetime = Field(default_factory=datetime.now)
    data_quality: DataQuality = Field(default=DataQuality.VALID)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MetricValue(TimestampedModel):
    """Base model for financial metric values"""
    symbol: str = Field(..., min_length=1, max_length=10)
    value: float = Field(..., description="Metric value")
    rank: Optional[int] = Field(None, ge=1, description="Ranking among peers (1=best)")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if not re.match(r'^[A-Z]{1,10}$', v):
            raise ValueError('Symbol must be uppercase letters only, 1-10 characters')
        return v


# Report Metadata Models
class ProcessingMetadata(BaseModel):
    """Processing and performance metadata"""
    processing_duration_ms: Optional[float] = None
    api_calls_made: int = Field(default=0)
    llm_tokens_used: int = Field(default=0)
    cost_estimate_usd: Optional[float] = None
    confidence_score: float = Field(default=100.0, ge=0.0, le=100.0)
    data_sources: List[str] = Field(default_factory=list)
    
    @validator('data_sources')
    def validate_data_sources(cls, v):
        valid_sources = {'FMP', 'OPENAI', 'MANUAL', 'CACHED'}
        for source in v:
            if source not in valid_sources:
                raise ValueError(f'Invalid data source: {source}')
        return v


class ReportMetadata(BaseModel):
    """Report identification and metadata"""
    report_id: str = Field(default_factory=lambda: str(uuid4()))
    generated_at: datetime = Field(default_factory=datetime.now)
    schema_version: str = Field(default="1.0")
    target_symbol: str = Field(..., min_length=1, max_length=10)
    client_id: str = Field(..., min_length=1)
    processing_metadata: ProcessingMetadata = Field(default_factory=ProcessingMetadata)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @validator('target_symbol')
    def validate_target_symbol(cls, v):
        if not re.match(r'^[A-Z]{1,10}$', v):
            raise ValueError('Target symbol must be uppercase letters only')
        return v


# Company Profile Models
class CompanyProfile(TimestampedModel):
    """Target company basic information"""
    symbol: str = Field(..., min_length=1, max_length=10)
    company_name: str = Field(..., min_length=1)
    sector: str = Field(..., min_length=1)
    industry: str = Field(..., min_length=1)
    market_cap_billions: float = Field(..., gt=0)
    country: str = Field(default="US")
    currency: str = Field(default="USD")
    exchange: str = Field(default="NASDAQ")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if not re.match(r'^[A-Z]{1,10}$', v):
            raise ValueError('Symbol must be uppercase letters only')
        return v


# Peer Group Models
class PeerCompany(BaseModel):
    """Individual peer company information"""
    symbol: str = Field(..., min_length=1, max_length=10)
    company_name: str = Field(..., min_length=1)
    similarity_score: float = Field(..., ge=0.0, le=100.0)
    selection_method: str = Field(default="automated")
    manual_override: bool = Field(default=False)
    inclusion_reason: str = Field(..., min_length=1)
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if not re.match(r'^[A-Z]{1,10}$', v):
            raise ValueError('Symbol must be uppercase letters only')
        return v


class PeerGroup(TimestampedModel):
    """Peer group definition and metadata"""
    target_symbol: str = Field(..., min_length=1, max_length=10)
    peers: List[PeerCompany] = Field(..., min_items=3, max_items=10)
    selection_criteria: str = Field(..., min_length=1)
    methodology: str = Field(default="market_cap_sector_similarity")
    
    @validator('peers')
    def validate_unique_peers(cls, v):
        symbols = [peer.symbol for peer in v]
        if len(symbols) != len(set(symbols)):
            raise ValueError('Peer symbols must be unique')
        return v
    
    @root_validator
    def validate_target_not_in_peers(cls, values):
        target = values.get('target_symbol')
        peers = values.get('peers', [])
        
        if target and any(peer.symbol == target for peer in peers):
            raise ValueError('Target symbol cannot be included in peer group')
        return values


# Financial Metrics Models
class MarketPerceptionAnalysis(BaseModel):
    """LLM-generated market perception analysis"""
    category: MarketPerceptionCategory
    explanation: str = Field(..., min_length=50, max_length=500)
    analysis: Dict[str, Any] = Field(...)
    calculation_date: datetime = Field(default_factory=datetime.now)
    
    @validator('analysis')
    def validate_analysis_structure(cls, v):
        required_keys = {'primary_driver', 'market_bias', 'potential_catalyst', 'confidence_level'}
        if not required_keys.issubset(v.keys()):
            missing = required_keys - v.keys()
            raise ValueError(f'Analysis missing required keys: {missing}')
        return v


class CompetitiveDashboardCompany(BaseModel):
    """Individual company data in competitive dashboard"""
    symbol: str = Field(..., min_length=1, max_length=10)
    company_name: str = Field(..., min_length=1)
    market_cap_billions: float = Field(..., gt=0)
    pe_ratio: float = Field(..., gt=0)
    roe_percentage: float = Field(..., ge=-100, le=200)
    revenue_growth_percentage: float = Field(..., ge=-100, le=1000)
    debt_to_equity: float = Field(..., ge=0)
    combined_ratio: Optional[float] = Field(None, gt=0, le=200)
    management_sentiment_score: int = Field(..., ge=0, le=100)
    analyst_confusion_score: int = Field(..., ge=0, le=100)
    overall_rank: int = Field(..., ge=1)
    market_perception: MarketPerceptionAnalysis
    rankings: Dict[str, int] = Field(default_factory=dict)
    calculation_date: datetime = Field(default_factory=datetime.now)
    data_quality: DataQuality = Field(default=DataQuality.VALID)
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if not re.match(r'^[A-Z]{1,10}$', v):
            raise ValueError('Symbol must be uppercase letters only')
        return v


class SummaryStatistics(BaseModel):
    """Dashboard summary statistics"""
    target_symbol: str = Field(..., min_length=1, max_length=10)
    peer_count: int = Field(..., ge=3, le=10)
    metrics_calculated: int = Field(..., ge=1)
    averages: Dict[str, float] = Field(default_factory=dict)
    target_vs_peer_gaps: Dict[str, float] = Field(default_factory=dict)


class OutlierAnalysis(BaseModel):
    """Statistical outlier analysis"""
    outliers: List[Dict[str, Any]] = Field(default_factory=list)
    best_performers: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    worst_performers: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class CompetitiveDashboard(TimestampedModel):
    """Complete competitive dashboard section"""
    companies: List[CompetitiveDashboardCompany] = Field(..., min_items=4, max_items=11)
    summary_statistics: SummaryStatistics
    outlier_analysis: OutlierAnalysis
    
    @validator('companies')
    def validate_unique_companies(cls, v):
        symbols = [company.symbol for company in v]
        if len(symbols) != len(set(symbols)):
            raise ValueError('Company symbols must be unique')
        return v


# Executive Summary Models
class ExecutiveSummary(TimestampedModel):
    """Executive summary with key findings"""
    company_overview: str = Field(..., min_length=200, max_length=1000)
    key_finding: str = Field(..., min_length=100, max_length=500)
    root_cause: str = Field(..., min_length=50, max_length=300)
    top_recommendations: List[str] = Field(..., min_items=3, max_items=5)
    
    @validator('top_recommendations')
    def validate_recommendation_length(cls, v):
        for rec in v:
            if len(rec) < 20 or len(rec) > 200:
                raise ValueError('Each recommendation must be 20-200 characters')
        return v


# Hidden Strengths Models
class HiddenStrength(BaseModel):
    """Individual hidden strength analysis"""
    title: str = Field(..., min_length=10, max_length=100)
    description: str = Field(..., min_length=50, max_length=500)
    quantification: str = Field(..., min_length=20, max_length=200)
    why_hidden: str = Field(..., min_length=30, max_length=300)
    valuation_impact: Optional[float] = Field(None, description="Estimated P/E impact")


class HiddenStrengths(TimestampedModel):
    """Hidden strengths section"""
    strengths: List[HiddenStrength] = Field(..., min_items=3, max_items=7)


# Competitive Strategy Models
class LinguisticData(BaseModel):
    """Linguistic analysis data for competitor messaging"""
    phrase: str = Field(..., min_length=1)
    target_frequency: int = Field(..., ge=0)
    peer_frequency: int = Field(..., ge=0)
    correlation_with_premium: Optional[float] = Field(None, ge=-1.0, le=1.0)


class CompetitorStrategy(BaseModel):
    """Individual competitor strategy analysis"""
    peer_symbol: str = Field(..., min_length=1, max_length=10)
    strategy_name: str = Field(..., min_length=5, max_length=100)
    impact_description: str = Field(..., min_length=20, max_length=300)
    linguistic_data: LinguisticData
    recommendation: str = Field(..., min_length=30, max_length=500)
    estimated_pe_impact: Optional[float] = Field(None, description="Estimated P/E multiple impact")


class StealTheirPlaybook(TimestampedModel):
    """Competitive strategy analysis section"""
    competitor_strategies: List[CompetitorStrategy] = Field(..., min_items=2, max_items=6)


# Valuation Analysis Models
class ValuationBridgeComponent(BaseModel):
    """Individual component of valuation bridge"""
    name: str = Field(..., min_length=5, max_length=50)
    value: float = Field(...)
    cumulative: float = Field(...)
    explanation: str = Field(..., min_length=30, max_length=300)


class ValuationBridge(BaseModel):
    """Complete valuation bridge analysis"""
    components: List[ValuationBridgeComponent] = Field(..., min_items=3, max_items=8)
    
    @root_validator
    def validate_bridge_consistency(cls, values):
        components = values.get('components', [])
        if len(components) < 2:
            return values
            
        # Validate cumulative values are consistent
        for i in range(1, len(components)):
            expected = components[i-1].cumulative + components[i].value
            actual = components[i].cumulative
            if abs(expected - actual) > 0.01:  # Allow small rounding differences
                raise ValueError(f'Valuation bridge cumulative values inconsistent at component {i}')
        
        return values


class GapDecomposition(BaseModel):
    """Valuation gap decomposition analysis"""
    fundamental_component: float = Field(...)
    narrative_component: float = Field(...)
    
    @root_validator
    def validate_gap_components(cls, values):
        fund = values.get('fundamental_component', 0)
        narr = values.get('narrative_component', 0)
        total = fund + narr
        
        # Store total for reference
        values['total_gap'] = total
        return values


class ValuationForensics(TimestampedModel):
    """Valuation forensics analysis section"""
    current_pe: float = Field(..., gt=0)
    peer_average_pe: float = Field(..., gt=0)
    total_gap: float = Field(...)
    gap_decomposition: GapDecomposition
    valuation_bridge: ValuationBridge
    
    @root_validator
    def validate_valuation_consistency(cls, values):
        current = values.get('current_pe')
        peer_avg = values.get('peer_average_pe')
        total_gap = values.get('total_gap')
        
        if current and peer_avg:
            expected_gap = current - peer_avg
            if abs(expected_gap - total_gap) > 0.01:
                raise ValueError('Total gap must equal current_pe - peer_average_pe')
        
        return values


# Recommendations Models
class ActionableRecommendation(BaseModel):
    """Individual actionable recommendation"""
    id: int = Field(..., ge=1)
    category: RecommendationCategory
    priority: Priority
    problem: str = Field(..., min_length=20, max_length=300)
    solution: str = Field(..., min_length=30, max_length=500)
    action: str = Field(..., min_length=20, max_length=300)
    expected_impact: str = Field(..., min_length=10, max_length=100)
    timeline: str = Field(..., min_length=5, max_length=50)
    implementation: str = Field(..., min_length=30, max_length=500)
    estimated_pe_impact: Optional[float] = Field(None, description="Estimated P/E multiple impact")


class ActionableRoadmap(TimestampedModel):
    """Actionable recommendations section"""
    recommendations: List[ActionableRecommendation] = Field(..., min_items=10, max_items=25)
    
    @validator('recommendations')
    def validate_unique_ids(cls, v):
        ids = [rec.id for rec in v]
        if len(ids) != len(set(ids)):
            raise ValueError('Recommendation IDs must be unique')
        return v
    
    @validator('recommendations')
    def validate_priority_distribution(cls, v):
        high_count = sum(1 for rec in v if rec.priority == Priority.HIGH)
        if high_count > len(v) * 0.4:  # Max 40% high priority
            raise ValueError('Too many high priority recommendations (max 40%)')
        return v


# Main Report Model
class CompetitiveIntelligenceReport(BaseModel):
    """Complete competitive intelligence report"""
    report_metadata: ReportMetadata
    company_profile: CompanyProfile
    peer_group: PeerGroup
    executive_summary: ExecutiveSummary
    competitive_dashboard: CompetitiveDashboard
    hidden_strengths: HiddenStrengths
    steal_their_playbook: StealTheirPlaybook
    valuation_forensics: ValuationForensics
    actionable_roadmap: ActionableRoadmap
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "report_metadata": {
                    "target_symbol": "WRB",
                    "client_id": "enterprise_client_123",
                    "schema_version": "1.0"
                },
                "company_profile": {
                    "symbol": "WRB",
                    "company_name": "W.R. Berkley Corporation",
                    "sector": "Financial Services",
                    "industry": "Insurance",
                    "market_cap_billions": 12.5
                }
            }
        }
    
    @root_validator
    def validate_symbol_consistency(cls, values):
        """Ensure target symbol is consistent across all sections"""
        metadata = values.get('report_metadata')
        profile = values.get('company_profile')
        peer_group = values.get('peer_group')
        dashboard = values.get('competitive_dashboard')
        
        if not metadata:
            return values
            
        target_symbol = metadata.target_symbol
        
        # Check profile consistency
        if profile and profile.symbol != target_symbol:
            raise ValueError('Company profile symbol must match report metadata target symbol')
        
        # Check peer group consistency
        if peer_group and peer_group.target_symbol != target_symbol:
            raise ValueError('Peer group target symbol must match report metadata')
        
        # Check dashboard consistency
        if dashboard:
            target_in_dashboard = any(
                comp.symbol == target_symbol for comp in dashboard.companies
            )
            if not target_in_dashboard:
                raise ValueError('Target company must be included in competitive dashboard')
        
        return values
    
    def get_target_company_data(self) -> Optional[CompetitiveDashboardCompany]:
        """Get target company data from competitive dashboard"""
        target_symbol = self.report_metadata.target_symbol
        for company in self.competitive_dashboard.companies:
            if company.symbol == target_symbol:
                return company
        return None
    
    def validate_report_completeness(self) -> Dict[str, bool]:
        """Validate that all required sections have sufficient data"""
        completeness = {
            "executive_summary": len(self.executive_summary.company_overview) >= 200,
            "competitive_dashboard": len(self.competitive_dashboard.companies) >= 4,
            "hidden_strengths": len(self.hidden_strengths.strengths) >= 3,
            "steal_their_playbook": len(self.steal_their_playbook.competitor_strategies) >= 2,
            "valuation_forensics": len(self.valuation_forensics.valuation_bridge.components) >= 3,
            "actionable_roadmap": len(self.actionable_roadmap.recommendations) >= 10
        }
        
        completeness["overall"] = all(completeness.values())
        return completeness