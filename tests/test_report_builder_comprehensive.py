"""
Comprehensive Test Suite for Report Builder

Tests the fluent API report builder with all validation scenarios,
error handling, and integration patterns.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from metis.reports.report_builder_v2 import (
    CompetitiveIntelligenceReportBuilder,
    create_sample_report
)
from metis.models.report_schema_v2 import (
    DataQuality,
    RecommendationCategory,
    RecommendationPriority,
    CompetitiveIntelligenceReport
)
from metis.models.validation_models import ValidationResult, ValidationSeverity


class TestReportBuilderBasics:
    """Test basic report builder functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.builder = CompetitiveIntelligenceReportBuilder()
    
    def test_builder_initialization(self):
        """Test builder initialization state"""
        assert self.builder._metadata is None
        assert len(self.builder._data_sources) == 0
        assert self.builder._target_company is None
        assert len(self.builder._peers) == 0
        assert self.builder._executive_summary is None
        assert len(self.builder._recommendations) == 0
    
    def test_reset_functionality(self):
        """Test builder reset functionality"""
        # Add some data
        self.builder.set_metadata("AAPL")
        self.builder.add_data_source("test", "provider", DataQuality.VALID)
        
        # Verify data exists
        assert self.builder._metadata is not None
        assert len(self.builder._data_sources) == 1
        
        # Reset and verify clean state
        self.builder.reset()
        assert self.builder._metadata is None
        assert len(self.builder._data_sources) == 0
    
    def test_fluent_api_chaining(self):
        """Test method chaining returns builder instance"""
        result = (self.builder
                 .set_metadata("AAPL")
                 .add_data_source("test", "provider")
                 .set_target_company("AAPL", "Apple Inc.", "Technology"))
        
        assert result is self.builder
        assert self.builder._metadata.target_symbol == "AAPL"
        assert len(self.builder._data_sources) == 1
        assert self.builder._target_company.symbol == "AAPL"


class TestMetadataOperations:
    """Test metadata setting and validation"""
    
    def setup_method(self):
        self.builder = CompetitiveIntelligenceReportBuilder()
    
    def test_set_metadata_basic(self):
        """Test basic metadata setting"""
        self.builder.set_metadata("MSFT")
        
        assert self.builder._metadata.target_symbol == "MSFT"
        assert self.builder._metadata.version == "1.0"
        assert isinstance(self.builder._metadata.generated_at, datetime)
        assert len(self.builder._metadata.report_id) > 0
    
    def test_set_metadata_with_custom_id(self):
        """Test metadata with custom report ID"""
        custom_id = "custom-report-123"
        self.builder.set_metadata("GOOGL", report_id=custom_id)
        
        assert self.builder._metadata.report_id == custom_id
        assert self.builder._metadata.target_symbol == "GOOGL"
    
    def test_set_metadata_with_version(self):
        """Test metadata with custom version"""
        self.builder.set_metadata("TSLA", version="2.0")
        
        assert self.builder._metadata.version == "2.0"
        assert self.builder._metadata.target_symbol == "TSLA"
    
    def test_set_processing_time(self):
        """Test setting processing time"""
        self.builder.set_metadata("AAPL")
        self.builder.set_processing_time(45.7)
        
        assert self.builder._metadata.processing_time_seconds == 45.7


