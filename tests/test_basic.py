"""Test basic functionality."""

import pytest
from metis import __version__
from metis.core.config import settings
from metis.orchestrators.competitive_intelligence_orchestrator import CompetitiveIntelligenceOrchestrator
from metis.assistants.peer_discovery_service import PeerDiscoveryService


def test_version():
    """Test that version is set."""
    assert __version__ == "0.1.0"


def test_settings():
    """Test that settings can be loaded."""
    assert settings.competitive_intelligence_enabled is True
    assert settings.max_peers_per_analysis == 5


def test_orchestrator():
    """Test orchestrator basic functionality."""
    orchestrator = CompetitiveIntelligenceOrchestrator()
    result = orchestrator.generate_report("AAPL")
    
    assert result["status"] == "success"
    assert result["target_symbol"] == "AAPL"
    assert "report_data" in result


def test_peer_discovery():
    """Test peer discovery service."""
    service = PeerDiscoveryService()
    peers = service.identify_peers("AAPL")
    
    assert len(peers) <= 5  # Default max_peers
    assert all("symbol" in peer for peer in peers)
    assert all("similarity_score" in peer for peer in peers)