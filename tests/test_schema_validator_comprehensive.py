"""
Comprehensive Test Suite for Schema Validator

Tests all validation rules, business logic, cross-field validation,
and data quality assessment functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from metis.models.validation_models import (
    ValidationResult,
    ValidationSeverity,
    SchemaValidator,
    BusinessRuleValidator,
    DataQualityValidator,
    CrossFieldValidator
)
from metis.models.report_schema_v2 import (
    CompetitiveIntelligenceReport,
    ReportMetadata,
    DataSource,
    CompanyProfile,
    PeerGroup,
    ExecutiveSummary,
    CompetitiveDashboard,
    MetricComparison,
    ActionableRoadmap,
    Recommendation,
    DataQuality,
    RecommendationCategory,
    RecommendationPriority
)


class TestValidationResult:
    """Test ValidationResult functionality"""
    
    def test_validation_result_success(self):
        """Test successful validation result"""
        result = ValidationResult(
            is_valid=True,
            severity=ValidationSeverity.INFO,
            issues=[],
            validation_time=0.05
        )
        
        assert result.is_valid
        assert result.severity == ValidationSeverity.INFO
        assert len(result.issues) == 0
        assert result.validation_time == 0.05
    
    def test_validation_result_failure(self):
        """Test failed validation result"""
        issues = ["Missing required field", "Invalid data type"]
        result = ValidationResult(
            is_valid=False,
            severity=ValidationSeverity.ERROR,
            issues=issues,
            validation_time=0.12
        )
        
        assert not result.is_valid
        assert result.severity == ValidationSeverity.ERROR
        assert len(result.issues) == 2
        assert "Missing required field" in result.issues
    
    def test_validation_result_warning(self):
        """Test validation result with warnings"""
        issues = ["Data quality could be improved", "Missing optional field"]
        result = ValidationResult(
            is_valid=True,
            severity=ValidationSeverity.WARNING,
            issues=issues,
            validation_time=0.08
        )
        
        assert result.is_valid  # Can be valid with warnings
        assert result.severity == ValidationSeverity.WARNING
        assert len(result.issues) == 2


class TestSchemaValidator:
    """Test main schema validator functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.validator = SchemaValidator()
    
    def create_valid_report(self) -> CompetitiveIntelligenceReport:
        """Helper to create valid report"""
        metadata = ReportMetadata(
            target_symbol="AAPL",
            generated_at=datetime.now(),
            version="1.0",
            report_id="test-report-123",
            processing_time_seconds=45.0
        )
        
        data_sources = [
            DataSource(
                source_type="financial_api",
                provider="FinancialModelingPrep",
                quality=DataQuality.VALID,
                data_date=datetime.now() - timedelta(days=1)
            )
        ]
        
        target_company = CompanyProfile(
            symbol="AAPL",
            company_name="Apple Inc.",
            sector="Technology",
            market_cap=3000000000000,
            pe_ratio=25.5,
            revenue_ttm=400000000000
        )
        
        peers = [
            CompanyProfile(symbol="MSFT", company_name="Microsoft", sector="Technology", market_cap=2800000000000),
            CompanyProfile(symbol="GOOGL", company_name="Alphabet", sector="Technology", market_cap=1800000000000)
        ]
        
        peer_group = PeerGroup(
            target_company=target_company,
            peers=peers,
            discovery_method="sector_similarity"
        )
        
        executive_summary = ExecutiveSummary(
            overview="Apple maintains strong competitive position in technology sector",
            key_insights=["Strong brand loyalty", "High profit margins", "Innovation leadership"],
            top_recommendations=["Expand services", "Improve supply chain", "Focus on AI"]
        )
        
        metric_comparisons = [
            MetricComparison(
                metric_name="P/E Ratio",
                target_value=25.5,
                peer_values={"MSFT": 28.2, "GOOGL": 22.1},
                target_ranking=2,
                analysis="Apple trades at moderate discount to Microsoft but premium to Google"
            )
        ]
        
        competitive_dashboard = CompetitiveDashboard(
            metric_comparisons=metric_comparisons,
            overall_ranking=2,
            strengths=["Best-in-class margins", "Strong brand loyalty"],
            weaknesses=["China dependency", "Hardware cyclicality"]
        )
        
        recommendations = [
            Recommendation(
                title="Expand AI capabilities",
                description="Integrate AI across product portfolio",
                category=RecommendationCategory.DO,
                priority=RecommendationPriority.HIGH,
                expected_impact="Competitive advantage and new revenue streams"
            ),
            Recommendation(
                title="Improve investor communication",
                description="Enhance quarterly presentations",
                category=RecommendationCategory.SAY,
                priority=RecommendationPriority.MEDIUM,
                expected_impact="Better analyst sentiment"
            ),
            Recommendation(
                title="Showcase innovation pipeline",
                description="Demonstrate technology leadership",
                category=RecommendationCategory.SHOW,
                priority=RecommendationPriority.HIGH,
                expected_impact="Market confidence"
            ),
            Recommendation(
                title="Optimize supply chain",
                description="Reduce dependency on single regions",
                category=RecommendationCategory.DO,
                priority=RecommendationPriority.MEDIUM,
                expected_impact="Risk reduction and cost savings"
            ),
            Recommendation(
                title="Engage with stakeholders",
                description="Better ESG communication",
                category=RecommendationCategory.SAY,
                priority=RecommendationPriority.LOW,
                expected_impact="Improved stakeholder trust"
            )
        ]
        
        actionable_roadmap = ActionableRoadmap(
            recommendations=recommendations,
            implementation_timeline="12-18 months",
            success_metrics=["Market share growth", "P/E multiple expansion", "Analyst coverage improvement"]
        )
        
        return CompetitiveIntelligenceReport(
            metadata=metadata,
            data_sources=data_sources,
            peer_group=peer_group,
            executive_summary=executive_summary,
            competitive_dashboard=competitive_dashboard,
            actionable_roadmap=actionable_roadmap
        )
    
    def test_validate_complete_valid_report(self):
        """Test validation of complete valid report"""
        report = self.create_valid_report()
        
        result = self.validator.validate_report(report)
        
        assert result.is_valid
        assert result.severity != ValidationSeverity.ERROR
        assert len([issue for issue in result.issues if "error" in issue.lower()]) == 0
    
    def test_validate_missing_metadata(self):
        """Test validation with missing metadata"""
        report = self.create_valid_report()
        report.metadata = None
        
        result = self.validator.validate_report(report)
        
        assert not result.is_valid
        assert result.severity == ValidationSeverity.ERROR
        assert any("metadata" in issue.lower() for issue in result.issues)
    
    def test_validate_empty_data_sources(self):
        """Test validation with empty data sources"""
        report = self.create_valid_report()
        report.data_sources = []
        
        result = self.validator.validate_report(report)
        
        assert not result.is_valid
        assert any("data source" in issue.lower() for issue in result.issues)
    
    def test_validate_missing_peer_group(self):
        """Test validation with missing peer group"""
        report = self.create_valid_report()
        report.peer_group = None
        
        result = self.validator.validate_report(report)
        
        assert not result.is_valid
        assert any("peer group" in issue.lower() for issue in result.issues)
    
    def test_validate_insufficient_recommendations(self):
        """Test validation with insufficient recommendations"""
        report = self.create_valid_report()
        report.actionable_roadmap.recommendations = [
            Recommendation(
                title="Only one",
                description="Single recommendation",
                category=RecommendationCategory.DO,
                priority=RecommendationPriority.HIGH,
                expected_impact="Limited impact"
            )
        ]
        
        result = self.validator.validate_report(report)
        
        assert not result.is_valid
        assert any("recommendation" in issue.lower() and "5" in issue for issue in result.issues)