class TestDataSourceOperations:
    """Test data source management"""
    
    def setup_method(self):
        self.builder = CompetitiveIntelligenceReportBuilder()
    
    def test_add_data_source_basic(self):
        """Test adding basic data source"""
        self.builder.add_data_source("financial_api", "FinancialModelingPrep")
        
        assert len(self.builder._data_sources) == 1
        source = self.builder._data_sources[0]
        assert source.source_type == "financial_api"
        assert source.provider == "FinancialModelingPrep"
        assert source.quality == DataQuality.VALID
    
    def test_add_data_source_with_quality(self):
        """Test adding data source with quality indicator"""
        test_date = datetime.now()
        self.builder.add_data_source(
            "earnings_transcript",
            "AlphaSense",
            quality=DataQuality.ESTIMATED,
            data_date=test_date
        )
        
        source = self.builder._data_sources[0]
        assert source.quality == DataQuality.ESTIMATED
        assert source.data_date == test_date
    
    def test_multiple_data_sources(self):
        """Test adding multiple data sources"""
        self.builder.add_data_source("financial_api", "FMP")
        self.builder.add_data_source("transcript", "AlphaSense")
        self.builder.add_data_source("market_data", "Yahoo")
        
        assert len(self.builder._data_sources) == 3
        
        sources = self.builder._data_sources
        assert sources[0].source_type == "financial_api"
        assert sources[1].source_type == "transcript"
        assert sources[2].source_type == "market_data"


class TestCompanyAndPeerOperations:
    """Test company and peer management"""
    
    def setup_method(self):
        self.builder = CompetitiveIntelligenceReportBuilder()
    
    def test_set_target_company_basic(self):
        """Test setting target company"""
        self.builder.set_target_company("AAPL", "Apple Inc.", "Technology")
        
        company = self.builder._target_company
        assert company.symbol == "AAPL"
        assert company.company_name == "Apple Inc."
        assert company.sector == "Technology"
        assert company.market_cap is None
    
    def test_set_target_company_with_metrics(self):
        """Test setting target company with financial metrics"""
        self.builder.set_target_company(
            "AAPL", "Apple Inc.", "Technology",
            market_cap=3000000000000,
            pe_ratio=25.5,
            revenue_ttm=400000000000
        )
        
        company = self.builder._target_company
        assert company.market_cap == 3000000000000
        assert company.pe_ratio == 25.5
        assert company.revenue_ttm == 400000000000
    
    def test_add_peer_company(self):
        """Test adding peer company"""
        self.builder.add_peer_company("MSFT", "Microsoft Corporation", 0.85)
        
        assert len(self.builder._peers) == 1
        peer = self.builder._peers[0]
        assert peer.symbol == "MSFT"
        assert peer.company_name == "Microsoft Corporation"
        assert peer.similarity_score == 0.85
    
    def test_add_multiple_peers(self):
        """Test adding multiple peer companies"""
        peers_data = [
            ("MSFT", "Microsoft Corporation", 0.85),
            ("GOOGL", "Alphabet Inc.", 0.78),
            ("META", "Meta Platforms", 0.72),
            ("NVDA", "NVIDIA Corporation", 0.68)
        ]
        
        for symbol, name, score in peers_data:
            self.builder.add_peer_company(symbol, name, score)
        
        assert len(self.builder._peers) == 4
        
        # Verify peer data
        peers = self.builder._peers
        assert peers[0].symbol == "MSFT"
        assert peers[1].similarity_score == 0.78
        assert peers[2].company_name == "Meta Platforms"
        assert peers[3].symbol == "NVDA"
    
    def test_set_peer_discovery_method(self):
        """Test setting peer discovery method"""
        self.builder.set_peer_discovery_method("machine_learning_similarity")
        
        assert self.builder._discovery_method == "machine_learning_similarity"


class TestExecutiveSummaryOperations:
    """Test executive summary building"""
    
    def setup_method(self):
        self.builder = CompetitiveIntelligenceReportBuilder()
    
    def test_set_executive_summary(self):
        """Test setting executive summary"""
        overview = "Apple maintains strong competitive position in technology sector"
        insights = ["Strong brand loyalty", "High profit margins", "Innovation leadership"]
        recommendations = ["Expand services", "Improve supply chain", "Focus on AI"]
        
        self.builder.set_executive_summary(overview, insights, recommendations)
        
        summary = self.builder._executive_summary
        assert summary.overview == overview
        assert summary.key_insights == insights
        assert summary.top_recommendations == recommendations
        assert len(summary.key_insights) == 3
        assert len(summary.top_recommendations) == 3


