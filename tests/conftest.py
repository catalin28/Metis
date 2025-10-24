"""Basic test configuration."""

import pytest
import os
from unittest.mock import MagicMock

# Test environment setup
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/metis_test")
os.environ.setdefault("FMP_API_KEY", "test_fmp_key")
os.environ.setdefault("OPENAI_API_KEY", "test_openai_key")
os.environ.setdefault("SECRET_KEY", "test_secret_key")


@pytest.fixture
def mock_fmp_client():
    """Mock FMP API client."""
    return MagicMock()


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    return MagicMock()


@pytest.fixture
def sample_company_data():
    """Sample company data for testing."""
    return {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "market_cap": 3000000000000,
        "country": "US"
    }


@pytest.fixture
def sample_peer_group():
    """Sample peer group for testing."""
    return [
        {"symbol": "MSFT", "similarity_score": 0.85},
        {"symbol": "GOOGL", "similarity_score": 0.82},
        {"symbol": "META", "similarity_score": 0.78},
        {"symbol": "AMZN", "similarity_score": 0.75},
    ]