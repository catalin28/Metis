# Metis - Competitive Intelligence Platform

An automated competitive intelligence system that generates comprehensive peer analysis reports for any public company, identifying valuation gaps and providing actionable recommendations.

## Features

- **Automated Peer Discovery**: Identifies comparable companies using sector and market cap similarity
- **Multi-Company Analysis**: Parallel processing of target company + 4-5 peers
- **Advanced Valuation Models**: 15-20+ factor models beyond simple P/E ratios
- **Linguistic Analysis**: Extracts patterns from earnings transcripts that correlate with valuation premiums
- **Rigorous Event Studies**: Controls for earnings surprises and confounding variables
- **Actionable Intelligence**: Ranked recommendations in Do/Say/Show format

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/metis/metis.git
cd metis

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

### Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit with your API keys
vi .env
```

Required environment variables:
- `FMP_API_KEY`: FinancialModelingPrep API key
- `OPENAI_API_KEY`: OpenAI API key
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string (optional, for caching)

### Database Setup

```bash
# Run migrations
alembic upgrade head

# Seed with test data (optional)
python -m metis.scripts.seed_data
```

### Run Analysis

```bash
# Generate competitive intelligence report
metis analyze --symbol AAPL

# Discover peers only
metis discover-peers --symbol TSLA --max-peers 5

# Batch analysis
metis analyze --batch --symbols "MSFT,GOOGL,META"
```

## Architecture

```
metis/
├── src/metis/
│   ├── orchestrators/          # Main workflow coordinators
│   ├── assistants/            # Analysis agents
│   ├── data_collecting/       # Data retrieval services
│   ├── reports/              # Report generation
│   ├── api/                  # FastAPI routes
│   ├── models/               # Database models
│   ├── utils/                # Utilities and helpers
│   └── cli/                  # Command line interface
├── tests/                    # Test suite
├── migrations/               # Database migrations
├── docs/                     # Documentation
└── config/                   # Configuration files
```

## Development

### Setup Development Environment

```bash
# Install with development dependencies
pip install -e ".[dev,test]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run with coverage
pytest --cov=metis

# Format code
black src/ tests/
isort src/ tests/

# Type checking
mypy src/
```

### Running the API Server

```bash
# Development server
uvicorn metis.api.main:app --reload --port 8000

# Production server
uvicorn metis.api.main:app --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Run all tests
pytest

# Run only unit tests
pytest -m unit

# Run integration tests
pytest -m integration

# Run with coverage report
pytest --cov=metis --cov-report=html
```

## API Usage

### Generate Competitive Intelligence Report

```bash
curl -X POST "http://localhost:8000/api/competitive-intelligence/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "max_peers": 5,
    "include_sections": ["executive_summary", "competitive_dashboard", "valuation_forensics"]
  }'
```

### Discover Peers

```bash
curl -X POST "http://localhost:8000/api/competitive-intelligence/discover-peers" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "TSLA",
    "sector": "automotive",
    "max_peers": 5
  }'
```

## Configuration

### Client Configuration

Edit `config/client_config.yaml` to customize peer groups and analysis parameters:

```yaml
clients:
  default:
    competitive_intelligence:
      enabled: true
      max_peers: 5
      peer_discovery_mode: auto
      custom_peer_groups:
        AAPL: ["MSFT", "GOOGL", "META", "AMZN"]
```

### Sector Templates

Add new sector-specific analysis in `src/metis/sector_templates/`:

```python
# src/metis/sector_templates/technology.py
TECHNOLOGY_TEMPLATE = {
    "metrics": ["revenue_growth", "gross_margin", "r_and_d_ratio"],
    "linguistic_terms": ["innovation", "AI", "cloud", "platform"],
    "valuation_multiples": ["ev_revenue", "peg_ratio"]
}
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Use Black for code formatting
- Follow PEP 8 guidelines
- Add type hints to all functions
- Write docstrings for all public methods
- Maintain test coverage above 85%

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- Documentation: [https://metis.readthedocs.io](https://metis.readthedocs.io)
- Issues: [GitHub Issues](https://github.com/metis/metis/issues)
- Discussions: [GitHub Discussions](https://github.com/metis/metis/discussions)

## Roadmap

- [ ] Real-time competitive monitoring
- [ ] Predictive analytics for competitive moves
- [ ] Enhanced sector-specific templates
- [ ] Integration with additional data sources
- [ ] Advanced visualization dashboards