"""
Test Suite for Report Schema Models

Tests the Pydantic models for competitive intelligence reports.
"""

import pytest
from datetime import datetime
from decimal import Decimal

from src.metis.models.report_schema import (
    CompetitiveIntelligenceReport,
    ReportMetadata,
    CompanyProfile,
    PeerGroup,
    PeerCompany,
    ExecutiveSummary,
    CompetitiveDashboard,
    CompetitiveDashboardCompany,
    MarketPerceptionAnalysis,
    MarketPerceptionCategory,
    DataQuality,
    Priority
)


class TestReportSchemaModels:
    """Test cases for report schema Pydantic models"""
    
    def test_report_metadata_creation(self):
        """Test creating valid report metadata"""
        metadata = ReportMetadata(
            target_symbol="WRB",
            client_id="test_client_123"
        )
        
        assert metadata.target_symbol == "WRB"
        assert metadata.client_id == "test_client_123"
        assert metadata.schema_version == "1.0"
        assert isinstance(metadata.generated_at, datetime)
        assert len(metadata.report_id) == 36  # UUID length
    
    def test_report_metadata_invalid_symbol(self):
        """Test validation of invalid stock symbol"""
        with pytest.raises(ValueError) as exc_info:
            ReportMetadata(
                target_symbol="invalid_symbol_123",
                client_id="test_client"
            )
        
        assert "uppercase letters only" in str(exc_info.value)
    
    def test_company_profile_creation(self):
        """Test creating valid company profile"""
        profile = CompanyProfile(
            symbol="WRB",
            company_name="W.R. Berkley Corporation",
            sector="Financial Services",
            industry="Insurance",
            market_cap_billions=12.5
        )
        
        assert profile.symbol == "WRB"
        assert profile.market_cap_billions == 12.5
        assert profile.country == "US"  # Default value
        assert profile.data_quality == DataQuality.VALID  # Default value
    
    def test_company_profile_invalid_market_cap(self):
        """Test validation of invalid market cap"""
        with pytest.raises(ValueError) as exc_info:
            CompanyProfile(
                symbol="WRB",
                company_name="Test Company",
                sector="Financial Services",
                industry="Insurance",
                market_cap_billions=-5.0  # Invalid negative value
            )
        
        assert "greater than 0" in str(exc_info.value)
    
    def test_peer_group_creation(self):
        """Test creating valid peer group"""
        peers = [
            PeerCompany(
                symbol="PGR",
                company_name="Progressive Corporation",
                similarity_score=85.5,
                inclusion_reason="Industry leader comparison"
            ),
            PeerCompany(
                symbol="CB",
                company_name="Chubb Limited",
                similarity_score=78.2,
                inclusion_reason="Market cap similarity"
            ),
            PeerCompany(
                symbol="TRV", 
                company_name="The Travelers Companies",
                similarity_score=82.1,
                inclusion_reason="Business model alignment"
            )
        ]
        
        peer_group = PeerGroup(
            target_symbol="WRB",
            peers=peers,
            selection_criteria="Market cap and industry similarity"
        )
        
        assert peer_group.target_symbol == "WRB"
        assert len(peer_group.peers) == 3
        assert peer_group.peers[0].symbol == "PGR"
        assert peer_group.methodology == "market_cap_sector_similarity"  # Default
    
    def test_peer_group_insufficient_peers(self):
        """Test validation of insufficient peer count"""
        with pytest.raises(ValueError) as exc_info:
            PeerGroup(
                target_symbol="WRB",
                peers=[  # Only 2 peers, minimum is 3
                    PeerCompany(
                        symbol="PGR",
                        company_name="Progressive",
                        similarity_score=85.0,
                        inclusion_reason="Test"
                    ),
                    PeerCompany(
                        symbol="CB",
                        company_name="Chubb",
                        similarity_score=80.0,
                        inclusion_reason="Test"
                    )
                ],
                selection_criteria="Test criteria"
            )
        
        assert "at least 3" in str(exc_info.value)
    
    def test_peer_group_duplicate_symbols(self):
        """Test validation of duplicate peer symbols"""
        with pytest.raises(ValueError) as exc_info:
            PeerGroup(
                target_symbol="WRB",
                peers=[
                    PeerCompany(
                        symbol="PGR",
                        company_name="Progressive 1",
                        similarity_score=85.0,
                        inclusion_reason="Test"
                    ),
                    PeerCompany(
                        symbol="PGR",  # Duplicate symbol
                        company_name="Progressive 2",
                        similarity_score=80.0,
                        inclusion_reason="Test"
                    ),
                    PeerCompany(
                        symbol="CB",
                        company_name="Chubb",
                        similarity_score=75.0,
                        inclusion_reason="Test"
                    )
                ],
                selection_criteria="Test criteria"
            )
        
        assert "unique" in str(exc_info.value)
    
    def test_peer_group_target_in_peers(self):
        """Test validation that target is not in peer list"""
        with pytest.raises(ValueError) as exc_info:
            PeerGroup(
                target_symbol="WRB",
                peers=[
                    PeerCompany(
                        symbol="WRB",  # Target symbol in peers - invalid
                        company_name="W.R. Berkley",
                        similarity_score=100.0,
                        inclusion_reason="Test"
                    ),
                    PeerCompany(
                        symbol="PGR",
                        company_name="Progressive",
                        similarity_score=85.0,
                        inclusion_reason="Test"
                    ),
                    PeerCompany(
                        symbol="CB",
                        company_name="Chubb",
                        similarity_score=80.0,
                        inclusion_reason="Test"
                    )
                ],
                selection_criteria="Test criteria"
            )
        
        assert "cannot be included" in str(exc_info.value)
    
    def test_market_perception_analysis(self):
        """Test market perception analysis model"""
        analysis = MarketPerceptionAnalysis(
            category=MarketPerceptionCategory.UNDERVALUED,
            explanation="Company trades at discount due to market misunderstanding of specialty insurance model",
            analysis={
                "primary_driver": "combined_ratio_advantage",
                "market_bias": "complexity_discount",
                "potential_catalyst": "simplified_communication",
                "confidence_level": "high",
                "supporting_evidence": ["Best combined ratio", "Conservative reserves"]
            }
        )
        
        assert analysis.category == MarketPerceptionCategory.UNDERVALUED
        assert len(analysis.explanation) >= 50
        assert "primary_driver" in analysis.analysis
        assert "confidence_level" in analysis.analysis
    
    def test_market_perception_analysis_missing_fields(self):
        """Test validation of incomplete analysis structure"""
        with pytest.raises(ValueError) as exc_info:
            MarketPerceptionAnalysis(
                category=MarketPerceptionCategory.UNDERVALUED,
                explanation="Valid explanation text that meets minimum length requirements",
                analysis={
                    "primary_driver": "test",
                    # Missing required fields: market_bias, potential_catalyst, confidence_level
                }
            )
        
        assert "missing required keys" in str(exc_info.value)
    
    def test_executive_summary_creation(self):
        """Test creating valid executive summary"""
        summary = ExecutiveSummary(
            company_overview="W.R. Berkley Corporation is a specialty insurance company that operates through multiple segments. The company focuses on commercial lines and specialty markets, providing a diversified portfolio of insurance and reinsurance products. With strong underwriting discipline and conservative reserve management, WRB has consistently delivered superior combined ratios compared to industry averages.",
            key_finding="WRB trades at 12.1x earnings vs peer average of 15.1x, representing a 3.0x discount despite best-in-class combined ratio performance",
            root_cause="Market undervalues operational excellence due to complexity concerns and limited technology narrative",
            top_recommendations=[
                "Enhance investor communication with quarterly competitive positioning reports",
                "Develop technology narrative around AI-powered underwriting capabilities", 
                "Increase management guidance frequency and specificity"
            ]
        )
        
        assert len(summary.company_overview) >= 200
        assert len(summary.key_finding) >= 100
        assert len(summary.top_recommendations) == 3
    
    def test_executive_summary_validation_errors(self):
        """Test executive summary validation failures"""
        # Test short company overview
        with pytest.raises(ValueError) as exc_info:
            ExecutiveSummary(
                company_overview="Too short",  # Under 200 characters
                key_finding="Valid key finding that meets the minimum length requirement for this field",
                root_cause="Valid root cause explanation text",
                top_recommendations=["Rec 1", "Rec 2", "Rec 3"]
            )
        
        assert "at least 200" in str(exc_info.value)
        
        # Test insufficient recommendations
        with pytest.raises(ValueError) as exc_info:
            ExecutiveSummary(
                company_overview="Valid company overview that meets the minimum length requirement of two hundred characters for this particular field in the executive summary section",
                key_finding="Valid key finding that meets the minimum length requirement for this field",
                root_cause="Valid root cause explanation text",
                top_recommendations=["Rec 1", "Rec 2"]  # Only 2, need 3+
            )
        
        assert "at least 3" in str(exc_info.value)
    
    def test_competitive_dashboard_company(self):
        """Test competitive dashboard company model"""
        perception = MarketPerceptionAnalysis(
            category=MarketPerceptionCategory.UNDERVALUED,
            explanation="Company trades at discount despite strong fundamentals and operational performance",
            analysis={
                "primary_driver": "operational_excellence",
                "market_bias": "complexity_discount", 
                "potential_catalyst": "communication_improvement",
                "confidence_level": "high"
            }
        )
        
        company = CompetitiveDashboardCompany(
            symbol="WRB",
            company_name="W.R. Berkley Corporation",
            market_cap_billions=12.5,
            pe_ratio=12.1,
            roe_percentage=18.4,
            revenue_growth_percentage=8.5,
            debt_to_equity=0.41,
            combined_ratio=88.3,
            management_sentiment_score=76,
            analyst_confusion_score=42,
            overall_rank=3,
            market_perception=perception
        )
        
        assert company.symbol == "WRB"
        assert company.pe_ratio == 12.1
        assert company.combined_ratio == 88.3
        assert company.market_perception.category == MarketPerceptionCategory.UNDERVALUED
    
    def test_competitive_dashboard_company_validation(self):
        """Test competitive dashboard company validation"""
        perception = MarketPerceptionAnalysis(
            category=MarketPerceptionCategory.FAIR_VALUE,
            explanation="Company fairly valued by market with appropriate multiple",
            analysis={
                "primary_driver": "fair_valuation",
                "market_bias": "none",
                "potential_catalyst": "none", 
                "confidence_level": "medium"
            }
        )
        
        # Test invalid P/E ratio
        with pytest.raises(ValueError) as exc_info:
            CompetitiveDashboardCompany(
                symbol="TEST",
                company_name="Test Company",
                market_cap_billions=10.0,
                pe_ratio=-5.0,  # Invalid negative P/E
                roe_percentage=15.0,
                revenue_growth_percentage=5.0,
                debt_to_equity=0.5,
                management_sentiment_score=70,
                analyst_confusion_score=30,
                overall_rank=1,
                market_perception=perception
            )
        
        assert "greater than 0" in str(exc_info.value)
        
        # Test invalid sentiment score
        with pytest.raises(ValueError) as exc_info:
            CompetitiveDashboardCompany(
                symbol="TEST",
                company_name="Test Company", 
                market_cap_billions=10.0,
                pe_ratio=15.0,
                roe_percentage=15.0,
                revenue_growth_percentage=5.0,
                debt_to_equity=0.5,
                management_sentiment_score=150,  # Invalid score > 100
                analyst_confusion_score=30,
                overall_rank=1,
                market_perception=perception
            )
        
        assert "less than or equal to 100" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__])