class TestDashboardOperations:
    """Test competitive dashboard building"""
    
    def setup_method(self):
        self.builder = CompetitiveIntelligenceReportBuilder()
    
    def test_add_metric_comparison(self):
        """Test adding metric comparison"""
        self.builder.add_metric_comparison(
            "P/E Ratio",
            25.5,
            {"MSFT": 28.2, "GOOGL": 22.1},
            2,
            "Apple trades at moderate discount to Microsoft but premium to Google"
        )
        
        assert len(self.builder._metric_comparisons) == 1
        comparison = self.builder._metric_comparisons[0]
        assert comparison.metric_name == "P/E Ratio"
        assert comparison.target_value == 25.5
        assert comparison.peer_values["MSFT"] == 28.2
        assert comparison.target_ranking == 2
    
    def test_add_multiple_metric_comparisons(self):
        """Test adding multiple metric comparisons"""
        metrics = [
            ("P/E Ratio", 25.5, {"MSFT": 28.2}, 2, "Analysis 1"),
            ("ROE", 18.4, {"MSFT": 19.1}, 2, "Analysis 2"),
            ("Revenue Growth", 8.5, {"MSFT": 12.3}, 2, "Analysis 3")
        ]
        
        for metric_name, target_val, peer_vals, ranking, analysis in metrics:
            self.builder.add_metric_comparison(metric_name, target_val, peer_vals, ranking, analysis)
        
        assert len(self.builder._metric_comparisons) == 3
        assert self.builder._metric_comparisons[0].metric_name == "P/E Ratio"
        assert self.builder._metric_comparisons[1].metric_name == "ROE"
        assert self.builder._metric_comparisons[2].metric_name == "Revenue Growth"
    
    def test_set_competitive_dashboard(self):
        """Test setting competitive dashboard summary"""
        self.builder.set_competitive_dashboard(
            overall_ranking=3,
            strengths=["Best-in-class margins", "Strong brand"],
            weaknesses=["High debt", "Cyclical exposure"]
        )
        
        assert self.builder._dashboard_ranking == 3
        assert len(self.builder._dashboard_strengths) == 2
        assert len(self.builder._dashboard_weaknesses) == 2
        assert "Best-in-class margins" in self.builder._dashboard_strengths
        assert "High debt" in self.builder._dashboard_weaknesses


class TestRecommendationOperations:
    """Test recommendation building"""
    
    def setup_method(self):
        self.builder = CompetitiveIntelligenceReportBuilder()
    
    def test_add_recommendation(self):
        """Test adding single recommendation"""
        self.builder.add_recommendation(
            "Improve investor communication",
            "Enhance quarterly earnings presentations with more detailed metrics",
            RecommendationCategory.SAY,
            RecommendationPriority.HIGH,
            "Improved analyst sentiment and coverage"
        )
        
        assert len(self.builder._recommendations) == 1
        rec = self.builder._recommendations[0]
        assert rec.title == "Improve investor communication"
        assert rec.category == RecommendationCategory.SAY
        assert rec.priority == RecommendationPriority.HIGH
        assert "Improved analyst sentiment" in rec.expected_impact
    
    def test_add_recommendations_all_categories(self):
        """Test adding recommendations across all categories"""
        recommendations = [
            ("Expand AI capabilities", RecommendationCategory.DO, RecommendationPriority.HIGH),
            ("Improve messaging", RecommendationCategory.SAY, RecommendationPriority.MEDIUM),
            ("Showcase innovation", RecommendationCategory.SHOW, RecommendationPriority.HIGH),
            ("Optimize operations", RecommendationCategory.DO, RecommendationPriority.LOW),
            ("Engage stakeholders", RecommendationCategory.SAY, RecommendationPriority.MEDIUM)
        ]
        
        for title, category, priority in recommendations:
            self.builder.add_recommendation(
                title,
                f"Description for {title}",
                category,
                priority,
                f"Expected impact for {title}"
            )
        
        assert len(self.builder._recommendations) == 5
        
        # Verify categories are represented
        categories = [rec.category for rec in self.builder._recommendations]
        assert RecommendationCategory.DO in categories
        assert RecommendationCategory.SAY in categories
        assert RecommendationCategory.SHOW in categories
    
    def test_set_actionable_roadmap(self):
        """Test setting actionable roadmap metadata"""
        self.builder.set_actionable_roadmap(
            "18 months",
            ["P/E multiple expansion", "Analyst coverage improvement", "Market share growth"]
        )
        
        assert self.builder._implementation_timeline == "18 months"
        assert len(self.builder._success_metrics) == 3
        assert "P/E multiple expansion" in self.builder._success_metrics


