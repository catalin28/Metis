# Metis - Competitive Intelligence System

## Project Overview

Metis is an automated competitive intelligence platform that generates comprehensive peer analysis reports for any public company. The system identifies peer groups, analyzes financial metrics, linguistic patterns from earnings calls, and valuation gaps to provide actionable recommendations for closing competitive positioning gaps.

## Architecture & Key Components

### Core Pipeline Flow
```
User Request (symbol) → Peer Discovery → Multi-Company Analysis → Comparative Synthesis → Report Generation
```

**Primary Orchestrators:**
- `orchestrators/competitive_intelligence_orchestrator.py` - Main coordinator for multi-company analysis
- `orchestrators/orchestrator.py` - Extended for batch processing multiple symbols in parallel

**Analysis Agents:**
- `assistants/peer_discovery_service.py` - Auto-identifies peer companies using sector + market cap similarity
- `assistants/comparative_analysis_agent.py` - Cross-company metric comparison and ranking
- `assistants/linguistic_analysis_agent.py` - Earnings transcript pattern extraction and sentiment analysis
- `assistants/valuation_gap_analyzer.py` - P/E gap decomposition (fundamental vs narrative components)

### Data Sources & Integration
- **FinancialModelingPrep (FMP) API**: Primary financial data source for company profiles, financial statements, stock prices, and earnings transcripts
- **OpenAI Assistants**: Custom assistants for comparative synthesis and linguistic analysis
- **Existing Pipelines**: Reuses `ModernEarningsAnalyzer`, `BalanceSheetPipeline`, `TradingZonesAnalyzer`, `VolumeAnalyzer`

## Development Patterns

### Sector-Agnostic Design
The system is designed to work across all sectors, not just insurance:
- Sector templates in `sector_templates/` directory define industry-specific metrics and terminology
- Peer discovery uses market cap + sector matching but works for any industry
- Financial metrics calculations are standardized (ROE, P/E, revenue growth, debt ratios)
- Linguistic analysis adapts to sector-specific terminology through configurable phrase dictionaries

### Multi-Company Processing
- Parallel processing of target company + 4-5 peers (configurable via `PARALLEL_COMPANY_LIMIT`)
- Fail-soft architecture: continues processing if individual peer analysis fails
- Batch API calls to FMP to minimize rate limit issues
- Results stored in unified JSON schema for consistent output across sectors

### Configuration Management
- `client_config.yaml` supports per-client peer group overrides
- Environment variables control processing limits, timeouts, and feature flags
- Sector templates are pluggable and can be extended for new industries

## Key Technical Decisions

### Cost & Performance Optimization
- **LLM Caching**: Prompt hashing with 90-day TTL to reduce OpenAI costs (target <$50/report)
- **Redis Caching**: 30-day TTL for FMP financial data to improve performance
- **Token Budgeting**: Per-client monthly limits with usage tracking in database
- **Processing Timeout**: 10-minute hard cap with streaming responses for long operations

### Database Schema
- `competitive_intelligence_reports` table stores full report JSON with JSONB for fast queries
- `company_metrics_history` enables time-series tracking and month-over-month comparisons
- `linguistic_patterns` table captures phrase frequency and sentiment correlations
- Tables are partitioned by month for performance at scale

### Report Structure (6 Sections)
1. **Executive Summary** - Key findings and top recommendations
2. **Competitive Dashboard** - Metric comparison table with rankings
3. **Hidden Strengths** - Where target outperforms but trades at discount
4. **Steal Their Playbook** - Successful competitor messaging strategies
5. **Valuation Forensics** - Multi-factor P/E gap decomposition with valuation bridge
6. **Actionable Roadmap** - Ranked recommendations in Do/Say/Show format

### Valuation Analysis Sophistication
The system uses advanced valuation methodologies beyond simple 3-factor models:

**Multi-Factor Valuation Models (15-20+ variables):**
- **Financial Fundamentals**: ROE, ROA, ROIC, revenue growth, margin trends, cash conversion, debt ratios
- **Quality Metrics**: Earnings quality, revenue predictability, cash flow stability, working capital efficiency
- **Risk Factors**: Beta, earnings volatility, sector cyclicality, geographic exposure, regulatory risk
- **Growth Drivers**: Market share trends, R&D intensity, capex efficiency, acquisition history
- **Market Structure**: Industry concentration, competitive moats, switching costs, network effects
- **Management Quality**: Track record, capital allocation, guidance accuracy, insider ownership

