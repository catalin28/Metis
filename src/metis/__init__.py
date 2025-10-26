"""Metis - Competitive Intelligence Platform.

An automated competitive intelligence system that generates comprehensive
peer analysis reports for any public company.

Public API for external projects:
    
    from metis import (
        generate_competitive_intelligence,
        generate_swing_trading_analysis,
        SwingTraderAnalyzer,
        CompetitiveIntelligenceClient
    )
"""

__version__ = "0.1.0"
__author__ = "Metis Development Team"
__email__ = "dev@metis.ai"

# Lazy imports to avoid circular dependencies
def __getattr__(name):
    """Lazy import for public API to avoid circular dependencies."""
    if name == "CompetitiveIntelligenceClient":
        from metis.api.client import CompetitiveIntelligenceClient
        return CompetitiveIntelligenceClient
    elif name == "generate_competitive_intelligence":
        from metis.api.functions import generate_competitive_intelligence
        return generate_competitive_intelligence
    elif name == "generate_swing_trading_analysis":
        from metis.api.functions import generate_swing_trading_analysis
        return generate_swing_trading_analysis
    elif name == "discover_peers":
        from metis.api.functions import discover_peers
        return discover_peers
    elif name == "SwingTraderAnalyzer":
        from metis.swing_trading import SwingTraderAnalyzer
        return SwingTraderAnalyzer
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    # Main API
    "CompetitiveIntelligenceClient",
    "generate_competitive_intelligence",
    "generate_swing_trading_analysis",
    "discover_peers",
    # Swing Trading
    "SwingTraderAnalyzer",
]