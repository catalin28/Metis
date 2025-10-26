# Metis Python Package - Installation & Usage Guide

## Installation

### From Local Development

```bash
# Install in editable mode for development
cd /path/to/Metis
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

### From Git Repository (for external projects)

```bash
# Install directly from git
pip install git+https://github.com/yourusername/Metis.git

# Or add to requirements.txt
echo "metis @ git+https://github.com/yourusername/Metis.git" >> requirements.txt
pip install -r requirements.txt

# Or add to pyproject.toml
# dependencies = [
#     "metis @ git+https://github.com/yourusername/Metis.git",
# ]
```

### From Local Path (for development/testing)

```bash
# Install from local directory
pip install /path/to/Metis

# Or in requirements.txt
echo "metis @ file:///path/to/Metis" >> requirements.txt
```

## Environment Setup

Create a `.env` file with your API keys:

```bash
OPENAI_API_KEY=your-openai-api-key-here
FMP_API_KEY=your-fmp-api-key-here
```

## Usage Examples

### 1. Simple Function API (Recommended for Quick Tasks)

```python
import asyncio
from metis import generate_competitive_intelligence, generate_swing_trading_analysis

# Async version
async def main():
    # Generate competitive intelligence report
    report = await generate_competitive_intelligence('AAPL')
    print(f"Target: {report['target_symbol']}")
    print(f"P/E Premium: {report['valuation_context']['premium_vs_peer_percent']:.2f}%")
    
    # Generate swing trading analysis with narrative
    analysis = await generate_swing_trading_analysis('TSLA', generate_narrative=True)
    print(f"Trade Direction: {analysis['signals']['overall_bias']}")
    print(f"Conviction: {analysis['signals']['conviction_score']}/10")
    print(f"\nNarrative Preview:\n{analysis['narrative'][:500]}...")

asyncio.run(main())

# Synchronous version (blocks until complete)
from metis.api.functions import (
    generate_competitive_intelligence_sync,
    generate_swing_trading_analysis_sync
)

report = generate_competitive_intelligence_sync('MSFT')
analysis = generate_swing_trading_analysis_sync('NVDA')
```

### 2. Client API (Recommended for Multiple Requests)

```python
from metis import CompetitiveIntelligenceClient

# Initialize client with your API key
client = CompetitiveIntelligenceClient(
    api_key="your-openai-key",  # Optional if using .env
    default_model="gpt-4"
)

# Single company analysis
report = client.get_competitive_intelligence('AAPL')
analysis = client.get_swing_trading_analysis('TSLA')

# Discover peers
peers = client.discover_peers('NVDA', max_peers=5)
print(f"Peers for NVDA: {[p['symbol'] for p in peers['peers']]}")

# Batch processing multiple companies
symbols = ['AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN']
reports = client.batch_competitive_intelligence(symbols)

for symbol, report in reports.items():
    print(f"{symbol}: P/E {report['valuation_context']['current_pe']:.2f}x")

# Batch swing trading analysis
analyses = client.batch_swing_trading_analysis(symbols, generate_narrative=False)
```

### 3. Direct Module Access (Advanced Usage)

```python
from metis.swing_trading import SwingTraderAnalyzer
from metis.assistants.peer_discovery_service import PeerDiscoveryService
from metis.data_collecting.fmp_client import FMPClient
from generate_competitive_report import generate_report

# Use internal components directly
async def advanced_analysis():
    # Generate CI report with custom sections
    report = await generate_report(
        symbol='AAPL',
        peer_symbols=['MSFT', 'GOOGL', 'META'],
        sections=[1, 2, 3]  # Skip analyst consensus (2.5)
    )
    
    # Extract trading signals
    analyzer = SwingTraderAnalyzer()
    signals = analyzer.analyze_from_dict(report)
    
    # Generate custom narrative
    narrative = await analyzer.generate_trading_narrative(
        report_data=report,
        model='gpt-4',
        temperature=0.7
    )
    
    return signals, narrative
```

### 4. Integration with External Project

```python
# In your external project (e.g., Glistening)
# File: external_project/services/market_analysis.py

from metis import CompetitiveIntelligenceClient
import logging

logger = logging.getLogger(__name__)