class TestBusinessRuleValidator:
    """Test business logic validation"""
    
    def setup_method(self):
        self.validator = BusinessRuleValidator()
    
    def create_test_report(self):
        """Helper to create test report"""
        validator = SchemaValidator()
        return validator.create_valid_report()  # Reuse from schema validator
    
    def test_symbol_consistency_validation(self):
        """Test symbol consistency across report sections"""
        report = self.create_test_report()
        
        # Introduce symbol inconsistency
        report.peer_group.target_company.symbol = "MSFT"  # Wrong symbol
        
        result = self.validator.validate_business_rules(report)
        
        assert not result.is_valid
        assert any("symbol" in issue.lower() and "mismatch" in issue.lower() for issue in result.issues)
    
    def test_peer_uniqueness_validation(self):
        """Test peer company uniqueness"""
        report = self.create_test_report()
        
        # Add duplicate peer
        duplicate_peer = CompanyProfile(
            symbol="MSFT",  # Already exists
            company_name="Microsoft Corp",
            sector="Technology"
        )
        report.peer_group.peers.append(duplicate_peer)
        
        result = self.validator.validate_business_rules(report)
        
        assert not result.is_valid
        assert any("duplicate" in issue.lower() and "peer" in issue.lower() for issue in result.issues)
    
    def test_target_not_in_peers_validation(self):
        """Test that target company is not in peer list"""
        report = self.create_test_report()
        
        # Add target company as peer
        target_as_peer = CompanyProfile(
            symbol="AAPL",  # Same as target
            company_name="Apple Inc.",
            sector="Technology"
        )
        report.peer_group.peers.append(target_as_peer)
        
        result = self.validator.validate_business_rules(report)
        
        assert not result.is_valid
        assert any("target" in issue.lower() and "peer" in issue.lower() for issue in result.issues)
    
    def test_recommendation_category_distribution(self):
        """Test recommendation category distribution"""
        report = self.create_test_report()
        
        # Make all recommendations same category
        for rec in report.actionable_roadmap.recommendations:
            rec.category = RecommendationCategory.DO
        
        result = self.validator.validate_business_rules(report)
        
        # Should have warning about category distribution
        assert any("category" in issue.lower() and "distribution" in issue.lower() for issue in result.issues)
    
    def test_financial_metric_reasonableness(self):
        """Test financial metric reasonableness checks"""
        report = self.create_test_report()
        
        # Set unreasonable P/E ratio
        report.peer_group.target_company.pe_ratio = -5.0  # Negative P/E
        
        result = self.validator.validate_business_rules(report)
        
        assert any("ratio" in issue.lower() and "negative" in issue.lower() for issue in result.issues)
    
    def test_market_cap_consistency(self):
        """Test market cap vs sector consistency"""
        report = self.create_test_report()
        
        # Set tiny market cap for large tech company
        report.peer_group.target_company.market_cap = 1000000  # $1M market cap
        
        result = self.validator.validate_business_rules(report)
        
        # Should flag as potential data quality issue
        assert result.severity in [ValidationSeverity.WARNING, ValidationSeverity.ERROR]
    
    def test_peer_ranking_validation(self):
        """Test peer ranking validation in metrics"""
        report = self.create_test_report()
        
        # Set invalid ranking
        if report.competitive_dashboard.metric_comparisons:
            report.competitive_dashboard.metric_comparisons[0].target_ranking = 10  # Only 3 companies total
        
        result = self.validator.validate_business_rules(report)
        
        assert any("ranking" in issue.lower() for issue in result.issues)


