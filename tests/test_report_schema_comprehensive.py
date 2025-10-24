"""
Comprehensive Test Suite for Report Schema Models

Tests all Pydantic models, validation rules, and schema compliance
for the competitive intelligence report structure.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
import json
from pydantic import ValidationError

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from metis.models.report_schema_v2 import (
    DataQuality,
    RecommendationPriority, 
    RecommendationCategory,
    ReportMetadata,
    DataSource,
    CompanyProfile,
    PeerCompany,
    PeerGroup,
    MetricComparison,
    ExecutiveSummary,
    CompetitiveDashboard,
    Recommendation,
    ActionableRoadmap,
    CompetitiveIntelligenceReport
)


class TestEnums:
    """Test enum definitions and values"""
    
    def test_data_quality_enum(self):
        """Test DataQuality enum values"""
        assert DataQuality.VALID == "valid"
        assert DataQuality.ESTIMATED == "estimated"
        assert DataQuality.INSUFFICIENT == "insufficient"
        
        # Test enum membership
        assert "valid" in DataQuality
        assert "invalid_value" not in DataQuality
    
    def test_recommendation_priority_enum(self):
        """Test RecommendationPriority enum"""
        assert RecommendationPriority.HIGH == "high"
        assert RecommendationPriority.MEDIUM == "medium"
        assert RecommendationPriority.LOW == "low"
    
    def test_recommendation_category_enum(self):
        """Test RecommendationCategory enum"""
        assert RecommendationCategory.DO == "do"
        assert RecommendationCategory.SAY == "say"
        assert RecommendationCategory.SHOW == "show"


class TestReportMetadata:
    """Test ReportMetadata model"""
    
    def test_valid_metadata_creation(self):
        """Test creating valid metadata"""
        metadata = ReportMetadata(target_symbol="AAPL")
        
        assert metadata.target_symbol == "AAPL"
        assert metadata.version == "1.0"
        assert isinstance(metadata.generated_at, datetime)
        assert len(metadata.report_id) > 0
    
    def test_target_symbol_validation(self):
        """Test target symbol validation"""
        # Valid symbols
        valid_metadata = ReportMetadata(target_symbol="MSFT")
        assert valid_metadata.target_symbol == "MSFT"
        
        # Empty symbol should raise error
        with pytest.raises(ValueError, match="Target symbol cannot be empty"):
            ReportMetadata(target_symbol="")
        
        # Whitespace-only symbol
        with pytest.raises(ValueError):
            ReportMetadata(target_symbol="   ")
    
    def test_symbol_normalization(self):
        """Test symbol normalization (uppercase, strip)"""
        metadata = ReportMetadata(target_symbol="  aapl  ")
        assert metadata.target_symbol == "AAPL"
    
    def test_optional_fields(self):
        """Test optional field handling"""
        metadata = ReportMetadata(
            target_symbol="GOOGL",
            processing_time_seconds=45.5
        )
        
        assert metadata.processing_time_seconds == 45.5
        assert metadata.target_symbol == "GOOGL"


class TestDataSource:
    """Test DataSource model"""
    
    def test_valid_data_source(self):
        """Test creating valid data source"""
        source = DataSource(
            source_type="financial_api",
            provider="FinancialModelingPrep"
        )
        
        assert source.source_type == "financial_api"
        assert source.provider == "FinancialModelingPrep"
        assert source.quality == DataQuality.VALID
    
    def test_data_source_with_date(self):
        """Test data source with timestamp"""
        test_date = datetime.now()
        source = DataSource(
            source_type="earnings_transcript",
            provider="AlphaSense",
            data_date=test_date,
            quality=DataQuality.ESTIMATED
        )
        
        assert source.data_date == test_date
        assert source.quality == DataQuality.ESTIMATED


class TestCompanyProfile:
    """Test CompanyProfile model"""
    
    def test_valid_company_profile(self):
        """Test creating valid company profile"""
        profile = CompanyProfile(
            symbol="AAPL",
            company_name="Apple Inc.",
            sector="Technology",
            market_cap=3000000000000,
            pe_ratio=25.5,
            revenue_ttm=400000000000
        )
        
        assert profile.symbol == "AAPL"
        assert profile.company_name == "Apple Inc."
        assert profile.sector == "Technology"
        assert profile.market_cap == 3000000000000
        assert profile.pe_ratio == 25.5
        assert profile.revenue_ttm == 400000000000
    
    def test_symbol_validation_and_normalization(self):
        """Test symbol validation in company profile"""
        profile = CompanyProfile(
            symbol="  msft  ",
            company_name="Microsoft Corporation",
            sector="Technology"
        )
        
        assert profile.symbol == "MSFT"
    
    def test_optional_financial_metrics(self):
        """Test optional financial fields"""
        minimal_profile = CompanyProfile(
            symbol="TSLA",
            company_name="Tesla Inc.",
            sector="Automotive"
        )
        
        assert minimal_profile.market_cap is None
        assert minimal_profile.pe_ratio is None
        assert minimal_profile.revenue_ttm is None


class TestPeerCompany:
    """Test PeerCompany model"""
    
    def test_valid_peer_company(self):
        """Test creating valid peer company"""
        peer = PeerCompany(
            symbol="MSFT",
            company_name="Microsoft Corporation",
            similarity_score=0.85
        )
        
        assert peer.symbol == "MSFT"
        assert peer.company_name == "Microsoft Corporation"
        assert peer.similarity_score == 0.85
    
    def test_similarity_score_validation(self):
        """Test similarity score range validation"""
        # Valid scores
        peer1 = PeerCompany(
            symbol="GOOGL",
            company_name="Alphabet Inc.",
            similarity_score=0.0
        )
        assert peer1.similarity_score == 0.0
        
        peer2 = PeerCompany(
            symbol="GOOGL",
            company_name="Alphabet Inc.",
            similarity_score=1.0
        )
        assert peer2.similarity_score == 1.0
        
        # Invalid scores should raise validation error
        with pytest.raises(ValueError):
            PeerCompany(
                symbol="GOOGL",
                company_name="Alphabet Inc.",
                similarity_score=-0.1
            )
        
        with pytest.raises(ValueError):
            PeerCompany(
                symbol="GOOGL",
                company_name="Alphabet Inc.",
                similarity_score=1.1
            )


class TestPeerGroup:
    """Test PeerGroup model"""
    
    def test_valid_peer_group(self):
        """Test creating valid peer group"""
        target = CompanyProfile(
            symbol="AAPL",
            company_name="Apple Inc.",
            sector="Technology"
        )
        
        peers = [
            PeerCompany(symbol="MSFT", company_name="Microsoft Corporation", similarity_score=0.85),
            PeerCompany(symbol="GOOGL", company_name="Alphabet Inc.", similarity_score=0.75)
        ]
        
        peer_group = PeerGroup(
            target_company=target,
            peers=peers,
            discovery_method="sector_similarity"
        )
        
        assert peer_group.target_company.symbol == "AAPL"
        assert len(peer_group.peers) == 2
        assert peer_group.discovery_method == "sector_similarity"
    
    def test_peer_group_validation(self):
        """Test peer group validation rules"""
        target = CompanyProfile(
            symbol="AAPL",
            company_name="Apple Inc.",
            sector="Technology"
        )
        
        # Empty peers list should fail
        with pytest.raises(ValidationError):
            PeerGroup(
                target_company=target,
                peers=[],
                discovery_method="manual"
            )


class TestMetricComparison:
    """Test MetricComparison model"""
    
    def test_valid_metric_comparison(self):
        """Test creating valid metric comparison"""
        comparison = MetricComparison(
            metric_name="P/E Ratio",
            target_value=25.5,
            peer_values={"MSFT": 28.2, "GOOGL": 22.1},
            target_ranking=2,
            analysis="Target company trades at moderate discount to peers"
        )
        
        assert comparison.metric_name == "P/E Ratio"
        assert comparison.target_value == 25.5
        assert comparison.peer_values["MSFT"] == 28.2
        assert comparison.target_ranking == 2
        assert len(comparison.analysis) > 0
    
    def test_optional_fields(self):
        """Test optional fields in metric comparison"""
        comparison = MetricComparison(
            metric_name="ROE",
            peer_values={},
            analysis="Limited peer data available"
        )
        
        assert comparison.target_value is None
        assert comparison.target_ranking is None
        assert comparison.peer_values == {}


class TestExecutiveSummary:
    """Test ExecutiveSummary model"""
    
    def test_valid_executive_summary(self):
        """Test creating valid executive summary"""
        summary = ExecutiveSummary(
            overview="Company maintains strong competitive position",
            key_insights=["Strong brand loyalty", "High profit margins", "Market leadership"],
            top_recommendations=["Expand international", "Invest in R&D", "Improve efficiency"]
        )
        
        assert len(summary.key_insights) == 3
        assert len(summary.top_recommendations) == 3
        assert len(summary.overview) > 0
    
    def test_minimum_requirements(self):
        """Test minimum count requirements"""
        # Minimum valid counts
        summary = ExecutiveSummary(
            overview="Brief overview",
            key_insights=["Insight 1", "Insight 2", "Insight 3"],
            top_recommendations=["Rec 1", "Rec 2", "Rec 3"]
        )
        assert len(summary.key_insights) == 3
        assert len(summary.top_recommendations) == 3
        
        # Too few insights should fail
        with pytest.raises(ValueError):
            ExecutiveSummary(
                overview="Overview",
                key_insights=["Only one", "Only two"],
                top_recommendations=["Rec 1", "Rec 2", "Rec 3"]
            )
        
        # Too few recommendations should fail
        with pytest.raises(ValueError):
            ExecutiveSummary(
                overview="Overview",
                key_insights=["Insight 1", "Insight 2", "Insight 3"],
                top_recommendations=["Only one", "Only two"]
            )
    
    def test_maximum_limits(self):
        """Test maximum count limits"""
        # Maximum valid counts
        summary = ExecutiveSummary(
            overview="Overview",
            key_insights=["1", "2", "3", "4", "5"],
            top_recommendations=["1", "2", "3", "4", "5"]
        )
        assert len(summary.key_insights) == 5
        assert len(summary.top_recommendations) == 5
        
        # Too many insights should fail
        with pytest.raises(ValueError):
            ExecutiveSummary(
                overview="Overview",
                key_insights=["1", "2", "3", "4", "5", "6"],
                top_recommendations=["1", "2", "3"]
            )


class TestCompetitiveDashboard:
    """Test CompetitiveDashboard model"""
    
    def test_valid_competitive_dashboard(self):
        """Test creating valid competitive dashboard"""
        comparisons = [
            MetricComparison(
                metric_name="P/E Ratio",
                target_value=25.5,
                peer_values={"MSFT": 28.2},
                target_ranking=2,
                analysis="Good performance"
            )
        ]
        
        dashboard = CompetitiveDashboard(
            metric_comparisons=comparisons,
            overall_ranking=2,
            strengths=["Strong profitability", "Market leadership"],
            weaknesses=["High debt", "Cyclical exposure"]
        )
        
        assert len(dashboard.metric_comparisons) == 1
        assert dashboard.overall_ranking == 2
        assert len(dashboard.strengths) == 2
        assert len(dashboard.weaknesses) == 2
    
    def test_ranking_validation(self):
        """Test ranking value validation"""
        comparisons = []
        
        # Valid ranking
        dashboard = CompetitiveDashboard(
            metric_comparisons=comparisons,
            overall_ranking=1,
            strengths=[],
            weaknesses=[]
        )
        assert dashboard.overall_ranking == 1
        
        # Invalid ranking (0 or negative)
        with pytest.raises(ValueError):
            CompetitiveDashboard(
                metric_comparisons=comparisons,
                overall_ranking=0,
                strengths=[],
                weaknesses=[]
            )


class TestRecommendation:
    """Test Recommendation model"""
    
    def test_valid_recommendation(self):
        """Test creating valid recommendation"""
        rec = Recommendation(
            title="Improve investor communication",
            description="Enhance quarterly earnings presentations with detailed metrics",
            category=RecommendationCategory.SAY,
            priority=RecommendationPriority.HIGH,
            expected_impact="Improved analyst sentiment and coverage"
        )
        
        assert rec.title == "Improve investor communication"
        assert rec.category == RecommendationCategory.SAY
        assert rec.priority == RecommendationPriority.HIGH
        assert len(rec.expected_impact) > 0
    
    def test_recommendation_categories(self):
        """Test all recommendation categories"""
        categories = [
            (RecommendationCategory.DO, "Operational action"),
            (RecommendationCategory.SAY, "Communication improvement"),
            (RecommendationCategory.SHOW, "Demonstration of value")
        ]
        
        for category, description in categories:
            rec = Recommendation(
                title=f"Test {category.value} recommendation",
                description=description,
                category=category,
                priority=RecommendationPriority.MEDIUM,
                expected_impact="Expected impact"
            )
            assert rec.category == category


class TestActionableRoadmap:
    """Test ActionableRoadmap model"""
    
    def test_valid_actionable_roadmap(self):
        """Test creating valid actionable roadmap"""
        recommendations = [
            Recommendation(
                title=f"Recommendation {i}",
                description=f"Description {i}",
                category=RecommendationCategory.DO if i % 3 == 0 else 
                         RecommendationCategory.SAY if i % 3 == 1 else 
                         RecommendationCategory.SHOW,
                priority=RecommendationPriority.HIGH,
                expected_impact=f"Impact {i}"
            )
            for i in range(1, 6)
        ]
        
        roadmap = ActionableRoadmap(
            recommendations=recommendations,
            implementation_timeline="12 months",
            success_metrics=["Metric 1", "Metric 2", "Metric 3"]
        )
        
        assert len(roadmap.recommendations) == 5
        assert roadmap.implementation_timeline == "12 months"
        assert len(roadmap.success_metrics) == 3
    
    def test_minimum_recommendations_validation(self):
        """Test minimum recommendations requirement"""
        # Too few recommendations
        recommendations = [
            Recommendation(
                title="Single rec",
                description="Description",
                category=RecommendationCategory.DO,
                priority=RecommendationPriority.HIGH,
                expected_impact="Impact"
            )
        ]
        
        with pytest.raises(ValueError):
            ActionableRoadmap(
                recommendations=recommendations,
                implementation_timeline="6 months",
                success_metrics=["Metric 1"]
            )


class TestCompetitiveIntelligenceReport:
    """Test complete report model"""
    
    def create_sample_report(self) -> CompetitiveIntelligenceReport:
        """Helper to create a valid sample report"""
        metadata = ReportMetadata(target_symbol="AAPL")
        
        data_sources = [
            DataSource(source_type="financial_api", provider="FMP")
        ]
        
        target_company = CompanyProfile(
            symbol="AAPL",
            company_name="Apple Inc.",
            sector="Technology"
        )
        
        peers = [
            PeerCompany(symbol="MSFT", company_name="Microsoft", similarity_score=0.85)
        ]
        
        peer_group = PeerGroup(
            target_company=target_company,
            peers=peers,
            discovery_method="sector_similarity"
        )
        
        executive_summary = ExecutiveSummary(
            overview="Strong competitive position",
            key_insights=["Insight 1", "Insight 2", "Insight 3"],
            top_recommendations=["Rec 1", "Rec 2", "Rec 3"]
        )
        
        metric_comparisons = [
            MetricComparison(
                metric_name="P/E Ratio",
                target_value=25.5,
                peer_values={"MSFT": 28.2},
                target_ranking=1,
                analysis="Good performance"
            )
        ]
        
        competitive_dashboard = CompetitiveDashboard(
            metric_comparisons=metric_comparisons,
            overall_ranking=1,
            strengths=["Strength 1"],
            weaknesses=["Weakness 1"]
        )
        
        recommendations = [
            Recommendation(
                title=f"Recommendation {i}",
                description=f"Description {i}",
                category=RecommendationCategory.DO,
                priority=RecommendationPriority.HIGH,
                expected_impact=f"Impact {i}"
            )
            for i in range(1, 6)
        ]
        
        actionable_roadmap = ActionableRoadmap(
            recommendations=recommendations,
            implementation_timeline="12 months",
            success_metrics=["Metric 1", "Metric 2"]
        )
        
        return CompetitiveIntelligenceReport(
            metadata=metadata,
            data_sources=data_sources,
            peer_group=peer_group,
            executive_summary=executive_summary,
            competitive_dashboard=competitive_dashboard,
            actionable_roadmap=actionable_roadmap
        )
    
    def test_valid_complete_report(self):
        """Test creating valid complete report"""
        report = self.create_sample_report()
        
        assert report.metadata.target_symbol == "AAPL"
        assert len(report.data_sources) == 1
        assert report.peer_group.target_company.symbol == "AAPL"
        assert len(report.executive_summary.key_insights) >= 3
        assert len(report.actionable_roadmap.recommendations) >= 5
    
    def test_cross_field_validation(self):
        """Test cross-field validation in complete report"""
        report = self.create_sample_report()
        
        # Symbol consistency should pass validation
        assert report.metadata.target_symbol == report.peer_group.target_company.symbol
    
    def test_symbol_mismatch_validation(self):
        """Test validation fails with symbol mismatch"""
        # Create report with mismatched symbols
        metadata = ReportMetadata(target_symbol="AAPL")
        
        target_company = CompanyProfile(
            symbol="MSFT",  # Different symbol!
            company_name="Microsoft Corporation",
            sector="Technology"
        )
        
        peers = [
            PeerCompany(symbol="GOOGL", company_name="Alphabet", similarity_score=0.85)
        ]
        
        peer_group = PeerGroup(
            target_company=target_company,
            peers=peers,
            discovery_method="manual"
        )
        
        # This should fail validation
        with pytest.raises(ValueError, match="Target symbol mismatch"):
            CompetitiveIntelligenceReport(
                metadata=metadata,
                data_sources=[DataSource(source_type="test", provider="test")],
                peer_group=peer_group,
                executive_summary=ExecutiveSummary(
                    overview="Overview",
                    key_insights=["1", "2", "3"],
                    top_recommendations=["1", "2", "3"]
                ),
                competitive_dashboard=CompetitiveDashboard(
                    metric_comparisons=[],
                    overall_ranking=1,
                    strengths=[],
                    weaknesses=[]
                ),
                actionable_roadmap=ActionableRoadmap(
                    recommendations=[
                        Recommendation(
                            title=f"Rec {i}",
                            description=f"Desc {i}",
                            category=RecommendationCategory.DO,
                            priority=RecommendationPriority.HIGH,
                            expected_impact=f"Impact {i}"
                        )
                        for i in range(5)
                    ],
                    implementation_timeline="12 months",
                    success_metrics=["Metric 1"]
                )
            )
    
    def test_json_serialization(self):
        """Test JSON serialization and deserialization"""
        report = self.create_sample_report()
        
        # Serialize to JSON
        json_data = report.model_dump()
        json_str = json.dumps(json_data, default=str)
        
        # Should be valid JSON
        assert len(json_str) > 1000
        
        # Deserialize back
        parsed_data = json.loads(json_str)
        new_report = CompetitiveIntelligenceReport.model_validate(parsed_data)
        
        assert new_report.metadata.target_symbol == report.metadata.target_symbol
        assert len(new_report.peer_group.peers) == len(report.peer_group.peers)


class TestModelValidationEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_strings_validation(self):
        """Test validation of empty strings"""
        with pytest.raises(ValueError):
            CompanyProfile(
                symbol="",
                company_name="Valid Name",
                sector="Valid Sector"
            )
    
    def test_very_long_strings(self):
        """Test handling of very long strings"""
        long_string = "x" * 10000
        
        # Should handle long descriptions
        rec = Recommendation(
            title="Short title",
            description=long_string,
            category=RecommendationCategory.DO,
            priority=RecommendationPriority.HIGH,
            expected_impact="Impact"
        )
        
        assert len(rec.description) == 10000
    
    def test_special_characters_in_symbols(self):
        """Test handling of special characters in symbols"""
        # Valid symbol with dots
        profile = CompanyProfile(
            symbol="BRK.B",
            company_name="Berkshire Hathaway Class B",
            sector="Financial"
        )
        assert profile.symbol == "BRK.B"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])