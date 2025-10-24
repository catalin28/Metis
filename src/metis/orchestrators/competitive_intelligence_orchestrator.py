"""
Competitive Intelligence Orchestrator

Main coordinator for multi-company competitive intelligence analysis.
Orchestrates the entire pipeline from peer discovery to report generation.

This orchestrator follows the pipeline:
User Request (symbol) → Peer Discovery → Multi-Company Analysis → Comparative Synthesis → Report Generation

Key Features:
- Multi-method peer discovery (FMP screener + curated peers + manual filtering)
- Parallel processing of target company + 4-5 peers
- Fail-soft architecture (continues if individual peer analysis fails)
- Comprehensive valuation gap analysis with fundamental vs narrative decomposition
- Linguistic analysis of earnings transcripts
- Actionable recommendations in Do/Say/Show format

Author: Metis Development Team
Created: 2025-10-22
"""

import asyncio
import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any

from ..assistants.peer_discovery_service import PeerDiscoveryService
from ..core.config import get_config
from ..utils.exceptions import CompetitiveIntelligenceError


logger = logging.getLogger(__name__)


class CompetitiveIntelligenceOrchestrator:
    """
    Main orchestrator for competitive intelligence analysis.
    
    Coordinates the entire competitive intelligence pipeline:
    1. Peer discovery using multiple methods
    2. Parallel data collection for target + peers
    3. Comparative analysis and metric ranking
    4. Valuation gap decomposition 
    5. Linguistic analysis of earnings transcripts
    6. Report generation with actionable insights
    """
    
    def __init__(self):
        """Initialize the orchestrator with required services."""
        self.config = get_config()
        self.peer_discovery_service = PeerDiscoveryService()
        self.max_peers = self.config.get('PARALLEL_COMPANY_LIMIT', 5)
        self.processing_timeout = self.config.get('COMPETITIVE_INTEL_TIMEOUT_MINUTES', 10) * 60
        
        # Feature flag check
        if not self.config.get('COMPETITIVE_INTELLIGENCE_ENABLED', False):
            raise CompetitiveIntelligenceError(
                "Competitive intelligence feature is disabled. "
                "Set COMPETITIVE_INTELLIGENCE_ENABLED=true to enable."
            )
    
    async def generate_competitive_intelligence_report(
        self,
        target_symbol: str,
        client_id: Optional[str] = None,
        peer_symbols: Optional[List[str]] = None,
        include_sections: Optional[List[str]] = None,
        manual_peer_override: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive competitive intelligence report.
        
        Args:
            target_symbol: Stock symbol of target company (e.g., 'WRB')
            client_id: Optional client identifier for tracking and billing
            peer_symbols: Optional manual peer override list
            include_sections: Optional list of report sections to include
            manual_peer_override: Whether peer_symbols should override auto-discovery
            
        Returns:
            Dict containing complete competitive intelligence report in unified schema format
            
        Raises:
            CompetitiveIntelligenceError: If analysis fails or times out
        """
        report_id = str(uuid.uuid4())
        start_time = time.time()
        
        logger.info(f"Starting competitive intelligence analysis for {target_symbol} (Report ID: {report_id})")
        
        try:
            # Step 1: Peer Discovery
            if peer_symbols and manual_peer_override:
                logger.info(f"Using manual peer override: {peer_symbols}")
                peers = [{'symbol': symbol, 'similarityScore': 1.0, 'source': 'manual'} 
                        for symbol in peer_symbols[:self.max_peers]]
            else:
                logger.info(f"Discovering peers for {target_symbol}")
                peers = await self._discover_peers(target_symbol, peer_symbols)
            
            # Step 2: Parallel Data Collection
            logger.info(f"Collecting data for {target_symbol} and {len(peers)} peers")
            company_data = await self._collect_company_data(target_symbol, peers)
            
            # Step 3: Comparative Analysis
            logger.info("Performing comparative analysis")
            comparative_analysis = await self._perform_comparative_analysis(
                target_symbol, company_data
            )
            
            # Step 4: Valuation Gap Analysis
            logger.info("Analyzing valuation gaps")
            valuation_analysis = await self._analyze_valuation_gaps(
                target_symbol, company_data
            )
            
            # Step 5: Linguistic Analysis (if earnings transcripts available)
            logger.info("Performing linguistic analysis")
            linguistic_analysis = await self._perform_linguistic_analysis(
                target_symbol, company_data
            )
            
            # Step 6: Generate Unified Report
            logger.info("Generating unified report")
            report = await self._generate_unified_report(
                report_id=report_id,
                target_symbol=target_symbol,
                client_id=client_id,
                peers=peers,
                company_data=company_data,
                comparative_analysis=comparative_analysis,
                valuation_analysis=valuation_analysis,
                linguistic_analysis=linguistic_analysis,
                processing_time=time.time() - start_time,
                include_sections=include_sections or self._get_default_sections()
            )
            
            logger.info(f"Competitive intelligence analysis completed for {target_symbol} "
                       f"in {time.time() - start_time:.1f} seconds")
            
            return report
            
        except Exception as e:
            logger.error(f"Competitive intelligence analysis failed for {target_symbol}: {str(e)}")
            raise CompetitiveIntelligenceError(
                f"Failed to generate competitive intelligence report for {target_symbol}: {str(e)}"
            ) from e
    
    async def discover_peers_only(
        self,
        target_symbol: str,
        max_peers: Optional[int] = None,
        sector_override: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Discover peer companies without full analysis.
        
        Args:
            target_symbol: Stock symbol of target company
            max_peers: Maximum number of peers to return (default: config value)
            sector_override: Optional sector override for discovery
            
        Returns:
            List of peer companies with similarity scores
        """
        logger.info(f"Discovering peers for {target_symbol}")
        
        try:
            return await self.peer_discovery_service.identify_peers(
                symbol=target_symbol,
                max_peers=max_peers or self.max_peers,
                sector_override=sector_override
            )
        except Exception as e:
            logger.error(f"Peer discovery failed for {target_symbol}: {str(e)}")
            raise CompetitiveIntelligenceError(
                f"Failed to discover peers for {target_symbol}: {str(e)}"
            ) from e
    
    async def _discover_peers(
        self, 
        target_symbol: str, 
        supplemental_peers: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Discover peer companies using multi-method approach."""
        peers = await self.peer_discovery_service.identify_peers(
            symbol=target_symbol,
            max_peers=self.max_peers
        )
        
        # Supplement with manual peers if provided
        if supplemental_peers:
            manual_peers = [
                {'symbol': symbol, 'similarityScore': 0.95, 'source': 'manual'}
                for symbol in supplemental_peers
                if symbol not in [p['symbol'] for p in peers]
            ]
            peers.extend(manual_peers[:self.max_peers - len(peers)])
        
        return peers[:self.max_peers]
    
    async def _collect_company_data(
        self, 
        target_symbol: str, 
        peers: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Collect financial and market data for target company and peers in parallel."""
        all_symbols = [target_symbol] + [peer['symbol'] for peer in peers]
        
        # Use ThreadPoolExecutor for parallel API calls
        with ThreadPoolExecutor(max_workers=self.max_peers + 1) as executor:
            future_to_symbol = {
                executor.submit(self._collect_single_company_data, symbol): symbol
                for symbol in all_symbols
            }
            
            company_data = {}
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    data = future.result(timeout=60)  # 60 second timeout per company
                    company_data[symbol] = data
                except Exception as e:
                    logger.warning(f"Failed to collect data for {symbol}: {str(e)}")
                    # Fail-soft: continue without this company's data
                    company_data[symbol] = {'error': str(e), 'available': False}
        
        return company_data
    
    def _collect_single_company_data(self, symbol: str) -> Dict[str, Any]:
        """Collect comprehensive data for a single company."""
        # This is a placeholder - will be implemented with actual FMP API calls
        logger.info(f"Collecting data for {symbol}")
        
        # TODO: Implement actual data collection using FMP APIs:
        # - Company profile (/api/v3/profile/{symbol})
        # - Financial statements (/api/v3/income-statement/{symbol}, etc.)
        # - Key metrics (/api/v3/key-metrics/{symbol})
        # - Stock quotes (/api/v3/quote/{symbol})
        # - Earnings transcripts (/api/v3/earning_call_transcript/{symbol})
        
        return {
            'symbol': symbol,
            'available': True,
            'profile': {},
            'financials': {},
            'metrics': {},
            'quote': {},
            'transcripts': []
        }
    
    async def _perform_comparative_analysis(
        self,
        target_symbol: str,
        company_data: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform comparative analysis across all companies."""
        logger.info("Performing comparative financial analysis")
        
        # TODO: Implement comparative analysis logic:
        # - Calculate key ratios (ROE, P/E, debt ratios, etc.)
        # - Rank companies on each metric
        # - Identify hidden strengths (where target ranks #1 but trades at discount)
        # - Generate comparison tables
        
        return {
            'metrics_comparison': {},
            'rankings': {},
            'hidden_strengths': []
        }
    
    async def _analyze_valuation_gaps(
        self,
        target_symbol: str,
        company_data: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze valuation gaps with fundamental vs narrative decomposition."""
        logger.info("Analyzing valuation gaps")
        
        # TODO: Implement valuation gap analysis:
        # - Calculate P/E ratios for all companies
        # - Build regression model for "fair" P/E prediction
        # - Decompose gap into fundamental vs narrative components
        # - Generate valuation bridge data structure
        
        return {
            'target_pe': 0.0,
            'peer_average_pe': 0.0,
            'total_gap': 0.0,
            'fundamental_component': 0.0,
            'narrative_component': 0.0,
            'valuation_bridge': []
        }
    
    async def _perform_linguistic_analysis(
        self,
        target_symbol: str,
        company_data: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform linguistic analysis of earnings transcripts."""
        logger.info("Performing linguistic analysis")
        
        # TODO: Implement linguistic analysis:
        # - Extract and analyze phrases from earnings transcripts
        # - Calculate narrative scores
        # - Perform event study analysis
        # - Compare linguistic patterns across peers
        
        return {
            'narrative_score': 0,
            'linguistic_patterns': [],
            'peer_comparison': {},
            'event_study': {}
        }
    
    async def _generate_unified_report(
        self,
        report_id: str,
        target_symbol: str,
        client_id: Optional[str],
        peers: List[Dict[str, Any]],
        company_data: Dict[str, Dict[str, Any]],
        comparative_analysis: Dict[str, Any],
        valuation_analysis: Dict[str, Any],
        linguistic_analysis: Dict[str, Any],
        processing_time: float,
        include_sections: List[str]
    ) -> Dict[str, Any]:
        """Generate unified report in standardized schema format."""
        
        target_data = company_data.get(target_symbol, {})
        
        # Build unified report structure
        report = {
            "reportMetadata": {
                "reportId": report_id,
                "generatedAt": datetime.now(timezone.utc).isoformat(),
                "version": "1.0",
                "targetSymbol": target_symbol,
                "reportType": "competitive_intelligence",
                "period": f"Q{datetime.now().month//3 + 1}-{datetime.now().year}",
                "clientId": client_id
            },
            "companyProfile": {
                "symbol": target_symbol,
                "name": target_data.get('profile', {}).get('companyName', ''),
                "sector": target_data.get('profile', {}).get('sector', ''),
                "industry": target_data.get('profile', {}).get('industry', ''),
                "marketCap": target_data.get('profile', {}).get('mktCap', 0),
                "country": target_data.get('profile', {}).get('country', '')
            },
            "peerGroup": {
                "peers": peers,
                "selectionMethod": "automated" if not any(p.get('source') == 'manual' for p in peers) else "hybrid",
                "manualOverride": any(p.get('source') == 'manual' for p in peers)
            },
            "fundamentals": comparative_analysis,
            "valuation": valuation_analysis,
            "sentiment": linguistic_analysis,
            "recommendations": {
                "executive": "Placeholder executive summary",
                "actionableInsights": [],
                "stealTheirPlaybook": []
            },
            "metadata": {
                "processingTime": processing_time,
                "dataSourceTimestamps": {
                    "financialStatements": datetime.now().isoformat(),
                    "stockPrice": datetime.now().isoformat(),
                    "earningsTranscript": datetime.now().isoformat()
                },
                "llmTokensUsed": 0,
                "llmCostCents": 0,
                "cacheHits": 0,
                "cacheMisses": 0,
                "confidence": 0.85,
                "warnings": [],
                "errors": [
                    {"company": symbol, "error": data.get('error')}
                    for symbol, data in company_data.items()
                    if not data.get('available', True)
                ]
            }
        }
        
        return report
    
    def _get_default_sections(self) -> List[str]:
        """Get default report sections to include."""
        return [
            "executive_summary",
            "competitive_dashboard", 
            "hidden_strengths",
            "steal_their_playbook",
            "valuation_forensics",
            "actionable_roadmap"
        ]


class CompetitiveIntelligenceError(Exception):
    """Custom exception for competitive intelligence operations."""
    pass