class TestDataQualityValidator:
    """Test data quality validation"""
    
    def setup_method(self):
        self.validator = DataQualityValidator()
    
    def create_test_report(self):
        """Helper to create test report"""
        validator = SchemaValidator()
        return validator.create_valid_report()
    
    def test_data_freshness_validation(self):
        """Test data freshness validation"""
        report = self.create_test_report()
        
        # Set old data date
        old_date = datetime.now() - timedelta(days=400)  # Over 1 year old
        report.data_sources[0].data_date = old_date
        
        result = self.validator.validate_data_quality(report)
        
        assert any("stale" in issue.lower() or "old" in issue.lower() for issue in result.issues)
    
    def test_data_quality_flags(self):
        """Test data quality flag assessment"""
        report = self.create_test_report()
        
        # Set poor data quality
        report.data_sources[0].quality = DataQuality.ESTIMATED
        
        result = self.validator.validate_data_quality(report)
        
        # Should have warning about estimated data
        assert any("estimated" in issue.lower() or "quality" in issue.lower() for issue in result.issues)
    
    def test_missing_financial_data(self):
        """Test detection of missing financial data"""
        report = self.create_test_report()
        
        # Remove financial metrics
        report.peer_group.target_company.pe_ratio = None
        report.peer_group.target_company.market_cap = None
        report.peer_group.target_company.revenue_ttm = None
        
        result = self.validator.validate_data_quality(report)
        
        assert any("missing" in issue.lower() and "financial" in issue.lower() for issue in result.issues)
    
    def test_peer_data_completeness(self):
        """Test peer data completeness"""
        report = self.create_test_report()
        
        # Remove peer financial data
        for peer in report.peer_group.peers:
            peer.market_cap = None
            peer.pe_ratio = None
        
        result = self.validator.validate_data_quality(report)
        
        assert any("peer" in issue.lower() and "incomplete" in issue.lower() for issue in result.issues)
    
    def test_metric_comparison_data_quality(self):
        """Test metric comparison data quality"""
        report = self.create_test_report()
        
        # Create metric comparison with missing peer data
        if report.competitive_dashboard.metric_comparisons:
            comparison = report.competitive_dashboard.metric_comparisons[0]
            comparison.peer_values = {}  # No peer data
        
        result = self.validator.validate_data_quality(report)
        
        assert any("comparison" in issue.lower() and "peer" in issue.lower() for issue in result.issues)
    
    def test_extreme_outlier_detection(self):
        """Test detection of extreme outliers"""
        report = self.create_test_report()
        
        # Set extreme outlier values
        report.peer_group.target_company.pe_ratio = 500.0  # Extremely high P/E
        
        result = self.validator.validate_data_quality(report)
        
        assert any("outlier" in issue.lower() or "extreme" in issue.lower() for issue in result.issues)


