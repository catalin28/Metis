"""
Analyst Grades Data Collector

Fetches analyst rating actions from FMP API and calculates consensus metrics
for competitive intelligence reports.

Data Source: FMP /stable/grades?symbol={SYMBOL}
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from collections import defaultdict

import requests

from metis.core.config import settings
from metis.models.report_schema_v2 import (
    AnalystAction,
    AnalystConsensusMetric
)

logger = logging.getLogger(__name__)


class AnalystGradesCollector:
    """
    Collects analyst rating actions and calculates consensus metrics.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize collector with FMP API key.
        
        Args:
            api_key: FMP API key (defaults to settings.fmp_api_key)
        """
        self.api_key = api_key or settings.fmp_api_key
        self.base_url = "https://financialmodelingprep.com/stable"
        
    def fetch_analyst_grades(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch analyst rating actions from FMP API.
        
        Args:
            symbol: Stock ticker symbol
            limit: Maximum number of records to fetch (default 100)
            
        Returns:
            List of analyst action dicts
            
        Raises:
            requests.RequestException: If API call fails
        """
        url = f"{self.base_url}/grades"
        params = {
            "symbol": symbol.upper(),
            "apikey": self.api_key
        }
        
        try:
            logger.info(f"Fetching analyst grades for {symbol}")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not isinstance(data, list):
                logger.warning(f"Unexpected response format for {symbol}: {type(data)}")
                return []
            
            logger.info(f"Fetched {len(data)} analyst actions for {symbol}")
            return data[:limit]  # Limit to most recent N records
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch analyst grades for {symbol}: {e}")
            raise
    
    def calculate_consensus_metrics(
        self,
        symbol: str,
        company_name: str,
        raw_grades: List[Dict[str, Any]],
        days_90_ago: Optional[datetime] = None,
        days_365_ago: Optional[datetime] = None
    ) -> AnalystConsensusMetric:
        """
        Calculate consensus metrics from raw analyst grades data.
        
        Args:
            symbol: Stock ticker symbol
            company_name: Full company name
            raw_grades: List of analyst action dicts from FMP API
            days_90_ago: Cutoff date for 90-day metrics (defaults to today - 90 days)
            days_365_ago: Cutoff date for 12-month metrics (defaults to today - 365 days)
            
        Returns:
            AnalystConsensusMetric with calculated metrics
        """
        # Set default date ranges
        if days_90_ago is None:
            days_90_ago = datetime.now() - timedelta(days=90)
        if days_365_ago is None:
            days_365_ago = datetime.now() - timedelta(days=365)
        
        # Initialize counters
        upgrades_90d = 0
        downgrades_90d = 0
        maintains_90d = 0
        initiates_90d = 0
        recent_actions_90d = 0
        
        coverage_firms = set()
        latest_action = None
        latest_date = None
        
        # Process each analyst action
        for grade in raw_grades:
            try:
                action_date = datetime.strptime(grade["date"], "%Y-%m-%d")
                action_type = grade["action"].lower()
                grading_company = grade["gradingCompany"]
                
                # Track latest action
                if latest_date is None or action_date > latest_date:
                    latest_date = action_date
                    latest_action = AnalystAction(
                        symbol=symbol,
                        date=grade["date"],
                        grading_company=grading_company,
                        previous_grade=grade.get("previousGrade"),
                        new_grade=grade["newGrade"],
                        action=action_type
                    )
                
                # Count 90-day actions
                if action_date >= days_90_ago:
                    recent_actions_90d += 1
                    
                    if action_type == "upgrade":
                        upgrades_90d += 1
                    elif action_type == "downgrade":
                        downgrades_90d += 1
                    elif action_type == "maintain":
                        maintains_90d += 1
                    elif action_type == "initiate":
                        initiates_90d += 1
                
                # Track coverage breadth (12 months)
                if action_date >= days_365_ago:
                    coverage_firms.add(grading_company)
                    
            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping invalid grade record for {symbol}: {e}")
                continue
        
        # Calculate net sentiment
        net_sentiment = self._calculate_sentiment(upgrades_90d, downgrades_90d, maintains_90d)
        
        return AnalystConsensusMetric(
            symbol=symbol,
            company_name=company_name,
            recent_actions_90d=recent_actions_90d,
            upgrades_90d=upgrades_90d,
            downgrades_90d=downgrades_90d,
            maintains_90d=maintains_90d,
            initiates_90d=initiates_90d,
            net_sentiment=net_sentiment,
            coverage_breadth=len(coverage_firms),
            latest_action=latest_action,
            current_pe=1.0  # Default value, will be updated if company_data provided
        )
    
    def _calculate_sentiment(self, upgrades: int, downgrades: int, maintains: int) -> str:
        """
        Determine net sentiment from action counts.
        
        Rules:
        - Bullish: Upgrades > Downgrades + Maintains OR (Upgrades >= 3 and Downgrades == 0)
        - Bearish: Downgrades > Upgrades + Maintains OR (Downgrades >= 3 and Upgrades == 0)
        - Neutral: All other cases (balanced, low activity, or maintains dominate)
        
        Args:
            upgrades: Number of upgrades
            downgrades: Number of downgrades
            maintains: Number of maintains
            
        Returns:
            Sentiment string: "Bullish", "Bearish", or "Neutral"
        """
        total_actions = upgrades + downgrades + maintains
        
        # No activity
        if total_actions == 0:
            return "Neutral"
        
        # Strong bullish signal
        if upgrades > downgrades + maintains or (upgrades >= 3 and downgrades == 0):
            return "Bullish"
        
        # Strong bearish signal
        if downgrades > upgrades + maintains or (downgrades >= 3 and upgrades == 0):
            return "Bearish"
        
        # Default to neutral (balanced or maintains dominate)
        return "Neutral"
    
    def collect_multi_company_consensus(
        self,
        symbols: List[str],
        company_names: Dict[str, str]
    ) -> List[AnalystConsensusMetric]:
        """
        Collect analyst consensus metrics for multiple companies.
        
        Args:
            symbols: List of stock ticker symbols
            company_names: Dict mapping symbols to company names
            
        Returns:
            List of AnalystConsensusMetric objects
        """
        results = []
        
        for symbol in symbols:
            try:
                # Fetch raw grades
                raw_grades = self.fetch_analyst_grades(symbol)
                
                # Calculate metrics
                company_name = company_names.get(symbol, symbol)
                metrics = self.calculate_consensus_metrics(
                    symbol=symbol,
                    company_name=company_name,
                    raw_grades=raw_grades
                )
                
                results.append(metrics)
                
            except Exception as e:
                logger.error(f"Failed to collect consensus for {symbol}: {e}")
                # Add empty metrics for failed collection
                results.append(AnalystConsensusMetric(
                    symbol=symbol,
                    company_name=company_names.get(symbol, symbol),
                    recent_actions_90d=0,
                    upgrades_90d=0,
                    downgrades_90d=0,
                    maintains_90d=0,
                    initiates_90d=0,
                    net_sentiment="Neutral",
                    coverage_breadth=0,
                    latest_action=None
                ))
        
        return results