class TestValidationOperations:
    """Test validation functionality"""
    
    def setup_method(self):
        self.builder = CompetitiveIntelligenceReportBuilder()
    
    def create_minimal_valid_builder(self):
        """Helper to create minimally valid builder"""
        return (self.builder
                .set_metadata("AAPL")
                .set_target_company("AAPL", "Apple Inc.", "Technology")
                .add_peer_company("MSFT", "Microsoft", 0.85)
                .set_executive_summary("Overview", ["1", "2", "3"], ["A", "B", "C"])
                .add_recommendation("Rec 1", "Desc 1", RecommendationCategory.DO, RecommendationPriority.HIGH, "Impact 1")
                .add_recommendation("Rec 2", "Desc 2", RecommendationCategory.SAY, RecommendationPriority.HIGH, "Impact 2")
                .add_recommendation("Rec 3", "Desc 3", RecommendationCategory.SHOW, RecommendationPriority.HIGH, "Impact 3")
                .add_recommendation("Rec 4", "Desc 4", RecommendationCategory.DO, RecommendationPriority.HIGH, "Impact 4")
                .add_recommendation("Rec 5", "Desc 5", RecommendationCategory.SAY, RecommendationPriority.HIGH, "Impact 5"))
    
    def test_validate_success(self):
        """Test successful validation"""
        builder = self.create_minimal_valid_builder()
        
        validation_result = builder.validate()
        
        assert validation_result.is_valid
        assert validation_result.severity != ValidationSeverity.ERROR
    
    def test_validate_missing_metadata(self):
        """Test validation failure for missing metadata"""
        validation_result = self.builder.validate()
        
        assert not validation_result.is_valid
        assert validation_result.severity == ValidationSeverity.ERROR
        assert any("Metadata is required" in issue for issue in validation_result.issues)
    
    def test_validate_missing_target_company(self):
        """Test validation failure for missing target company"""
        self.builder.set_metadata("AAPL")
        
        validation_result = self.builder.validate()
        
        assert not validation_result.is_valid
        assert any("Target company is required" in issue for issue in validation_result.issues)
    
    def test_validate_insufficient_recommendations(self):
        """Test validation failure for insufficient recommendations"""
        (self.builder
         .set_metadata("AAPL")
         .set_target_company("AAPL", "Apple Inc.", "Technology")
         .set_executive_summary("Overview", ["1", "2", "3"], ["A", "B", "C"])
         .add_recommendation("Only one", "Desc", RecommendationCategory.DO, RecommendationPriority.HIGH, "Impact"))
        
        validation_result = self.builder.validate()
        
        assert not validation_result.is_valid
        assert any("At least 5 recommendations are required" in issue for issue in validation_result.issues)


