"""
Report Builder for Competitive Intelligence Reports (v2)

This module provides a fluent API for assembling competitive intelligence reports
with integrated validation and error handling.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from ..models.report_schema_v2 import (
    CompetitiveIntelligenceReport,
    ReportMetadata,
    DataSource,
    DataQuality,
    CompanyProfile,
    PeerCompany,
    PeerGroup,
    ExecutiveSummary,
    CompetitiveDashboard,
    MetricComparison,
    Recommendation,
    RecommendationCategory,
    RecommendationPriority,
    ActionableRoadmap
)
from ..utils.schema_validator_v2_simple import CompetitiveIntelligenceReportValidator
from ..models.validation_models import ValidationResult, ValidationSeverity


class CompetitiveIntelligenceReportBuilder:
    """
    Fluent API builder for constructing competitive intelligence reports
    with comprehensive validation and error handling.
    """
    
    def __init__(self):
        """Initialize the builder with empty state"""
        self.reset()
    
    def reset(self) -> 'CompetitiveIntelligenceReportBuilder':
        """Reset the builder to initial state"""
        self._metadata: Optional[ReportMetadata] = None
        self._data_sources: List[DataSource] = []
        self._target_company: Optional[CompanyProfile] = None
        self._peers: List[PeerCompany] = []
        self._discovery_method: str = "manual"
        self._executive_summary: Optional[ExecutiveSummary] = None
        self._metric_comparisons: List[MetricComparison] = []
        self._dashboard_ranking: int = 1
        self._dashboard_strengths: List[str] = []
        self._dashboard_weaknesses: List[str] = []
        self._recommendations: List[Recommendation] = []
        self._implementation_timeline: str = ""
        self._success_metrics: List[str] = []
        
        self._validator = CompetitiveIntelligenceReportValidator()
        
        return self
    
    # Metadata methods
    def set_metadata(self, target_symbol: str, report_id: Optional[str] = None, 
                    version: str = "1.0") -> 'CompetitiveIntelligenceReportBuilder':
        """Set report metadata"""
        self._metadata = ReportMetadata(
            report_id=report_id or str(uuid.uuid4()),
            target_symbol=target_symbol,
            version=version
        )
        return self
    
    def set_processing_time(self, seconds: float) -> 'CompetitiveIntelligenceReportBuilder':
        """Set processing time in metadata"""
        if self._metadata:
            self._metadata.processing_time_seconds = seconds
        return self
    
    # Data source methods
    def add_data_source(self, source_type: str, provider: str, 
                       quality: DataQuality = DataQuality.VALID,
                       data_date: Optional[datetime] = None) -> 'CompetitiveIntelligenceReportBuilder':
        """Add a data source"""
        data_source = DataSource(
            source_type=source_type,
            provider=provider,
            quality=quality,
            data_date=data_date
        )
        self._data_sources.append(data_source)
        return self
    
    # Company and peer methods
    def set_target_company(self, symbol: str, company_name: str, sector: str,
                          market_cap: Optional[float] = None, 
                          pe_ratio: Optional[float] = None,
                          revenue_ttm: Optional[float] = None) -> 'CompetitiveIntelligenceReportBuilder':
        """Set the target company information"""
        self._target_company = CompanyProfile(
            symbol=symbol,
            company_name=company_name,
            sector=sector,
            market_cap=market_cap,
            pe_ratio=pe_ratio,
            revenue_ttm=revenue_ttm
        )
        return self
    
    def add_peer_company(self, symbol: str, company_name: str, 
                        similarity_score: float) -> 'CompetitiveIntelligenceReportBuilder':
        """Add a peer company"""
        peer = PeerCompany(
            symbol=symbol,
            company_name=company_name,
            similarity_score=similarity_score
        )
        self._peers.append(peer)
        return self
    
    def set_peer_discovery_method(self, method: str) -> 'CompetitiveIntelligenceReportBuilder':
        """Set the peer discovery method"""
        self._discovery_method = method
        return self
    
    # Executive summary methods
    def set_executive_summary(self, overview: str, key_insights: List[str],
                             top_recommendations: List[str]) -> 'CompetitiveIntelligenceReportBuilder':
        """Set the executive summary"""
        self._executive_summary = ExecutiveSummary(
            overview=overview,
            key_insights=key_insights,
            top_recommendations=top_recommendations
        )
        return self
    
    # Dashboard methods
    def add_metric_comparison(self, metric_name: str, target_value: Optional[float],
                             peer_values: Dict[str, float], target_ranking: Optional[int],
                             analysis: str) -> 'CompetitiveIntelligenceReportBuilder':
        """Add a metric comparison"""
        comparison = MetricComparison(
            metric_name=metric_name,
            target_value=target_value,
            peer_values=peer_values,
            target_ranking=target_ranking,
            analysis=analysis
        )
        self._metric_comparisons.append(comparison)
        return self
    
    def set_competitive_dashboard(self, overall_ranking: int, strengths: List[str],
                                 weaknesses: List[str]) -> 'CompetitiveIntelligenceReportBuilder':
        """Set competitive dashboard information"""
        self._dashboard_ranking = overall_ranking
        self._dashboard_strengths = strengths
        self._dashboard_weaknesses = weaknesses
        return self
    
    # Recommendations methods
    def add_recommendation(self, title: str, description: str, 
                          category: RecommendationCategory,
                          priority: RecommendationPriority,
                          expected_impact: str) -> 'CompetitiveIntelligenceReportBuilder':
        """Add a recommendation"""
        recommendation = Recommendation(
            title=title,
            description=description,
            category=category,
            priority=priority,
            expected_impact=expected_impact
        )
        self._recommendations.append(recommendation)
        return self
    
    def set_actionable_roadmap(self, implementation_timeline: str,
                              success_metrics: List[str]) -> 'CompetitiveIntelligenceReportBuilder':
        """Set actionable roadmap information"""
        self._implementation_timeline = implementation_timeline
        self._success_metrics = success_metrics
        return self
    
    # Validation methods
    def validate(self) -> ValidationResult:
        """Validate the current report state"""
        try:
            report = self._build_report()
            return self._validator.validate_report(report)
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                issues=[f"Build validation failed: {str(e)}"]
            )
    
    def _build_report(self) -> CompetitiveIntelligenceReport:
        """Internal method to build the report"""
        # Validate required components
        if not self._metadata:
            raise ValueError("Metadata is required")
        if not self._target_company:
            raise ValueError("Target company is required")
        if not self._executive_summary:
            raise ValueError("Executive summary is required")
        if len(self._recommendations) < 5:
            raise ValueError("At least 5 recommendations are required")
        
        # Build peer group
        peer_group = PeerGroup(
            target_company=self._target_company,
            peers=self._peers,
            discovery_method=self._discovery_method
        )
        
        # Build competitive dashboard
        competitive_dashboard = CompetitiveDashboard(
            metric_comparisons=self._metric_comparisons,
            overall_ranking=self._dashboard_ranking,
            strengths=self._dashboard_strengths,
            weaknesses=self._dashboard_weaknesses
        )
        
        # Build actionable roadmap
        actionable_roadmap = ActionableRoadmap(
            recommendations=self._recommendations,
            implementation_timeline=self._implementation_timeline or "12 months",
            success_metrics=self._success_metrics
        )
        
        # Build complete report
        return CompetitiveIntelligenceReport(
            metadata=self._metadata,
            data_sources=self._data_sources,
            peer_group=peer_group,
            executive_summary=self._executive_summary,
            competitive_dashboard=competitive_dashboard,
            actionable_roadmap=actionable_roadmap
        )
    
    def build(self) -> CompetitiveIntelligenceReport:
        """
        Build and return the complete competitive intelligence report.
        
        Returns:
            CompetitiveIntelligenceReport: The complete validated report
            
        Raises:
            ValueError: If required components are missing or validation fails
        """
        # Build the report
        report = self._build_report()
        
        # Validate the built report
        validation_result = self._validator.validate_report(report)
        
        if not validation_result.is_valid:
            error_messages = [
                f"Report validation failed with {len(validation_result.issues)} issues:",
                *validation_result.issues
            ]
            raise ValueError("\n".join(error_messages))
        
        return report
    
    def build_partial(self) -> CompetitiveIntelligenceReport:
        """
        Build a partial report without full validation.
        Useful for testing or incomplete reports.
        
        Returns:
            CompetitiveIntelligenceReport: The report (may be incomplete)
        """
        return self._build_report()


# Convenience functions
def create_sample_report() -> CompetitiveIntelligenceReport:
    """Create a sample report for testing purposes"""
    builder = CompetitiveIntelligenceReportBuilder()
    
    return (builder
            .set_metadata("AAPL")
            .add_data_source("financial_api", "FinancialModelingPrep", DataQuality.VALID)
            .set_target_company("AAPL", "Apple Inc.", "Technology", 3000000000000, 25.5)
            .add_peer_company("MSFT", "Microsoft Corporation", 0.85)
            .set_peer_discovery_method("sector_similarity")
            .set_executive_summary(
                overview="Apple maintains strong competitive position in technology sector",
                key_insights=["Strong brand loyalty", "High profit margins", "Innovation leadership"],
                top_recommendations=["Expand services revenue", "Improve supply chain", "Focus on AI"]
            )
            .add_metric_comparison("P/E Ratio", 25.5, {"MSFT": 28.2}, 1, "Apple trades at discount to peer")
            .set_competitive_dashboard(2, ["Brand strength"], ["China dependency"])
            .add_recommendation("Expand AI", "Focus on AI integration", RecommendationCategory.DO, RecommendationPriority.HIGH, "Competitive advantage")
            .add_recommendation("Communicate value", "Better articulate benefits", RecommendationCategory.SAY, RecommendationPriority.MEDIUM, "Market perception")
            .add_recommendation("Showcase innovation", "Demonstrate new tech", RecommendationCategory.SHOW, RecommendationPriority.HIGH, "Investor confidence")
            .add_recommendation("Improve efficiency", "Optimize operations", RecommendationCategory.DO, RecommendationPriority.MEDIUM, "Cost savings")
            .add_recommendation("Engage stakeholders", "Better communication", RecommendationCategory.SAY, RecommendationPriority.LOW, "Stakeholder trust")
            .set_actionable_roadmap("12 months", ["Market share growth", "P/E improvement"])
            .build())


# Export main classes
__all__ = [
    'CompetitiveIntelligenceReportBuilder',
    'create_sample_report'
]