class TestCrossFieldValidator:
    """Test cross-field validation logic"""
    
    def setup_method(self):
        self.validator = CrossFieldValidator()
    
    def create_test_report(self):
        """Helper to create test report"""
        validator = SchemaValidator()
        return validator.create_valid_report()
    
    def test_executive_summary_consistency(self):
        """Test executive summary consistency with data"""
        report = self.create_test_report()
        
        # Create inconsistency: claim "best performer" but rank is 2
        report.executive_summary.overview = "Apple is the best performing company in its peer group"
        report.competitive_dashboard.overall_ranking = 4  # Not best
        
        result = self.validator.validate_cross_field_consistency(report)
        
        assert any("inconsistent" in issue.lower() for issue in result.issues)
    
    def test_recommendation_alignment(self):
        """Test recommendation alignment with identified weaknesses"""
        report = self.create_test_report()
        
        # Set specific weakness
        report.competitive_dashboard.weaknesses = ["Poor customer service", "High debt levels"]
        
        # Check if recommendations address these weaknesses
        # This is a more complex validation that would need NLP analysis
        result = self.validator.validate_cross_field_consistency(report)
        
        # Should pass basic validation even without perfect alignment
        assert result.is_valid or result.severity != ValidationSeverity.ERROR
    
    def test_peer_group_sector_consistency(self):
        """Test peer group sector consistency"""
        report = self.create_test_report()
        
        # Mix different sectors in peer group
        report.peer_group.peers[0].sector = "Healthcare"  # Different from Technology
        
        result = self.validator.validate_cross_field_consistency(report)
        
        assert any("sector" in issue.lower() and "consistency" in issue.lower() for issue in result.issues)
    
    def test_timeline_recommendation_consistency(self):
        """Test timeline vs recommendation complexity consistency"""
        report = self.create_test_report()
        
        # Set very short timeline for complex recommendations
        report.actionable_roadmap.implementation_timeline = "1 month"
        
        # Add complex recommendation
        complex_rec = Recommendation(
            title="Complete digital transformation",
            description="Overhaul entire technology infrastructure and business processes",
            category=RecommendationCategory.DO,
            priority=RecommendationPriority.HIGH,
            expected_impact="Massive operational improvement"
        )
        report.actionable_roadmap.recommendations.append(complex_rec)
        
        result = self.validator.validate_cross_field_consistency(report)
        
        # Should flag unrealistic timeline
        assert any("timeline" in issue.lower() for issue in result.issues)
    
    def test_success_metrics_alignment(self):
        """Test success metrics alignment with recommendations"""
        report = self.create_test_report()
        
        # Set success metrics that don't align with recommendations
        report.actionable_roadmap.success_metrics = ["Manufacturing efficiency", "Physical store count"]
        # But all recommendations are about technology/AI (from create_valid_report)
        
        result = self.validator.validate_cross_field_consistency(report)
        
        # May flag misalignment
        assert result.is_valid or any("metric" in issue.lower() and "alignment" in issue.lower() for issue in result.issues)


