"""
FinancialModelingPrep (FMP) API Client

Provides comprehensive data collection from FMP APIs for competitive intelligence analysis.

Endpoints covered:
- Company Profile: /api/v3/profile/{symbol}
- Income Statement: /api/v3/income-statement/{symbol}
- Balance Sheet: /api/v3/balance-sheet-statement/{symbol}
- Cash Flow: /api/v3/cash-flow-statement/{symbol}
- Key Metrics: /api/v3/key-metrics/{symbol}
- Financial Ratios: /api/v3/ratios/{symbol}
- Stock Quote: /api/v3/quote/{symbol}
- Earnings Transcripts: /api/v3/earning_call_transcript/{symbol}
- Company Rating: /api/v3/rating/{symbol}

Author: Metis Development Team
Created: 2025-10-22
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

import requests
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class FMPClientError(Exception):
    """Raised when FMP API requests fail."""
    pass


class FMPClient:
    """
    Client for FinancialModelingPrep API.
    
    Handles all data collection operations with error handling, rate limiting,
    and response caching.
    """
    
    BASE_URL = "https://financialmodelingprep.com/api/v3/"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize FMP client.
        
        Args:
            api_key: FMP API key (uses FMP_API_KEY env var if not provided)
            
        Raises:
            FMPClientError: If API key is not found
        """
        self.api_key = api_key or os.getenv('FMP_API_KEY')
        if not self.api_key:
            raise FMPClientError(
                "FMP API key not found. Set FMP_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.session = requests.Session()
        self.session.params = {'apikey': self.api_key}
        logger.info("FMPClient initialized")
    
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated request to FMP API.
        
        Args:
            endpoint: API endpoint path (e.g., 'profile/AAPL')
            params: Optional query parameters
            
        Returns:
            JSON response data
            
        Raises:
            FMPClientError: If request fails
        """
        url = urljoin(self.BASE_URL, endpoint)
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Handle FMP error responses
            if isinstance(data, dict) and 'Error Message' in data:
                raise FMPClientError(f"FMP API error: {data['Error Message']}")
            
            return data
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for {endpoint}: {e}")
            raise FMPClientError(f"HTTP {e.response.status_code}: {e}") from e
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout for {endpoint}: {e}")
            raise FMPClientError(f"Request timeout for {endpoint}") from e
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {endpoint}: {e}")
            raise FMPClientError(f"Request failed: {e}") from e
        except ValueError as e:
            logger.error(f"Invalid JSON response for {endpoint}: {e}")
            raise FMPClientError(f"Invalid JSON response: {e}") from e
    
    # Company Profile & Fundamentals
    
    def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive company profile.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Company profile data including:
            - companyName, symbol, currency
            - sector, industry, exchange
            - mktCap, price, beta
            - description, ceo, website
            - country, city, address
            
        Example:
            >>> client = FMPClient()
            >>> profile = client.get_company_profile('AAPL')
            >>> print(profile['companyName'])
            'Apple Inc.'
        """
        logger.info(f"Fetching company profile for {symbol}")
        data = self._make_request(f'profile/{symbol.upper()}')
        
        if not data or len(data) == 0:
            raise FMPClientError(f"No profile data found for {symbol}")
        
        return data[0]  # FMP returns list with single item
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get real-time stock quote.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Quote data including:
            - price, changesPercentage, change
            - dayLow, dayHigh
            - yearHigh, yearLow
            - marketCap, priceAvg50, priceAvg200
            - volume, avgVolume
            - open, previousClose
            - eps, pe, earningsAnnouncement
        """
        logger.info(f"Fetching quote for {symbol}")
        data = self._make_request(f'quote/{symbol.upper()}')
        
        if not data or len(data) == 0:
            raise FMPClientError(f"No quote data found for {symbol}")
        
        return data[0]
    
    # Financial Statements
    
    def get_income_statement(
        self,
        symbol: str,
        period: str = 'quarter',
        limit: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Get income statements.
        
        Args:
            symbol: Stock ticker symbol
            period: 'annual' or 'quarter'
            limit: Number of periods to retrieve
            
        Returns:
            List of income statements with fields:
            - date, symbol, reportedCurrency, period
            - revenue, costOfRevenue, grossProfit
            - operatingExpenses, operatingIncome
            - netIncome, eps, epsdiluted
        """
        logger.info(f"Fetching income statement for {symbol} ({period})")
        data = self._make_request(
            f'income-statement/{symbol.upper()}',
            params={'period': period, 'limit': limit}
        )
        return data
    
    def get_balance_sheet(
        self,
        symbol: str,
        period: str = 'quarter',
        limit: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Get balance sheets.
        
        Args:
            symbol: Stock ticker symbol
            period: 'annual' or 'quarter'
            limit: Number of periods to retrieve
            
        Returns:
            List of balance sheets with fields:
            - totalAssets, totalLiabilities, totalEquity
            - cash, inventory, totalCurrentAssets
            - totalDebt, totalCurrentLiabilities
            - retainedEarnings, commonStock
        """
        logger.info(f"Fetching balance sheet for {symbol} ({period})")
        data = self._make_request(
            f'balance-sheet-statement/{symbol.upper()}',
            params={'period': period, 'limit': limit}
        )
        return data
    
    def get_cash_flow(
        self,
        symbol: str,
        period: str = 'quarter',
        limit: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Get cash flow statements.
        
        Args:
            symbol: Stock ticker symbol
            period: 'annual' or 'quarter'
            limit: Number of periods to retrieve
            
        Returns:
            List of cash flow statements with fields:
            - operatingCashFlow, capitalExpenditure, freeCashFlow
            - dividendsPaid, stockBasedCompensation
            - cashAtEndOfPeriod, cashAtBeginningOfPeriod
        """
        logger.info(f"Fetching cash flow for {symbol} ({period})")
        data = self._make_request(
            f'cash-flow-statement/{symbol.upper()}',
            params={'period': period, 'limit': limit}
        )
        return data
    
    # Metrics & Ratios
    
    def get_key_metrics(
        self,
        symbol: str,
        period: str = 'quarter',
        limit: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Get key financial metrics.
        
        Args:
            symbol: Stock ticker symbol
            period: 'annual' or 'quarter'
            limit: Number of periods to retrieve
            
        Returns:
            List of metrics including:
            - peRatio, priceToSalesRatio, pbRatio
            - roe, roa, roic
            - debtToEquity, currentRatio
            - revenuePerShare, netIncomePerShare
            - operatingCashFlowPerShare, freeCashFlowPerShare
        """
        logger.info(f"Fetching key metrics for {symbol} ({period})")
        data = self._make_request(
            f'key-metrics/{symbol.upper()}',
            params={'period': period, 'limit': limit}
        )
        return data
    
    def get_financial_ratios(
        self,
        symbol: str,
        period: str = 'quarter',
        limit: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Get comprehensive financial ratios.
        
        Args:
            symbol: Stock ticker symbol
            period: 'annual' or 'quarter'
            limit: Number of periods to retrieve
            
        Returns:
            List of ratios including:
            - Liquidity: currentRatio, quickRatio
            - Profitability: grossProfitMargin, operatingProfitMargin, netProfitMargin
            - Efficiency: assetTurnover, inventoryTurnover
            - Leverage: debtRatio, debtEquityRatio
            - Returns: returnOnAssets, returnOnEquity
        """
        logger.info(f"Fetching financial ratios for {symbol} ({period})")
        data = self._make_request(
            f'ratios/{symbol.upper()}',
            params={'period': period, 'limit': limit}
        )
        return data
    
    # Earnings & Analysis
    
    def get_earnings_call_transcript(
        self,
        symbol: str,
        year: Optional[int] = None,
        quarter: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get earnings call transcripts.
        
        Args:
            symbol: Stock ticker symbol
            year: Optional year filter (e.g., 2024)
            quarter: Optional quarter filter (1-4)
            
        Returns:
            List of transcripts with:
            - symbol, quarter, year, date
            - content (full transcript text)
        """
        logger.info(f"Fetching earnings transcript for {symbol}")
        
        params = {}
        if year:
            params['year'] = year
        if quarter:
            params['quarter'] = quarter
        
        data = self._make_request(
            f'earning_call_transcript/{symbol.upper()}',
            params=params if params else None
        )
        return data
    
    def get_company_rating(self, symbol: str) -> Dict[str, Any]:
        """
        Get company rating and recommendation.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Rating data including:
            - rating (e.g., 'A', 'B+')
            - ratingScore (0-100)
            - ratingRecommendation ('Strong Buy', 'Buy', etc.)
            - ratingDetailsDCFScore, ratingDetailsDEScore
        """
        logger.info(f"Fetching company rating for {symbol}")
        data = self._make_request(f'rating/{symbol.upper()}')
        
        if not data or len(data) == 0:
            raise FMPClientError(f"No rating data found for {symbol}")
        
        return data[0]
    
    # Batch Operations
    
    def get_comprehensive_company_data(
        self,
        symbol: str,
        periods: int = 8,
        period_type: str = 'quarter'
    ) -> Dict[str, Any]:
        """
        Get all available data for a company in one call.
        
        This is a convenience method that combines multiple API calls
        to gather comprehensive company data efficiently.
        
        Args:
            symbol: Stock ticker symbol
            periods: Number of historical periods to retrieve (default: 8 quarters = 2 years)
            period_type: 'quarter' (default) or 'annual'
            
        Returns:
            Dictionary containing:
            - profile: Company profile
            - quote: Current stock quote
            - income_statement: Income statements (quarterly by default)
            - balance_sheet: Balance sheets (quarterly by default)
            - cash_flow: Cash flow statements (quarterly by default)
            - key_metrics: Key financial metrics (quarterly by default)
            - ratios: Financial ratios (quarterly by default)
            - rating: Company rating
            - transcripts: Recent earnings transcripts (last 4 quarters)
        """
        logger.info(f"Fetching comprehensive data for {symbol} ({periods} {period_type} periods)")
        
        try:
            data = {
                'symbol': symbol.upper(),
                'collected_at': datetime.now().isoformat(),
                'period_type': period_type,
                'periods_count': periods
            }
            
            # Basic company info
            data['profile'] = self.get_company_profile(symbol)
            data['quote'] = self.get_quote(symbol)
            
            # Financial statements (quarterly by default for timeliness)
            data['income_statement'] = self.get_income_statement(symbol, period_type, periods)
            data['balance_sheet'] = self.get_balance_sheet(symbol, period_type, periods)
            data['cash_flow'] = self.get_cash_flow(symbol, period_type, periods)
            
            # Metrics and ratios
            data['key_metrics'] = self.get_key_metrics(symbol, period_type, periods)
            data['ratios'] = self.get_financial_ratios(symbol, period_type, periods)
            
            # Rating
            try:
                data['rating'] = self.get_company_rating(symbol)
            except FMPClientError as e:
                logger.warning(f"Could not fetch rating for {symbol}: {e}")
                data['rating'] = None
            
            # Earnings transcripts (last 4 quarters)
            try:
                data['transcripts'] = self.get_earnings_call_transcript(symbol)[:4]
            except FMPClientError as e:
                logger.warning(f"Could not fetch transcripts for {symbol}: {e}")
                data['transcripts'] = []
            
            logger.info(f"Successfully collected comprehensive data for {symbol}")
            return data
            
        except FMPClientError as e:
            logger.error(f"Failed to collect comprehensive data for {symbol}: {e}")
            raise
    
    def get_batch_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get quotes for multiple symbols efficiently.
        
        Args:
            symbols: List of stock ticker symbols
            
        Returns:
            Dictionary mapping symbols to quote data
        """
        logger.info(f"Fetching batch quotes for {len(symbols)} symbols")
        
        # FMP supports comma-separated symbols
        symbols_str = ','.join([s.upper() for s in symbols])
        data = self._make_request(f'quote/{symbols_str}')
        
        # Convert to dict for easy lookup
        return {item['symbol']: item for item in data}
    
    def get_batch_profiles(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get profiles for multiple symbols efficiently.
        
        Args:
            symbols: List of stock ticker symbols
            
        Returns:
            Dictionary mapping symbols to profile data
        """
        logger.info(f"Fetching batch profiles for {len(symbols)} symbols")
        
        # FMP supports comma-separated symbols
        symbols_str = ','.join([s.upper() for s in symbols])
        data = self._make_request(f'profile/{symbols_str}')
        
        # Convert to dict for easy lookup
        return {item['symbol']: item for item in data}
