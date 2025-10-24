"""
Peer Discovery Service

Multi-method peer discovery system for competitive intelligence analysis.
Auto-identifies peer companies using sector + market cap similarity with multiple fallback methods.

Discovery Methods (in order of preference):
1. FMP Company Screener - Comprehensive sector-based filtering
2. FMP Stock Peers API - Curated peer relationships  
3. Manual Filtering - Profile-based sector + market cap filtering

Similarity Scoring Algorithm:
- Sector match (40% weight): Exact sector vs industry group vs different
- Market cap ratio (30% weight): Logarithmic scale for size similarity
- Revenue proximity (20% weight): TTM revenue comparison
- Geographic overlap (10% weight): Country/region matching

Author: Metis Development Team
Created: 2025-10-22
"""

import asyncio
import logging
import math
import os
from typing import Dict, List, Optional, Any
import requests
from dataclasses import dataclass

from ..core.config import get_config


logger = logging.getLogger(__name__)


@dataclass
class SimilarityComponents:
    """Components of similarity scoring calculation."""
    sector_score: float
    market_cap_score: float
    revenue_score: float
    geographic_score: float
    final_score: float
    explanation: str


class PeerDiscoveryService:
    """
    Service for discovering peer companies using multiple methods.
    
    Implements a comprehensive peer discovery system that combines:
    - FMP company screener for broad sector-based discovery
    - FMP stock peers API for curated relationships
    - Manual filtering as fallback
    - Sophisticated similarity scoring algorithm
    """
    
    def __init__(self):
        """Initialize the peer discovery service."""
        self.config = get_config()
        self.fmp_api_key = os.environ.get('FMP_API_KEY')
        if not self.fmp_api_key:
            raise ValueError("FMP_API_KEY environment variable is required")
        
        self.base_url = "https://financialmodelingprep.com"
        self.similarity_threshold = 0.30  # Lowered to 0.30 to include more peers (screener already filters by sector/industry)
        
        # Regional mappings for geographic scoring
        self.regions = {
            'North America': ['US', 'USA', 'Canada', 'Mexico'],
            'Europe': ['UK', 'Germany', 'France', 'Italy', 'Spain', 'Netherlands', 'Switzerland', 'Sweden', 'Norway'],
            'Asia-Pacific': ['China', 'Japan', 'India', 'Australia', 'Singapore', 'South Korea', 'Hong Kong']
        }
    
    async def identify_peers(
        self,
        symbol: str,
        max_peers: int = 5,
        sector_override: Optional[str] = None,
        manual_override_peers: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Identify peer companies using multi-method approach.
        
        Args:
            symbol: Target company stock symbol
            max_peers: Maximum number of peers to return
            sector_override: Optional sector override for discovery
            manual_override_peers: Optional manual peer list to supplement results
            
        Returns:
            List of peer companies with similarity scores, sorted by score descending
            
        Raises:
            Exception: If all discovery methods fail
        """
        logger.info(f"Starting peer discovery for {symbol} (max_peers: {max_peers})")
        
        try:
            # Step 1: Get target company profile
            target_profile = await self._get_company_profile(symbol)
            if not target_profile:
                raise Exception(f"Could not retrieve profile for target company {symbol}")
            
            target_sector = sector_override or target_profile.get('sector', '')
            logger.info(f"Target company: {symbol} | Sector: {target_sector} | Market Cap: ${target_profile.get('mktCap', 0):,.0f}")
            
            # Step 2: Industry-focused peer discovery
            industry_candidates = []
            
            # Method 1: FMP Company Screener (Industry Peers - Primary for financial analysis)
            try:
                screener_candidates = await self._discover_via_screener(target_profile, target_sector, max_peers * 3)
                industry_candidates.extend(screener_candidates)
                logger.info(f"Screener method found {len(screener_candidates)} industry peer candidates")
            except Exception as e:
                logger.warning(f"Screener method failed: {str(e)}")
            
            # Method 2: Manual filtering (Fallback if not enough industry peers found)
            manual_candidates = []
            if len(industry_candidates) < max_peers:
                try:
                    fallback_candidates = await self._discover_via_manual_filtering(target_profile, target_sector)
                    manual_candidates.extend(fallback_candidates)
                    logger.info(f"Manual filtering found {len(fallback_candidates)} additional candidates")
                except Exception as e:
                    logger.warning(f"Manual filtering failed: {str(e)}")
            
            # Step 3: Combine candidates (prioritizing industry matches)
            all_candidates = industry_candidates + manual_candidates
            
            # Calculate similarity scores and rank with peer type weighting
            scored_peers = []
            for candidate in all_candidates:
                if candidate['symbol'] != symbol:  # Exclude target company
                    try:
                        similarity = await self._calculate_similarity_score(target_profile, candidate)
                        
                        # Classify peer type based on actual business similarity
                        peer_type = self._classify_peer_type(target_profile, candidate)
                        
                        # Apply peer type weighting for prioritization
                        weighted_score = similarity.final_score
                        if peer_type == 'industry':
                            weighted_score *= 1.3  # 30% boost for same industry
                        elif peer_type == 'sector':
                            weighted_score *= 1.1  # 10% boost for same sector
                        elif peer_type == 'financial':
                            weighted_score *= 1.0  # No boost for different sector/industry
                        
                        if similarity.final_score >= self.similarity_threshold:
                            scored_peers.append({
                                'symbol': candidate['symbol'],
                                'name': candidate.get('companyName', ''),
                                'similarityScore': round(similarity.final_score, 3),
                                'weightedScore': round(min(weighted_score, 1.0), 3),  # Cap at 1.0
                                'source': candidate.get('source', 'unknown'),
                                'peerType': peer_type,
                                'components': {
                                    'sectorScore': similarity.sector_score,
                                    'marketCapScore': similarity.market_cap_score,
                                    'revenueScore': similarity.revenue_score,
                                    'geographicScore': similarity.geographic_score
                                },
                                'explanation': similarity.explanation
                            })
                    except Exception as e:
                        logger.warning(f"Failed to score candidate {candidate.get('symbol', 'unknown')}: {str(e)}")
            
            # Step 4: Remove duplicates and sort by weighted score (prioritizing industry peers)
            unique_peers = self._deduplicate_peers(scored_peers)
            final_peers = sorted(unique_peers, key=lambda x: x['weightedScore'], reverse=True)[:max_peers]
            
            # Log peer type distribution
            type_counts = {}
            for peer in final_peers:
                peer_type = peer.get('peerType', 'unknown')
                type_counts[peer_type] = type_counts.get(peer_type, 0) + 1
            logger.info(f"Final peer distribution: {type_counts}")
            
            # Step 5: Add manual override peers if provided
            if manual_override_peers:
                manual_peers = await self._add_manual_override_peers(
                    manual_override_peers, target_profile, final_peers, max_peers
                )
                final_peers = manual_peers
            
            logger.info(f"Peer discovery completed for {symbol}. Found {len(final_peers)} peers: "
                       f"{[p['symbol'] for p in final_peers]}")
            
            return final_peers
            
        except Exception as e:
            logger.error(f"Peer discovery failed for {symbol}: {str(e)}")
            raise Exception(f"Failed to discover peers for {symbol}: {str(e)}") from e
    
    async def _get_company_profile(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get company profile from FMP API."""
        try:
            url = f"{self.base_url}/api/v3/profile/{symbol}"
            params = {'apikey': self.fmp_api_key}
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if data and len(data) > 0:
                return data[0]
            return None
            
        except Exception as e:
            logger.error(f"Failed to get profile for {symbol}: {str(e)}")
            return None
    
    async def _discover_via_screener(
        self, 
        target_profile: Dict[str, Any], 
        target_sector: str, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """Discover peers using FMP company screener."""
        target_market_cap = target_profile.get('mktCap', 0)
        target_industry = target_profile.get('industry', '')
        
        all_candidates = []
        
        # Try 1: Industry + Sector filter (no market cap filter - we'll select closest later)
        if target_industry:
            try:
                url = f"{self.base_url}/stable/company-screener"
                params = {
                    'apikey': self.fmp_api_key,
                    'sector': target_sector,
                    'industry': target_industry,
                    'isActivelyTrading': 'true',
                    'limit': 100  # Get more candidates to choose from
                }
                
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                candidates = response.json()
                if candidates:
                    for candidate in candidates:
                        candidate['source'] = 'screener_industry'
                        candidate = self._normalize_company_data(candidate, 'screener_industry')
                    all_candidates.extend(candidates)
                    logger.info(f"Screener found {len(candidates)} companies with industry={target_industry}")
            except Exception as e:
                logger.warning(f"Industry-specific screener failed: {str(e)}")
        
        # Try 2: Sector-only filter (if we need more peers)
        if len(all_candidates) < limit * 2:
            try:
                url = f"{self.base_url}/stable/company-screener"
                params = {
                    'apikey': self.fmp_api_key,
                    'sector': target_sector,
                    'isActivelyTrading': 'true',
                    'limit': 100  # Get more candidates to choose from
                }
                
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                candidates = response.json()
                if candidates:
                    for candidate in candidates:
                        candidate['source'] = 'screener_sector'
                        candidate = self._normalize_company_data(candidate, 'screener_sector')
                    all_candidates.extend(candidates)
                    logger.info(f"Screener found {len(candidates)} additional companies with sector={target_sector}")
            except Exception as e:
                logger.warning(f"Sector-only screener failed: {str(e)}")
        
        # Deduplicate by symbol
        unique_candidates = {}
        for candidate in all_candidates:
            symbol = candidate.get('symbol')
            if symbol and symbol not in unique_candidates:
                unique_candidates[symbol] = candidate
        
        # Sort by market cap proximity to target and take closest ones
        candidates_list = list(unique_candidates.values())
        if target_market_cap > 0:
            candidates_list.sort(key=lambda x: abs(x.get('mktCap', 0) - target_market_cap))
            logger.info(f"Sorted {len(candidates_list)} candidates by market cap proximity to ${target_market_cap:,.0f}")
        
        result = candidates_list[:limit * 3]  # Return 3x limit for similarity scoring to choose from
        logger.info(f"Screener returning {len(result)} closest market cap peers from {target_sector} sector")
        return result
    
    async def _discover_via_fmp_peers(
        self, 
        symbol: str, 
        target_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Discover peers using FMP stock peers API."""
        try:
            # Try v4 API first
            url = f"{self.base_url}/api/v4/stock_peers"
            params = {'symbol': symbol, 'apikey': self.fmp_api_key}
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                # Fallback to v3 API
                url = f"{self.base_url}/api/v3/stock-peers"
                response = requests.get(url, params=params, timeout=30)
            
            response.raise_for_status()
            data = response.json()
            
            if not data:
                return []
            
            # Extract peer symbols - handle different response formats
            peer_symbols = []
            if isinstance(data, list) and len(data) > 0:
                # v4 API returns [{"symbol": "M", "peersList": [...]}]
                first_item = data[0]
                if isinstance(first_item, dict) and 'peersList' in first_item:
                    peer_symbols = first_item['peersList']
                else:
                    # Direct list of symbols
                    peer_symbols = data
            elif isinstance(data, dict):
                # v3 API or other format
                peer_symbols = data.get('peersList', [])
            else:
                peer_symbols = data if isinstance(data, list) else []
            
            # Get profiles for each peer
            candidates = []
            for peer_symbol in peer_symbols[:10]:  # Limit to 10 to avoid too many API calls
                profile = await self._get_company_profile(peer_symbol)
                if profile:
                    profile = self._normalize_company_data(profile, 'fmp_peers')
                    candidates.append(profile)
            
            logger.info(f"FMP peers API found {len(candidates)} peer companies")
            return candidates
            
        except Exception as e:
            logger.error(f"FMP peers discovery failed: {str(e)}")
            return []
    
    async def _discover_via_manual_filtering(
        self, 
        target_profile: Dict[str, Any], 
        target_sector: str
    ) -> List[Dict[str, Any]]:
        """Manual filtering fallback method (placeholder for now)."""
        # This would implement a broader search and manual filtering
        # For now, return empty list as this requires more extensive company database
        logger.info("Manual filtering method not yet implemented")
        return []
    
    def _normalize_company_data(self, company_data: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Normalize company data from different API endpoints to consistent field names."""
        normalized = company_data.copy()
        
        # Normalize market cap field
        if 'marketCap' in company_data and 'mktCap' not in company_data:
            normalized['mktCap'] = company_data['marketCap']
        elif 'mktCap' not in company_data and 'marketCap' not in company_data:
            normalized['mktCap'] = 0
        
        # Normalize revenue field (if available)
        if 'revenue' not in normalized:
            normalized['revenue'] = 0
        
        # Add source for tracking
        normalized['source'] = source
        
        return normalized
    
    async def _calculate_similarity_score(
        self, 
        target_profile: Dict[str, Any], 
        candidate_profile: Dict[str, Any]
    ) -> SimilarityComponents:
        """Calculate comprehensive similarity score between target and candidate."""
        
        # Component 1: Sector match (40% weight)
        sector_score = self._calculate_sector_score(
            target_profile.get('sector', ''),
            target_profile.get('industry', ''),
            candidate_profile.get('sector', ''),
            candidate_profile.get('industry', '')
        )
        
        # Component 2: Market cap ratio (30% weight) 
        market_cap_score = self._calculate_market_cap_score(
            target_profile.get('mktCap', 0),
            candidate_profile.get('mktCap', 0)
        )
        
        # Component 3: Revenue proximity (20% weight)
        revenue_score = self._calculate_revenue_score(
            target_profile.get('revenue', 0),
            candidate_profile.get('revenue', 0)
        )
        
        # Component 4: Geographic overlap (10% weight)
        geographic_score = self._calculate_geographic_score(
            target_profile.get('country', ''),
            candidate_profile.get('country', '')
        )
        
        # Final weighted score
        final_score = (
            sector_score * 0.4 +
            market_cap_score * 0.3 +
            revenue_score * 0.2 +
            geographic_score * 0.1
        )
        
        explanation = f"Sector: {sector_score:.2f}, MCap: {market_cap_score:.2f}, Revenue: {revenue_score:.2f}, Geo: {geographic_score:.2f}"
        
        return SimilarityComponents(
            sector_score=sector_score,
            market_cap_score=market_cap_score,
            revenue_score=revenue_score,
            geographic_score=geographic_score,
            final_score=final_score,
            explanation=explanation
        )
    
    def _calculate_sector_score(
        self, 
        target_sector: str, 
        target_industry: str, 
        candidate_sector: str, 
        candidate_industry: str
    ) -> float:
        """Calculate sector similarity score."""
        if target_sector.lower() == candidate_sector.lower():
            return 1.0
        elif target_industry.lower() == candidate_industry.lower():
            return 0.5
        else:
            return 0.0
    
    def _calculate_market_cap_score(self, target_mcap: float, candidate_mcap: float) -> float:
        """Calculate market cap similarity score using logarithmic formula."""
        if target_mcap <= 0 or candidate_mcap <= 0:
            return 0.0
        
        try:
            ratio = target_mcap / candidate_mcap
            score = 1.0 - abs(math.log10(ratio))
            return max(0.0, min(1.0, score))  # Clamp to [0, 1]
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def _classify_peer_type(self, target_profile: Dict[str, Any], candidate_profile: Dict[str, Any]) -> str:
        """Classify peer type based on actual business similarity."""
        target_industry = target_profile.get('industry', '').lower().strip()
        candidate_industry = candidate_profile.get('industry', '').lower().strip()
        target_sector = target_profile.get('sector', '').lower().strip()
        candidate_sector = candidate_profile.get('sector', '').lower().strip()
        
        # Same industry = true business peers (best for operational metrics)
        if target_industry and candidate_industry and target_industry == candidate_industry:
            return 'industry'
        
        # Same sector but different industry = related business peers
        elif target_sector and candidate_sector and target_sector == candidate_sector:
            return 'sector'
        
        # Different sector/industry = financial peers only (valuation context)
        else:
            return 'financial'
    
    def _calculate_revenue_score(self, target_revenue: float, candidate_revenue: float) -> float:
        """Calculate revenue similarity score using logarithmic formula."""
        if target_revenue <= 0 or candidate_revenue <= 0:
            return 0.0
        
        try:
            ratio = target_revenue / candidate_revenue
            score = 1.0 - abs(math.log10(ratio))
            return max(0.0, min(1.0, score))  # Clamp to [0, 1]
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def _calculate_geographic_score(self, target_country: str, candidate_country: str) -> float:
        """Calculate geographic similarity score."""
        # Normalize country codes
        target_normalized = self._normalize_country_code(target_country)
        candidate_normalized = self._normalize_country_code(candidate_country)
        
        if target_normalized == candidate_normalized:
            return 1.0
        
        # Check if same region
        target_region = self._get_region(target_country)
        candidate_region = self._get_region(candidate_country)
        
        if target_region and target_region == candidate_region:
            return 0.5
        
        return 0.0
    
    def _normalize_country_code(self, country: str) -> str:
        """Normalize country codes (e.g., US, USA, United States -> US)."""
        country_upper = country.upper().strip()
        # Handle common US variations
        if country_upper in ['USA', 'UNITED STATES', 'UNITED STATES OF AMERICA']:
            return 'US'
        # Handle common UK variations
        if country_upper in ['UNITED KINGDOM', 'GREAT BRITAIN', 'BRITAIN']:
            return 'UK'
        return country_upper
    
    def _get_region(self, country: str) -> Optional[str]:
        """Get region for a country."""
        country_upper = country.upper()
        for region, countries in self.regions.items():
            if any(c.upper() == country_upper for c in countries):
                return region
        return None
    
    def _deduplicate_peers(self, peers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate peers, keeping the one with highest similarity score."""
        seen_symbols = {}
        for peer in peers:
            symbol = peer['symbol']
            if symbol not in seen_symbols or peer['similarityScore'] > seen_symbols[symbol]['similarityScore']:
                seen_symbols[symbol] = peer
        
        return list(seen_symbols.values())
    
    async def _add_manual_override_peers(
        self,
        manual_peers: List[str],
        target_profile: Dict[str, Any],
        existing_peers: List[Dict[str, Any]],
        max_peers: int
    ) -> List[Dict[str, Any]]:
        """Add manual override peers to the results."""
        existing_symbols = {peer['symbol'] for peer in existing_peers}
        combined_peers = existing_peers.copy()
        
        for symbol in manual_peers:
            if symbol not in existing_symbols and len(combined_peers) < max_peers:
                profile = await self._get_company_profile(symbol)
                if profile:
                    similarity = await self._calculate_similarity_score(target_profile, profile)
                    combined_peers.append({
                        'symbol': symbol,
                        'name': profile.get('companyName', ''),
                        'similarityScore': similarity.final_score,
                        'source': 'manual_override',
                        'components': {
                            'sectorScore': similarity.sector_score,
                            'marketCapScore': similarity.market_cap_score,
                            'revenueScore': similarity.revenue_score,
                            'geographicScore': similarity.geographic_score
                        },
                        'explanation': similarity.explanation
                    })
        
        return sorted(combined_peers, key=lambda x: x['similarityScore'], reverse=True)[:max_peers]


class PeerDiscoveryError(Exception):
    """Custom exception for peer discovery operations."""
    pass