# Convenience function for quick data collection
def collect_analyst_consensus(
    target_symbol: str,
    peer_symbols: List[str],
    company_names: Dict[str, str],
    company_data: Optional[Dict[str, Dict[str, Any]]] = None,
    api_key: Optional[str] = None
) -> tuple[AnalystConsensusMetric, List[AnalystConsensusMetric]]:
    """
    Collect analyst consensus for target and peers.
    
    Args:
        target_symbol: Target company symbol
        peer_symbols: List of peer company symbols
        company_names: Dict mapping all symbols to company names
        company_data: Optional dict with company data including P/E ratios
        api_key: Optional FMP API key
        
    Returns:
        Tuple of (target_metrics, peer_metrics_list)
    """
    collector = AnalystGradesCollector(api_key=api_key)
    
    # Collect all companies
    all_symbols = [target_symbol] + peer_symbols
    all_metrics = collector.collect_multi_company_consensus(all_symbols, company_names)
    
    # Add P/E ratios if company_data provided
    if company_data:
        for metric in all_metrics:
            symbol = metric.symbol
            if symbol in company_data:
                pe_ratio = company_data[symbol].get('pe_ratio', 0)
                # Update the metric with P/E (Pydantic models are frozen, need to use object.__setattr__)
                object.__setattr__(metric, 'current_pe', pe_ratio if pe_ratio and pe_ratio > 0 else 1.0)
    
    # Split target and peers
    target_metrics = all_metrics[0]
    peer_metrics = all_metrics[1:]
    
    return target_metrics, peer_metrics