**Alternative Valuation Approaches:**
- **Comparable Company Analysis**: EV/Revenue, EV/EBITDA, P/B multiples across peer sets
- **Sum-of-the-Parts**: Business segment valuations for diversified companies
- **Dividend Discount Models**: For dividend-paying companies with stable payout policies
- **Discounted Cash Flow**: Terminal value assumptions and WACC calculations
- **Market-Based Models**: Regression against sector ETFs, factor loading analysis

**Narrative vs Fundamental Decomposition:**
- Uses machine learning models (Random Forest, XGBoost) trained on historical valuation data
- Separates explainable valuation gaps (justified by fundamentals) from perception gaps
- Accounts for market regime changes, sector rotation effects, and momentum factors

### Event Study Methodology
The system employs rigorous event study techniques beyond simple market models:

**Advanced Abnormal Return Calculation:**
- **Multi-factor models**: Fama-French 3-factor, Carhart 4-factor, or sector-specific factor models
- **Industry-adjusted returns**: Benchmark against sector ETFs and peer group performance
- **Volatility-adjusted metrics**: Risk-adjusted abnormal returns using GARCH models
- **Multiple time windows**: [-1,+1], [-1,+3], [-5,+10] day windows for robustness

**Confounding Variable Controls:**
- **Earnings surprise magnitude**: Actual vs consensus EPS, revenue, and guidance
- **Market conditions**: VIX levels, sector rotation trends, concurrent macro events
- **Company-specific factors**: Analyst revision patterns, institutional flow changes
- **Temporal controls**: Day-of-week effects, earnings season clustering, holiday impacts

**Linguistic Analysis Robustness:**
- **Natural experiments**: Compare similar earnings surprises with different linguistic patterns
- **Instrumental variables**: Use exogenous language variation (management changes, prepared vs spontaneous remarks)
- **Difference-in-differences**: Track language changes within same company over time
- **Cross-validation**: Out-of-sample testing on held-back earnings calls

## API Patterns

### Primary Endpoints
- `POST /api/competitive-intelligence/generate` - Full report generation
- `POST /api/competitive-intelligence/discover-peers` - Peer identification only
- `GET /api/competitive-intelligence/history/{symbol}` - Historical tracking data

### Error Handling
- Retry logic with exponential backoff for external API calls (FMP, OpenAI)
- Graceful degradation: partial reports if some peers fail
- Comprehensive error logging with client-friendly messages

## Development Workflow

### Testing Strategy
- Unit tests for each analysis agent with sector-agnostic test cases
- Integration tests using real company data across different sectors
- Performance tests to ensure <10 minute processing time for 5-company analysis
- Manual testing with companies from different industries (not just insurance)

### Key Commands
```bash
# Run competitive intelligence analysis with advanced valuation models
python -m orchestrators.competitive_intelligence_orchestrator --symbol AAPL --valuation-model multi-factor

# Discover peers for any company with similarity scoring
python -m assistants.peer_discovery_service --symbol TSLA --max-peers 5 --similarity-threshold 0.7

# Process batch analysis with parallel valuation modeling
python -m orchestrators.orchestrator --batch --symbols "MSFT,GOOGL,META,AAPL,AMZN" --enable-ml-valuation

# Run sector-specific valuation analysis
python -m assistants.valuation_gap_analyzer --symbol NVDA --sector technology --model-type dcf,comps,sotp

# Execute rigorous event study with controls
python -m assistants.event_study_analyzer --symbol AAPL --event-date 2025-01-31 --model fama-french --controls earnings-surprise,vix,sector-rotation
```

## Guardrails & Compliance

### Content Policy
- Banned claims list prevents investment advice or price predictions
- All quantitative claims require confidence intervals
- Mandatory disclaimers on all generated reports
- No sector-specific bias in recommendations

### Data Handling
- 24-month data retention policy
- Encryption at rest and in transit
- Client data isolation through tenant-specific configurations
- SOC2 compliance roadmap for enterprise clients

## Sector Expansion Notes

When adding new sector support:
1. Create sector template in `sector_templates/{sector}.py`
2. Define sector-specific metrics, linguistic terms, and comparison logic
3. Update peer discovery similarity scoring for sector nuances
4. Add sector-specific test cases and validation
5. Update documentation with sector-specific examples

The system architecture is designed to be sector-agnostic from the ground up, with insurance examples used only for initial development and testing.