class TestBuildOperations:
    """Test report building"""
    
    def setup_method(self):
        self.builder = CompetitiveIntelligenceReportBuilder()
    
    def create_complete_valid_builder(self):
        """Helper to create complete valid builder"""
        return (self.builder
                .set_metadata("AAPL")
                .add_data_source("financial_api", "FMP", DataQuality.VALID)
                .set_target_company("AAPL", "Apple Inc.", "Technology", 3000000000000, 25.5)
                .add_peer_company("MSFT", "Microsoft", 0.85)
                .add_peer_company("GOOGL", "Alphabet", 0.78)
                .set_peer_discovery_method("sector_similarity")
                .set_executive_summary(
                    "Apple maintains strong competitive position",
                    ["Strong brand", "High margins", "Innovation"],
                    ["Expand services", "Improve supply chain", "Focus on AI"]
                )
                .add_metric_comparison("P/E Ratio", 25.5, {"MSFT": 28.2}, 1, "Apple discount")
                .set_competitive_dashboard(2, ["Brand strength"], ["China dependency"])
                .add_recommendation("Expand AI", "AI integration", RecommendationCategory.DO, RecommendationPriority.HIGH, "Advantage")
                .add_recommendation("Communicate value", "Better messaging", RecommendationCategory.SAY, RecommendationPriority.MEDIUM, "Perception")
                .add_recommendation("Show innovation", "Demonstrate tech", RecommendationCategory.SHOW, RecommendationPriority.HIGH, "Confidence")
                .add_recommendation("Improve efficiency", "Optimize ops", RecommendationCategory.DO, RecommendationPriority.MEDIUM, "Savings")
                .add_recommendation("Engage stakeholders", "Better comms", RecommendationCategory.SAY, RecommendationPriority.LOW, "Trust")
                .set_actionable_roadmap("12 months", ["Market share", "P/E improvement"]))
    
    def test_build_success(self):
        """Test successful report building"""
        builder = self.create_complete_valid_builder()
        
        report = builder.build()
        
        assert isinstance(report, CompetitiveIntelligenceReport)
        assert report.metadata.target_symbol == "AAPL"
        assert len(report.data_sources) == 1
        assert report.peer_group.target_company.symbol == "AAPL"
        assert len(report.peer_group.peers) == 2
        assert len(report.executive_summary.key_insights) == 3
        assert len(report.competitive_dashboard.metric_comparisons) == 1
        assert len(report.actionable_roadmap.recommendations) == 5
    
    def test_build_validation_failure(self):
        """Test build failure due to validation"""
        # Only set metadata, missing required fields
        self.builder.set_metadata("AAPL")
        
        with pytest.raises(ValueError) as exc_info:
            self.builder.build()
        
        assert "Target company is required" in str(exc_info.value)
    
    def test_build_partial_success(self):
        """Test partial build without full validation"""
        self.builder.set_metadata("AAPL")
        
        # This should succeed even though incomplete
        partial_report = self.builder.build_partial()
        
        assert partial_report.metadata.target_symbol == "AAPL"
        # Other fields will be None or empty, but structure exists
    
    def test_symbol_consistency_validation(self):
        """Test symbol consistency validation during build"""
        (self.builder
         .set_metadata("AAPL")
         .add_data_source("test", "provider")
         .set_target_company("MSFT", "Microsoft", "Technology")  # Wrong symbol!
         .set_executive_summary("Overview", ["1", "2", "3"], ["A", "B", "C"])
         .add_recommendation("R1", "D1", RecommendationCategory.DO, RecommendationPriority.HIGH, "I1")
         .add_recommendation("R2", "D2", RecommendationCategory.SAY, RecommendationPriority.HIGH, "I2")
         .add_recommendation("R3", "D3", RecommendationCategory.SHOW, RecommendationPriority.HIGH, "I3")
         .add_recommendation("R4", "D4", RecommendationCategory.DO, RecommendationPriority.HIGH, "I4")
         .add_recommendation("R5", "D5", RecommendationCategory.SAY, RecommendationPriority.HIGH, "I5"))
        
        with pytest.raises(ValueError) as exc_info:
            self.builder.build()
        
        assert "Target symbol mismatch" in str(exc_info.value)