class TestValidatorIntegration:
    """Test integrated validation workflow"""
    
    def setup_method(self):
        self.schema_validator = SchemaValidator()
        self.business_validator = BusinessRuleValidator()
        self.quality_validator = DataQualityValidator()
        self.cross_validator = CrossFieldValidator()
    
    def test_complete_validation_workflow(self):
        """Test complete validation workflow"""
        # Create valid report
        report = self.schema_validator.create_valid_report()
        
        # Run all validators
        schema_result = self.schema_validator.validate_report(report)
        business_result = self.business_validator.validate_business_rules(report)
        quality_result = self.quality_validator.validate_data_quality(report)
        cross_result = self.cross_validator.validate_cross_field_consistency(report)
        
        # All should pass for valid report
        assert schema_result.is_valid
        assert business_result.is_valid
        assert quality_result.is_valid
        assert cross_result.is_valid
    
    def test_validation_aggregation(self):
        """Test aggregating validation results"""
        report = self.schema_validator.create_valid_report()
        
        # Introduce multiple issues
        report.data_sources = []  # Schema issue
        report.peer_group.peers.append(report.peer_group.target_company)  # Business rule issue
        report.data_sources = [DataSource(
            source_type="test",
            provider="test",
            quality=DataQuality.ESTIMATED,  # Quality issue
            data_date=datetime.now() - timedelta(days=400)
        )]
        
        # Run all validators
        results = [
            self.schema_validator.validate_report(report),
            self.business_validator.validate_business_rules(report),
            self.quality_validator.validate_data_quality(report),
            self.cross_validator.validate_cross_field_consistency(report)
        ]
        
        # Aggregate issues
        all_issues = []
        max_severity = ValidationSeverity.INFO
        overall_valid = True
        
        for result in results:
            all_issues.extend(result.issues)
            if result.severity.value > max_severity.value:
                max_severity = result.severity
            if not result.is_valid:
                overall_valid = False
        
        assert not overall_valid
        assert max_severity == ValidationSeverity.ERROR
        assert len(all_issues) > 0
    
    def test_validation_performance(self):
        """Test validation performance with large reports"""
        report = self.schema_validator.create_valid_report()
        
        # Add many peers and recommendations
        for i in range(20):
            peer = CompanyProfile(
                symbol=f"PEER{i}",
                company_name=f"Peer Company {i}",
                sector="Technology",
                market_cap=1000000000 * (i + 1)
            )
            report.peer_group.peers.append(peer)
        
        for i in range(25):
            rec = Recommendation(
                title=f"Recommendation {i}",
                description=f"Description {i}",
                category=RecommendationCategory.DO,
                priority=RecommendationPriority.MEDIUM,
                expected_impact=f"Impact {i}"
            )
            report.actionable_roadmap.recommendations.append(rec)
        
        # Validation should still complete in reasonable time
        start_time = datetime.now()
        result = self.schema_validator.validate_report(report)
        end_time = datetime.now()
        
        validation_time = (end_time - start_time).total_seconds()
        assert validation_time < 5.0  # Should complete within 5 seconds
        assert result.is_valid


class TestValidatorEdgeCases:
    """Test validator edge cases and error handling"""
    
    def setup_method(self):
        self.validator = SchemaValidator()
    
    def test_none_report_validation(self):
        """Test validation with None report"""
        result = self.validator.validate_report(None)
        
        assert not result.is_valid
        assert result.severity == ValidationSeverity.ERROR
        assert any("None" in issue or "null" in issue.lower() for issue in result.issues)
    
    def test_empty_string_fields(self):
        """Test validation with empty string fields"""
        report = self.validator.create_valid_report()
        
        # Set empty strings
        report.metadata.target_symbol = ""
        report.peer_group.target_company.company_name = ""
        
        result = self.validator.validate_report(report)
        
        assert not result.is_valid
        assert any("empty" in issue.lower() for issue in result.issues)
    
    def test_special_character_handling(self):
        """Test handling of special characters in strings"""
        report = self.validator.create_valid_report()
        
        # Add special characters
        report.peer_group.target_company.company_name = "Apple Inc. 🍎 & Co."
        report.executive_summary.overview = "Analysis with émoji and ñ characters"
        
        result = self.validator.validate_report(report)
        
        # Should handle special characters gracefully
        assert result.is_valid or result.severity != ValidationSeverity.ERROR
    
    def test_very_long_strings(self):
        """Test handling of very long strings"""
        report = self.validator.create_valid_report()
        
        # Create very long description
        long_description = "Very long description. " * 1000  # ~22,000 characters
        report.actionable_roadmap.recommendations[0].description = long_description
        
        result = self.validator.validate_report(report)
        
        # Should handle long strings (may warn about length)
        assert result.is_valid or result.severity == ValidationSeverity.WARNING
    
    def test_unicode_handling(self):
        """Test Unicode character handling"""
        report = self.validator.create_valid_report()
        
        # Add Unicode characters
        report.peer_group.target_company.company_name = "Société Générale 中国银行"
        
        result = self.validator.validate_report(report)
        
        # Should handle Unicode gracefully
        assert result.is_valid or result.severity != ValidationSeverity.ERROR


if __name__ == "__main__":
    pytest.main([__file__, "-v"])