class MarketAnalysisService:
    """Service that integrates Metis competitive intelligence."""
    
    def __init__(self):
        self.metis_client = CompetitiveIntelligenceClient()
    
    def analyze_company(self, symbol: str):
        """Get competitive intelligence and trading signals."""
        try:
            # Get comprehensive analysis
            analysis = self.metis_client.get_swing_trading_analysis(
                symbol=symbol,
                generate_narrative=True
            )
            
            # Extract key insights
            insights = {
                'symbol': symbol,
                'trade_direction': analysis['signals']['overall_bias'],
                'conviction': analysis['signals']['conviction_score'],
                'valuation_discount': analysis['competitive_intelligence']['valuation_context']['premium_vs_peer_percent'],
                'hidden_strengths': len(analysis['signals']['hidden_strengths']),
                'narrative': analysis['narrative']
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None
    
    def screen_portfolio(self, symbols: list):
        """Screen multiple companies for trading opportunities."""
        opportunities = []
        
        reports = self.metis_client.batch_competitive_intelligence(symbols)
        
        for symbol, report in reports.items():
            valuation = report['valuation_context']
            
            # Flag undervalued companies
            if valuation['premium_vs_peer_percent'] < -20:
                opportunities.append({
                    'symbol': symbol,
                    'discount': valuation['premium_vs_peer_percent'],
                    'rank': report['section_2_competitive_dashboard']['overall_target_rank']
                })
        
        return sorted(opportunities, key=lambda x: x['discount'])

# Usage in your external project
if __name__ == '__main__':
    service = MarketAnalysisService()
    
    # Analyze single company
    insights = service.analyze_company('MO')
    print(f"Trade Direction: {insights['trade_direction']}")
    print(f"Conviction: {insights['conviction']}/10")
    
    # Screen portfolio
    watchlist = ['AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN', 'TSLA', 'NVDA']
    opportunities = service.screen_portfolio(watchlist)
    
    print("\nTop Undervalued Companies:")
    for opp in opportunities[:3]:
        print(f"{opp['symbol']}: {opp['discount']:.1f}% discount, Rank #{opp['rank']}")
```

## API Reference

### Main Functions

```python
# Competitive Intelligence
generate_competitive_intelligence(symbol, peer_symbols=None, sections=None, api_key=None)
generate_competitive_intelligence_sync(...)  # Synchronous version

# Swing Trading Analysis
generate_swing_trading_analysis(symbol, peer_symbols=None, generate_narrative=True, model='gpt-4', api_key=None)
generate_swing_trading_analysis_sync(...)  # Synchronous version

# Peer Discovery
discover_peers(symbol, max_peers=5, api_key=None)
discover_peers_sync(...)  # Synchronous version
```

### Client Class

```python
client = CompetitiveIntelligenceClient(api_key=None, default_model='gpt-4', default_sections=[1,2,2.5,3])

# Methods
client.get_competitive_intelligence(symbol, peer_symbols=None, sections=None)
client.get_swing_trading_analysis(symbol, peer_symbols=None, generate_narrative=True, model=None)
client.discover_peers(symbol, max_peers=5)
client.batch_competitive_intelligence(symbols, peer_symbols=None)
client.batch_swing_trading_analysis(symbols, generate_narrative=True)

# Async versions (append _async to method name)
await client.get_competitive_intelligence_async(...)
```

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...           # OpenAI API key
FMP_API_KEY=...                 # Financial Modeling Prep API key

# Optional
METIS_DEFAULT_MODEL=gpt-4       # Default LLM model
METIS_DEFAULT_SECTIONS=1,2,2.5,3  # Default report sections
METIS_CACHE_TTL=86400           # Cache TTL in seconds
```

### Programmatic Configuration

```python
from metis import CompetitiveIntelligenceClient

client = CompetitiveIntelligenceClient(
    api_key="your-key",
    default_model="gpt-4",
    default_sections=[1, 2, 3]  # Skip analyst consensus
)
```

## Error Handling

```python
from metis import generate_competitive_intelligence_sync

try:
    report = generate_competitive_intelligence_sync('INVALID')
except ValueError as e:
    print(f"Invalid symbol: {e}")
except ConnectionError as e:
    print(f"API connection failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Performance Tips

1. **Use async for multiple companies**: Async functions are much faster for batch processing
2. **Cache results**: Reports are expensive - cache them for 24 hours
3. **Skip narrative generation**: Set `generate_narrative=False` for 50% speedup
4. **Reuse client**: Initialize `CompetitiveIntelligenceClient` once and reuse it

## Testing

```python
# Run tests
pytest tests/

# Test installation
python -c "from metis import CompetitiveIntelligenceClient; print('✓ Metis installed successfully')"
```

## Support

For issues or questions:
- GitHub Issues: https://github.com/yourusername/Metis/issues
- Documentation: https://metis.readthedocs.io
- Email: dev@metis.ai