class TestSampleReportCreation:
    """Test sample report creation functionality"""
    
    def test_create_sample_report(self):
        """Test creating sample report"""
        report = create_sample_report()
        
        assert isinstance(report, CompetitiveIntelligenceReport)
        assert report.metadata.target_symbol == "AAPL"
        assert len(report.data_sources) >= 1
        assert len(report.peer_group.peers) >= 1
        assert len(report.executive_summary.key_insights) >= 3
        assert len(report.actionable_roadmap.recommendations) >= 5
    
    def test_sample_report_validation(self):
        """Test that sample report passes validation"""
        report = create_sample_report()
        
        # Should be valid without errors
        assert report.metadata.target_symbol == report.peer_group.target_company.symbol


class TestBuilderErrorHandling:
    """Test error handling and edge cases"""
    
    def setup_method(self):
        self.builder = CompetitiveIntelligenceReportBuilder()
    
    def test_validator_error_handling(self):
        """Test error handling when validator fails"""
        # Mock validator to raise exception
        with patch.object(self.builder._validator, 'validate_report', side_effect=Exception("Validation error")):
            self.builder.set_metadata("AAPL")
            
            validation_result = self.builder.validate()
            
            assert not validation_result.is_valid
            assert validation_result.severity == ValidationSeverity.ERROR
            assert any("Build validation failed" in issue for issue in validation_result.issues)
    
    def test_empty_peer_values_handling(self):
        """Test handling of empty peer values in metrics"""
        builder = (self.builder
                  .set_metadata("AAPL")
                  .set_target_company("AAPL", "Apple Inc.", "Technology")
                  .add_metric_comparison("Test Metric", 25.5, {}, None, "No peer data available"))
        
        # Should handle empty peer values gracefully
        assert len(builder._metric_comparisons) == 1
        assert builder._metric_comparisons[0].peer_values == {}
    
    def test_none_values_handling(self):
        """Test handling of None values in optional fields"""
        builder = (self.builder
                  .set_target_company("AAPL", "Apple Inc.", "Technology", None, None, None)
                  .add_metric_comparison("Test", None, {"MSFT": 25.0}, None, "Analysis"))
        
        assert builder._target_company.market_cap is None
        assert builder._target_company.pe_ratio is None
        assert builder._metric_comparisons[0].target_value is None


class TestBuilderPerformance:
    """Test builder performance characteristics"""
    
    def test_large_peer_group_handling(self):
        """Test handling of large peer groups"""
        builder = CompetitiveIntelligenceReportBuilder()
        builder.set_metadata("AAPL")
        builder.set_target_company("AAPL", "Apple Inc.", "Technology")
        
        # Add many peers
        for i in range(50):
            builder.add_peer_company(f"PEER{i}", f"Peer Company {i}", 0.5)
        
        assert len(builder._peers) == 50
        
        # Should still build successfully
        builder.set_executive_summary("Overview", ["1", "2", "3"], ["A", "B", "C"])
        
        # Add minimum recommendations
        for i in range(5):
            builder.add_recommendation(f"Rec {i}", f"Desc {i}", RecommendationCategory.DO, RecommendationPriority.HIGH, f"Impact {i}")
        
        report = builder.build()
        assert len(report.peer_group.peers) == 50
    
    def test_large_recommendation_list(self):
        """Test handling of large recommendation lists"""
        builder = (CompetitiveIntelligenceReportBuilder()
                  .set_metadata("AAPL")
                  .set_target_company("AAPL", "Apple Inc.", "Technology")
                  .add_peer_company("MSFT", "Microsoft", 0.85)
                  .set_executive_summary("Overview", ["1", "2", "3"], ["A", "B", "C"]))
        
        # Add many recommendations
        categories = [RecommendationCategory.DO, RecommendationCategory.SAY, RecommendationCategory.SHOW]
        priorities = [RecommendationPriority.HIGH, RecommendationPriority.MEDIUM, RecommendationPriority.LOW]
        
        for i in range(25):
            builder.add_recommendation(
                f"Recommendation {i}",
                f"Description {i}",
                categories[i % 3],
                priorities[i % 3],
                f"Impact {i}"
            )
        
        report = builder.build()
        assert len(report.actionable_roadmap.recommendations) == 25


if __name__ == "__main__":
    pytest.main([__file__, "-v"])