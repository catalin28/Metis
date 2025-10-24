"""
Tests for Peer Discovery Service

Comprehensive test suite for the peer discovery service including
multi-method discovery, similarity scoring, and error handling.

Author: Metis Development Team
Created: 2025-10-22
"""

import pytest
import math
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

from src.metis.assistants.peer_discovery_service import (
    PeerDiscoveryService,
    SimilarityComponents,
    PeerDiscoveryError
)


class TestPeerDiscoveryService:
    """Test suite for PeerDiscoveryService."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {}
    
    @pytest.fixture
    def mock_fmp_api_key(self):
        """Mock FMP API key."""
        return "test_api_key_12345"
    
    @pytest.fixture
    def service(self, mock_config, mock_fmp_api_key):
        """Create service instance with mocked dependencies."""
        with patch('src.metis.assistants.peer_discovery_service.get_config', return_value=mock_config):
            with patch('os.environ.get', return_value=mock_fmp_api_key):
                return PeerDiscoveryService()
    
    @pytest.fixture
    def sample_target_profile(self):
        """Sample target company profile."""
        return {
            'symbol': 'AAPL',
            'companyName': 'Apple Inc.',
            'sector': 'Technology',
            'industry': 'Consumer Electronics',
            'mktCap': 3000000000000,
            'revenue': 394328000000,
            'country': 'US'
        }
    
    @pytest.fixture
    def sample_candidate_profile(self):
        """Sample candidate company profile."""
        return {
            'symbol': 'MSFT',
            'companyName': 'Microsoft Corporation',
            'sector': 'Technology',
            'industry': 'Software',
            'mktCap': 2800000000000,
            'revenue': 211915000000,
            'country': 'US'
        }
    
    def test_initialization_success(self, mock_config, mock_fmp_api_key):
        """Test successful service initialization."""
        with patch('src.metis.assistants.peer_discovery_service.get_config', return_value=mock_config):
            with patch('os.environ.get', return_value=mock_fmp_api_key):
                service = PeerDiscoveryService()
                assert service.fmp_api_key == mock_fmp_api_key
                assert service.base_url == "https://financialmodelingprep.com"
                assert service.similarity_threshold == 0.60
    
    def test_initialization_missing_api_key(self, mock_config):
        """Test initialization failure when API key is missing."""
        with patch('src.metis.assistants.peer_discovery_service.get_config', return_value=mock_config):
            with patch('os.environ.get', return_value=None):
                with pytest.raises(ValueError, match="FMP_API_KEY environment variable is required"):
                    PeerDiscoveryService()
    
    def test_calculate_sector_score_exact_match(self, service):
        """Test sector score calculation with exact sector match."""
        # Act
        score = service._calculate_sector_score('Technology', 'Software', 'Technology', 'Hardware')
        
        # Assert
        assert score == 1.0
    
    def test_calculate_sector_score_industry_match(self, service):
        """Test sector score calculation with industry match only."""
        # Act
        score = service._calculate_sector_score('Technology', 'Software', 'Financial', 'Software')
        
        # Assert
        assert score == 0.5
    
    def test_calculate_sector_score_no_match(self, service):
        """Test sector score calculation with no match."""
        # Act
        score = service._calculate_sector_score('Technology', 'Software', 'Healthcare', 'Pharmaceuticals')
        
        # Assert
        assert score == 0.0
    
    def test_calculate_market_cap_score_equal_caps(self, service):
        """Test market cap score with equal market caps."""
        # Act
        score = service._calculate_market_cap_score(1000000000, 1000000000)
        
        # Assert
        assert score == 1.0
    
    def test_calculate_market_cap_score_similar_caps(self, service):
        """Test market cap score with similar market caps."""
        # Act
        score = service._calculate_market_cap_score(1000000000, 2000000000)  # 2x difference
        
        # Assert
        expected = 1.0 - abs(math.log10(0.5))  # log10(1B/2B) = log10(0.5)
        assert abs(score - expected) < 0.001
    
    def test_calculate_market_cap_score_zero_caps(self, service):
        """Test market cap score with zero market caps."""
        # Act
        score1 = service._calculate_market_cap_score(0, 1000000000)
        score2 = service._calculate_market_cap_score(1000000000, 0)
        
        # Assert
        assert score1 == 0.0
        assert score2 == 0.0
    
    def test_calculate_revenue_score_similar_revenues(self, service):
        """Test revenue score calculation."""
        # Act
        score = service._calculate_revenue_score(100000000, 200000000)  # 2x difference
        
        # Assert
        expected = 1.0 - abs(math.log10(0.5))
        assert abs(score - expected) < 0.001
    
    def test_calculate_geographic_score_same_country(self, service):
        """Test geographic score with same country."""
        # Act
        score = service._calculate_geographic_score('US', 'USA')
        
        # Assert
        assert score == 1.0
    
    def test_calculate_geographic_score_same_region(self, service):
        """Test geographic score with same region."""
        # Act
        score = service._calculate_geographic_score('US', 'Canada')
        
        # Assert
        assert score == 0.5
    
    def test_calculate_geographic_score_different_regions(self, service):
        """Test geographic score with different regions."""
        # Act
        score = service._calculate_geographic_score('US', 'Germany')
        
        # Assert
        assert score == 0.0  # US and Germany are in different regions
    
    def test_get_region_known_countries(self, service):
        """Test region identification for known countries."""
        # Act & Assert
        assert service._get_region('US') == 'North America'
        assert service._get_region('Germany') == 'Europe'
        assert service._get_region('Japan') == 'Asia-Pacific'
    
    def test_get_region_unknown_country(self, service):
        """Test region identification for unknown country."""
        # Act
        region = service._get_region('Unknown Country')
        
        # Assert
        assert region is None
    
    @pytest.mark.asyncio
    async def test_calculate_similarity_score(self, service, sample_target_profile, sample_candidate_profile):
        """Test comprehensive similarity score calculation."""
        # Act
        similarity = await service._calculate_similarity_score(sample_target_profile, sample_candidate_profile)
        
        # Assert
        assert isinstance(similarity, SimilarityComponents)
        assert similarity.sector_score == 1.0  # Same sector
        assert similarity.geographic_score == 1.0  # Same country
        assert 0 <= similarity.market_cap_score <= 1.0
        assert 0 <= similarity.revenue_score <= 1.0
        assert 0 <= similarity.final_score <= 1.0
        assert isinstance(similarity.explanation, str)
        
        # Check weighted calculation
        expected_score = (
            similarity.sector_score * 0.4 +
            similarity.market_cap_score * 0.3 +
            similarity.revenue_score * 0.2 +
            similarity.geographic_score * 0.1
        )
        assert abs(similarity.final_score - expected_score) < 0.001
    
    def test_deduplicate_peers_keeps_highest_score(self, service):
        """Test deduplication keeps peer with highest similarity score."""
        # Arrange
        peers = [
            {'symbol': 'MSFT', 'similarityScore': 0.75, 'source': 'screener'},
            {'symbol': 'GOOGL', 'similarityScore': 0.85, 'source': 'fmp_peers'},
            {'symbol': 'MSFT', 'similarityScore': 0.90, 'source': 'manual'},  # Higher score
        ]
        
        # Act
        result = service._deduplicate_peers(peers)
        
        # Assert
        assert len(result) == 2
        msft_peer = next(peer for peer in result if peer['symbol'] == 'MSFT')
        assert msft_peer['similarityScore'] == 0.90
        assert msft_peer['source'] == 'manual'
    
    @pytest.mark.asyncio
    async def test_get_company_profile_success(self, service):
        """Test successful company profile retrieval."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = [{'symbol': 'AAPL', 'companyName': 'Apple Inc.'}]
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.get', return_value=mock_response):
            # Act
            profile = await service._get_company_profile('AAPL')
            
            # Assert
            assert profile is not None
            assert profile['symbol'] == 'AAPL'
            assert profile['companyName'] == 'Apple Inc.'
    
    @pytest.mark.asyncio
    async def test_get_company_profile_failure(self, service):
        """Test company profile retrieval failure."""
        # Arrange
        with patch('requests.get', side_effect=Exception("API Error")):
            # Act
            profile = await service._get_company_profile('INVALID')
            
            # Assert
            assert profile is None
    
    @pytest.mark.asyncio
    async def test_get_company_profile_empty_response(self, service):
        """Test company profile retrieval with empty response."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.get', return_value=mock_response):
            # Act
            profile = await service._get_company_profile('NOTFOUND')
            
            # Assert
            assert profile is None
    
    @pytest.mark.asyncio
    async def test_discover_via_screener_success(self, service, sample_target_profile):
        """Test successful discovery via FMP screener."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = [
            {'symbol': 'MSFT', 'companyName': 'Microsoft Corporation'},
            {'symbol': 'GOOGL', 'companyName': 'Alphabet Inc.'}
        ]
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.get', return_value=mock_response):
            # Act
            candidates = await service._discover_via_screener(sample_target_profile, 'Technology', 10)
            
            # Assert
            assert len(candidates) == 2
            assert all(candidate['source'] == 'screener' for candidate in candidates)
            assert candidates[0]['symbol'] == 'MSFT'
            assert candidates[1]['symbol'] == 'GOOGL'
    
    @pytest.mark.asyncio
    async def test_discover_via_screener_failure(self, service, sample_target_profile):
        """Test screener discovery failure handling."""
        # Arrange
        with patch('requests.get', side_effect=Exception("API Error")):
            # Act
            candidates = await service._discover_via_screener(sample_target_profile, 'Technology', 10)
            
            # Assert
            assert candidates == []
    
    @pytest.mark.asyncio
    async def test_discover_via_fmp_peers_success(self, service, sample_target_profile):
        """Test successful discovery via FMP peers API."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = ['MSFT', 'GOOGL', 'META']
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.get', return_value=mock_response):
            with patch.object(service, '_get_company_profile') as mock_get_profile:
                mock_get_profile.side_effect = [
                    {'symbol': 'MSFT', 'companyName': 'Microsoft Corporation'},
                    {'symbol': 'GOOGL', 'companyName': 'Alphabet Inc.'},
                    {'symbol': 'META', 'companyName': 'Meta Platforms Inc.'}
                ]
                
                # Act
                candidates = await service._discover_via_fmp_peers('AAPL', sample_target_profile)
                
                # Assert
                assert len(candidates) == 3
                assert all(candidate['source'] == 'fmp_peers' for candidate in candidates)
    
    @pytest.mark.asyncio
    async def test_discover_via_fmp_peers_v4_fallback_to_v3(self, service, sample_target_profile):
        """Test FMP peers API fallback from v4 to v3."""
        # Arrange
        mock_response_v4 = Mock()
        mock_response_v4.status_code = 404  # v4 not available
        
        mock_response_v3 = Mock()
        mock_response_v3.status_code = 200
        mock_response_v3.json.return_value = ['MSFT', 'GOOGL']
        mock_response_v3.raise_for_status.return_value = None
        
        with patch('requests.get', side_effect=[mock_response_v4, mock_response_v3]):
            with patch.object(service, '_get_company_profile') as mock_get_profile:
                mock_get_profile.side_effect = [
                    {'symbol': 'MSFT', 'companyName': 'Microsoft Corporation'},
                    {'symbol': 'GOOGL', 'companyName': 'Alphabet Inc.'}
                ]
                
                # Act
                candidates = await service._discover_via_fmp_peers('AAPL', sample_target_profile)
                
                # Assert
                assert len(candidates) == 2
    
    @pytest.mark.asyncio
    async def test_discover_via_manual_filtering_placeholder(self, service, sample_target_profile):
        """Test manual filtering placeholder method."""
        # Act
        candidates = await service._discover_via_manual_filtering(sample_target_profile, 'Technology')
        
        # Assert
        assert candidates == []  # Placeholder implementation returns empty list
    
    @pytest.mark.asyncio
    async def test_add_manual_override_peers(self, service, sample_target_profile):
        """Test adding manual override peers."""
        # Arrange
        existing_peers = [
            {'symbol': 'MSFT', 'similarityScore': 0.85, 'source': 'screener'}
        ]
        manual_peers = ['GOOGL', 'META']
        
        with patch.object(service, '_get_company_profile') as mock_get_profile:
            mock_get_profile.side_effect = [
                {'symbol': 'GOOGL', 'companyName': 'Alphabet Inc.'},
                {'symbol': 'META', 'companyName': 'Meta Platforms Inc.'}
            ]
            
            with patch.object(service, '_calculate_similarity_score') as mock_calc_similarity:
                mock_similarity = SimilarityComponents(
                    sector_score=1.0, market_cap_score=0.8, revenue_score=0.7, 
                    geographic_score=1.0, final_score=0.88, explanation="Test"
                )
                mock_calc_similarity.return_value = mock_similarity
                
                # Act
                result = await service._add_manual_override_peers(
                    manual_peers, sample_target_profile, existing_peers, 5
                )
                
                # Assert
                assert len(result) == 3  # 1 existing + 2 manual
                manual_added = [peer for peer in result if peer['source'] == 'manual_override']
                assert len(manual_added) == 2
                assert manual_added[0]['symbol'] in ['GOOGL', 'META']
                assert manual_added[1]['symbol'] in ['GOOGL', 'META']
    
    @pytest.mark.asyncio
    async def test_identify_peers_full_workflow_success(self, service):
        """Test full peer identification workflow."""
        # Arrange
        target_profile = {
            'symbol': 'AAPL',
            'companyName': 'Apple Inc.',
            'sector': 'Technology',
            'mktCap': 3000000000000,
            'country': 'US'
        }
        
        screener_candidates = [
            {'symbol': 'MSFT', 'companyName': 'Microsoft Corporation', 'source': 'screener'}
        ]
        
        with patch.object(service, '_get_company_profile', return_value=target_profile):
            with patch.object(service, '_discover_via_screener', return_value=screener_candidates):
                with patch.object(service, '_discover_via_fmp_peers', return_value=[]):
                    with patch.object(service, '_discover_via_manual_filtering', return_value=[]):
                        with patch.object(service, '_calculate_similarity_score') as mock_similarity:
                            mock_similarity.return_value = SimilarityComponents(
                                sector_score=1.0, market_cap_score=0.8, revenue_score=0.7,
                                geographic_score=1.0, final_score=0.88, explanation="High similarity"
                            )
                            
                            # Act
                            result = await service.identify_peers('AAPL', max_peers=5)
                            
                            # Assert
                            assert len(result) == 1
                            assert result[0]['symbol'] == 'MSFT'
                            assert result[0]['similarityScore'] == 0.88
                            assert result[0]['source'] == 'screener'
    
    @pytest.mark.asyncio
    async def test_identify_peers_target_profile_failure(self, service):
        """Test peer identification when target profile retrieval fails."""
        # Arrange
        with patch.object(service, '_get_company_profile', return_value=None):
            # Act & Assert
            with pytest.raises(Exception, match="Could not retrieve profile for target company INVALID"):
                await service.identify_peers('INVALID')
    
    @pytest.mark.asyncio
    async def test_identify_peers_all_methods_fail(self, service):
        """Test peer identification when all discovery methods fail but still returns empty result."""
        # Arrange
        target_profile = {'symbol': 'AAPL', 'sector': 'Technology', 'mktCap': 3000000000000}
        
        with patch.object(service, '_get_company_profile', return_value=target_profile):
            with patch.object(service, '_discover_via_screener', side_effect=Exception("Screener failed")):
                with patch.object(service, '_discover_via_fmp_peers', side_effect=Exception("FMP peers failed")):
                    with patch.object(service, '_discover_via_manual_filtering', side_effect=Exception("Manual failed")):
                        
                        # Act
                        result = await service.identify_peers('AAPL')
                        
                        # Assert
                        assert result == []  # Should return empty list, not raise exception


class TestSimilarityComponents:
    """Test suite for SimilarityComponents dataclass."""
    
    def test_similarity_components_creation(self):
        """Test SimilarityComponents dataclass creation."""
        # Act
        components = SimilarityComponents(
            sector_score=0.8,
            market_cap_score=0.7,
            revenue_score=0.6,
            geographic_score=0.9,
            final_score=0.75,
            explanation="Test explanation"
        )
        
        # Assert
        assert components.sector_score == 0.8
        assert components.market_cap_score == 0.7
        assert components.revenue_score == 0.6
        assert components.geographic_score == 0.9
        assert components.final_score == 0.75
        assert components.explanation == "Test explanation"


class TestPeerDiscoveryError:
    """Test suite for PeerDiscoveryError exception."""
    
    def test_error_creation(self):
        """Test error creation and message."""
        # Act
        error = PeerDiscoveryError("Test error message")
        
        # Assert
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)