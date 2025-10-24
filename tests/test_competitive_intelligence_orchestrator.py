"""
Tests for Competitive Intelligence Orchestrator

Comprehensive test suite for the competitive intelligence orchestrator
including unit tests, integration tests, and error handling scenarios.

Author: Metis Development Team
Created: 2025-10-22
"""

import asyncio
import pytest
import uuid
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone
from typing import Dict, List, Any

from src.metis.orchestrators.competitive_intelligence_orchestrator import (
    CompetitiveIntelligenceOrchestrator,
    CompetitiveIntelligenceError
)


class TestCompetitiveIntelligenceOrchestrator:
    """Test suite for CompetitiveIntelligenceOrchestrator."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {
            'PARALLEL_COMPANY_LIMIT': 5,
            'COMPETITIVE_INTEL_TIMEOUT_MINUTES': 10,
            'COMPETITIVE_INTELLIGENCE_ENABLED': True
        }
    
    @pytest.fixture
    def mock_peer_discovery_service(self):
        """Mock peer discovery service."""
        mock_service = Mock()
        mock_service.identify_peers = AsyncMock(return_value=[
            {'symbol': 'MSFT', 'similarityScore': 0.85, 'source': 'screener'},
            {'symbol': 'GOOGL', 'similarityScore': 0.82, 'source': 'screener'},
            {'symbol': 'META', 'similarityScore': 0.78, 'source': 'fmp_peers'}
        ])
        return mock_service
    
    @pytest.fixture
    def orchestrator(self, mock_config, mock_peer_discovery_service):
        """Create orchestrator instance with mocked dependencies."""
        with patch('src.metis.orchestrators.competitive_intelligence_orchestrator.get_config', return_value=mock_config):
            with patch('src.metis.orchestrators.competitive_intelligence_orchestrator.PeerDiscoveryService', return_value=mock_peer_discovery_service):
                return CompetitiveIntelligenceOrchestrator()
    
    @pytest.fixture
    def sample_company_data(self):
        """Sample company data for testing."""
        return {
            'AAPL': {
                'symbol': 'AAPL',
                'available': True,
                'profile': {
                    'companyName': 'Apple Inc.',
                    'sector': 'Technology',
                    'industry': 'Consumer Electronics',
                    'mktCap': 3000000000000,
                    'country': 'US'
                },
                'financials': {'revenue': 394328000000},
                'metrics': {'pe': 25.5},
                'quote': {'price': 150.0},
                'transcripts': []
            },
            'MSFT': {
                'symbol': 'MSFT',
                'available': True,
                'profile': {
                    'companyName': 'Microsoft Corporation',
                    'sector': 'Technology',
                    'mktCap': 2800000000000,
                    'country': 'US'
                },
                'financials': {'revenue': 211915000000},
                'metrics': {'pe': 28.2},
                'quote': {'price': 420.0},
                'transcripts': []
            }
        }
    
    @pytest.mark.asyncio
    async def test_discover_peers_only_success(self, orchestrator, mock_peer_discovery_service):
        """Test successful peer discovery only operation."""
        # Act
        result = await orchestrator.discover_peers_only('AAPL')
        
        # Assert
        assert len(result) == 3
        assert result[0]['symbol'] == 'MSFT'
        assert result[0]['similarityScore'] == 0.85
        mock_peer_discovery_service.identify_peers.assert_called_once_with(
            symbol='AAPL',
            max_peers=5,
            sector_override=None
        )
    
    @pytest.mark.asyncio
    async def test_discover_peers_only_with_sector_override(self, orchestrator, mock_peer_discovery_service):
        """Test peer discovery with sector override."""
        # Act
        await orchestrator.discover_peers_only('AAPL', sector_override='Technology')
        
        # Assert
        mock_peer_discovery_service.identify_peers.assert_called_once_with(
            symbol='AAPL',
            max_peers=5,
            sector_override='Technology'
        )
    
    @pytest.mark.asyncio
    async def test_discover_peers_only_failure(self, orchestrator, mock_peer_discovery_service):
        """Test peer discovery failure handling."""
        # Arrange
        mock_peer_discovery_service.identify_peers.side_effect = Exception("API Error")
        
        # Act & Assert
        with pytest.raises(CompetitiveIntelligenceError, match="Failed to discover peers for AAPL"):
            await orchestrator.discover_peers_only('AAPL')
    
    @pytest.mark.asyncio
    async def test_discover_peers_with_supplemental(self, orchestrator):
        """Test internal _discover_peers method with supplemental peers."""
        # Arrange
        orchestrator.peer_discovery_service.identify_peers.return_value = [
            {'symbol': 'MSFT', 'similarityScore': 0.85, 'source': 'screener'}
        ]
        
        # Act
        result = await orchestrator._discover_peers('AAPL', ['GOOGL', 'META'])
        
        # Assert
        assert len(result) <= 5  # max_peers limit
        symbols = [peer['symbol'] for peer in result]
        assert 'MSFT' in symbols
        # Check that manual peers were added
        manual_peers = [peer for peer in result if peer.get('source') == 'manual']
        assert len(manual_peers) > 0
    
    def test_collect_single_company_data_placeholder(self, orchestrator):
        """Test single company data collection placeholder."""
        # Act
        result = orchestrator._collect_single_company_data('AAPL')
        
        # Assert
        assert result['symbol'] == 'AAPL'
        assert result['available'] == True
        assert 'profile' in result
        assert 'financials' in result
        assert 'metrics' in result
        assert 'quote' in result
        assert 'transcripts' in result
    
    @pytest.mark.asyncio
    async def test_collect_company_data_parallel(self, orchestrator, sample_company_data):
        """Test parallel company data collection."""
        # Arrange
        peers = [{'symbol': 'MSFT', 'similarityScore': 0.85}]
        
        with patch.object(orchestrator, '_collect_single_company_data') as mock_collect:
            mock_collect.side_effect = lambda symbol: sample_company_data.get(symbol, {'error': 'Not found', 'available': False})
            
            # Act
            result = await orchestrator._collect_company_data('AAPL', peers)
            
            # Assert
            assert 'AAPL' in result
            assert 'MSFT' in result
            assert result['AAPL']['available'] == True
            assert result['MSFT']['available'] == True
    
    @pytest.mark.asyncio
    async def test_collect_company_data_with_failures(self, orchestrator):
        """Test company data collection with some failures (fail-soft)."""
        # Arrange
        peers = [{'symbol': 'MSFT', 'similarityScore': 0.85}, {'symbol': 'INVALID', 'similarityScore': 0.70}]
        
        def mock_collect_data(symbol):
            if symbol == 'INVALID':
                raise Exception("Company not found")
            return {'symbol': symbol, 'available': True, 'profile': {}}
        
        with patch.object(orchestrator, '_collect_single_company_data', side_effect=mock_collect_data):
            # Act
            result = await orchestrator._collect_company_data('AAPL', peers)
            
            # Assert
            assert len(result) == 3  # AAPL + MSFT + INVALID
            assert result['AAPL']['available'] == True
            assert result['MSFT']['available'] == True
            assert result['INVALID']['available'] == False
            assert 'error' in result['INVALID']
    
    @pytest.mark.asyncio
    async def test_perform_comparative_analysis_placeholder(self, orchestrator, sample_company_data):
        """Test comparative analysis placeholder."""
        # Act
        result = await orchestrator._perform_comparative_analysis('AAPL', sample_company_data)
        
        # Assert
        assert 'metrics_comparison' in result
        assert 'rankings' in result
        assert 'hidden_strengths' in result
    
    @pytest.mark.asyncio
    async def test_analyze_valuation_gaps_placeholder(self, orchestrator, sample_company_data):
        """Test valuation gap analysis placeholder."""
        # Act
        result = await orchestrator._analyze_valuation_gaps('AAPL', sample_company_data)
        
        # Assert
        assert 'target_pe' in result
        assert 'peer_average_pe' in result
        assert 'total_gap' in result
        assert 'fundamental_component' in result
        assert 'narrative_component' in result
        assert 'valuation_bridge' in result
    
    @pytest.mark.asyncio
    async def test_perform_linguistic_analysis_placeholder(self, orchestrator, sample_company_data):
        """Test linguistic analysis placeholder."""
        # Act
        result = await orchestrator._perform_linguistic_analysis('AAPL', sample_company_data)
        
        # Assert
        assert 'narrative_score' in result
        assert 'linguistic_patterns' in result
        assert 'peer_comparison' in result
        assert 'event_study' in result
    
    @pytest.mark.asyncio
    async def test_generate_unified_report_structure(self, orchestrator, sample_company_data):
        """Test unified report generation structure."""
        # Arrange
        report_id = str(uuid.uuid4())
        peers = [{'symbol': 'MSFT', 'similarityScore': 0.85, 'source': 'screener'}]
        comparative_analysis = {'metrics_comparison': {}, 'rankings': {}}
        valuation_analysis = {'target_pe': 25.5, 'peer_average_pe': 28.0}
        linguistic_analysis = {'narrative_score': 0}
        
        # Act
        result = await orchestrator._generate_unified_report(
            report_id=report_id,
            target_symbol='AAPL',
            client_id='test_client',
            peers=peers,
            company_data=sample_company_data,
            comparative_analysis=comparative_analysis,
            valuation_analysis=valuation_analysis,
            linguistic_analysis=linguistic_analysis,
            processing_time=45.2,
            include_sections=['executive_summary', 'competitive_dashboard']
        )
        
        # Assert
        assert result['reportMetadata']['reportId'] == report_id
        assert result['reportMetadata']['targetSymbol'] == 'AAPL'
        assert result['reportMetadata']['clientId'] == 'test_client'
        assert result['companyProfile']['symbol'] == 'AAPL'
        assert result['companyProfile']['name'] == 'Apple Inc.'
        assert result['peerGroup']['peers'] == peers
        assert result['fundamentals'] == comparative_analysis
        assert result['valuation'] == valuation_analysis
        assert result['sentiment'] == linguistic_analysis
        assert result['metadata']['processingTime'] == 45.2
        assert len(result['metadata']['errors']) == 0  # No failed companies in sample data
    
    def test_get_default_sections(self, orchestrator):
        """Test default report sections."""
        # Act
        sections = orchestrator._get_default_sections()
        
        # Assert
        expected_sections = [
            "executive_summary",
            "competitive_dashboard",
            "hidden_strengths", 
            "steal_their_playbook",
            "valuation_forensics",
            "actionable_roadmap"
        ]
        assert sections == expected_sections
    
    def test_initialization_feature_disabled(self, mock_peer_discovery_service):
        """Test orchestrator initialization when feature is disabled."""
        # Arrange
        disabled_config = {
            'PARALLEL_COMPANY_LIMIT': 5,
            'COMPETITIVE_INTEL_TIMEOUT_MINUTES': 10,
            'COMPETITIVE_INTELLIGENCE_ENABLED': False
        }
        
        # Act & Assert
        with patch('src.metis.orchestrators.competitive_intelligence_orchestrator.get_config', return_value=disabled_config):
            with patch('src.metis.orchestrators.competitive_intelligence_orchestrator.PeerDiscoveryService', return_value=mock_peer_discovery_service):
                with pytest.raises(CompetitiveIntelligenceError, match="Competitive intelligence feature is disabled"):
                    CompetitiveIntelligenceOrchestrator()
    
    @pytest.mark.asyncio
    async def test_generate_full_report_manual_peer_override(self, orchestrator, sample_company_data):
        """Test full report generation with manual peer override."""
        # Arrange
        manual_peers = ['MSFT', 'GOOGL']
        
        with patch.object(orchestrator, '_collect_company_data', return_value=sample_company_data):
            with patch.object(orchestrator, '_perform_comparative_analysis', return_value={'rankings': {}}):
                with patch.object(orchestrator, '_analyze_valuation_gaps', return_value={'total_gap': 0.0}):
                    with patch.object(orchestrator, '_perform_linguistic_analysis', return_value={'narrative_score': 0}):
                        with patch.object(orchestrator, '_generate_unified_report', return_value={'reportId': 'test'}):
                            
                            # Act
                            result = await orchestrator.generate_competitive_intelligence_report(
                                target_symbol='AAPL',
                                peer_symbols=manual_peers,
                                manual_peer_override=True
                            )
                            
                            # Assert
                            assert result is not None
                            # Verify peer discovery was bypassed for manual override
                            orchestrator.peer_discovery_service.identify_peers.assert_not_called()


class TestCompetitiveIntelligenceError:
    """Test suite for CompetitiveIntelligenceError exception."""
    
    def test_error_creation(self):
        """Test error creation and message."""
        # Act
        error = CompetitiveIntelligenceError("Test error message")
        
        # Assert
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)