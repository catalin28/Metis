"""Public API for Metis - Competitive Intelligence Platform."""

from .client import CompetitiveIntelligenceClient
from .functions import (
    generate_competitive_intelligence,
    generate_swing_trading_analysis,
    discover_peers,
)

__all__ = [
    "CompetitiveIntelligenceClient",
    "generate_competitive_intelligence",
    "generate_swing_trading_analysis",
    "discover_peers",
]