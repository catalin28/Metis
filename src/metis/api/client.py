"""
Client class for Metis API - object-oriented interface.

Provides a stateful client for managing API keys and configuration.
"""

from typing import Dict, Any, Optional, List
import asyncio

from .functions import (
    generate_competitive_intelligence,
    generate_swing_trading_analysis,
    discover_peers,
)


class CompetitiveIntelligenceClient:
    """
    High-level client for Metis competitive intelligence platform.
    
    This client maintains configuration (API keys, default settings) and provides
    a clean object-oriented interface for external projects.
    
    Example:
        >>> from metis import CompetitiveIntelligenceClient
        >>> 
        >>> client = CompetitiveIntelligenceClient(api_key="your-openai-key")
        >>> 
        >>> # Generate competitive intelligence
        >>> report = client.get_competitive_intelligence('AAPL')
        >>> 
        >>> # Generate swing trading analysis
        >>> analysis = client.get_swing_trading_analysis('TSLA', generate_narrative=True)
        >>> 
        >>> # Discover peers
        >>> peers = client.discover_peers('NVDA', max_peers=5)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = "gpt-4",
        default_sections: Optional[List[int]] = None
    ):
        """
        Initialize the Metis client.
        
        Args:
            api_key: OpenAI API key (uses environment variable if not provided)
            default_model: Default LLM model for narratives (default: gpt-4)
            default_sections: Default sections to generate (default: [1, 2, 2.5, 3])
        """
        self.api_key = api_key
        self.default_model = default_model
        self.default_sections = default_sections or [1, 2, 2.5, 3]
    
    async def get_competitive_intelligence_async(
        self,
        symbol: str,
        peer_symbols: Optional[List[str]] = None,
        sections: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Generate competitive intelligence report (async).
        
        Args:
            symbol: Target company ticker symbol
            peer_symbols: Optional list of peer symbols
            sections: Optional list of section numbers (uses default if None)
        
        Returns:
            Dictionary containing the complete competitive intelligence report
        """
        return await generate_competitive_intelligence(
            symbol=symbol,
            peer_symbols=peer_symbols,
            sections=sections or self.default_sections,
            api_key=self.api_key
        )
    
    def get_competitive_intelligence(
        self,
        symbol: str,
        peer_symbols: Optional[List[str]] = None,
        sections: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Generate competitive intelligence report (synchronous).
        
        Args:
            symbol: Target company ticker symbol
            peer_symbols: Optional list of peer symbols
            sections: Optional list of section numbers
        
        Returns:
            Dictionary containing the complete competitive intelligence report
        """
        return asyncio.run(self.get_competitive_intelligence_async(
            symbol=symbol,
            peer_symbols=peer_symbols,
            sections=sections
        ))
    
    async def get_swing_trading_analysis_async(
        self,
        symbol: str,
        peer_symbols: Optional[List[str]] = None,
        generate_narrative: bool = True,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate swing trading analysis (async).
        
        Args:
            symbol: Target company ticker symbol
            peer_symbols: Optional list of peer symbols
            generate_narrative: Whether to generate LLM narrative
            model: LLM model to use (uses default if None)
        
        Returns:
            Dictionary with competitive_intelligence, signals, and narrative
        """
        return await generate_swing_trading_analysis(
            symbol=symbol,
            peer_symbols=peer_symbols,
            generate_narrative=generate_narrative,
            model=model or self.default_model,
            api_key=self.api_key
        )
    
    def get_swing_trading_analysis(
        self,
        symbol: str,
        peer_symbols: Optional[List[str]] = None,
        generate_narrative: bool = True,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate swing trading analysis (synchronous).
        
        Args:
            symbol: Target company ticker symbol
            peer_symbols: Optional list of peer symbols
            generate_narrative: Whether to generate LLM narrative
            model: LLM model to use
        
        Returns:
            Dictionary with competitive_intelligence, signals, and narrative
        """
        return asyncio.run(self.get_swing_trading_analysis_async(
            symbol=symbol,
            peer_symbols=peer_symbols,
            generate_narrative=generate_narrative,
            model=model
        ))
    
    async def discover_peers_async(
        self,
        symbol: str,
        max_peers: int = 5
    ) -> Dict[str, Any]:
        """
        Discover peer companies (async).
        
        Args:
            symbol: Target company ticker symbol
            max_peers: Maximum number of peers to return
        
        Returns:
            Dictionary with target and peer company information
        """
        return await discover_peers(
            symbol=symbol,
            max_peers=max_peers,
            api_key=self.api_key
        )
    
    def discover_peers(
        self,
        symbol: str,
        max_peers: int = 5
    ) -> Dict[str, Any]:
        """
        Discover peer companies (synchronous).
        
        Args:
            symbol: Target company ticker symbol
            max_peers: Maximum number of peers to return
        
        Returns:
            Dictionary with target and peer company information
        """
        return asyncio.run(self.discover_peers_async(
            symbol=symbol,
            max_peers=max_peers
        ))
    
    def batch_competitive_intelligence(
        self,
        symbols: List[str],
        peer_symbols: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate competitive intelligence for multiple companies.
        
        Args:
            symbols: List of target company ticker symbols
            peer_symbols: Optional dict mapping symbols to peer lists
        
        Returns:
            Dictionary mapping symbols to their reports
        """
        results = {}
        for symbol in symbols:
            peers = peer_symbols.get(symbol) if peer_symbols else None
            results[symbol] = self.get_competitive_intelligence(
                symbol=symbol,
                peer_symbols=peers
            )
        return results
    
    def batch_swing_trading_analysis(
        self,
        symbols: List[str],
        generate_narrative: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate swing trading analysis for multiple companies.
        
        Args:
            symbols: List of target company ticker symbols
            generate_narrative: Whether to generate narratives
        
        Returns:
            Dictionary mapping symbols to their analyses
        """
        results = {}
        for symbol in symbols:
            results[symbol] = self.get_swing_trading_analysis(
                symbol=symbol,
                generate_narrative=generate_narrative
            )
        return results
