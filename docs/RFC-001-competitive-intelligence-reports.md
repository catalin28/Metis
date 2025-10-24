# RFC-001: Competitive Intelligence Reports System

**Status**: Draft  
**Author**: Development Team  
**Created**: 2025-10-21  
**Updated**: 2025-10-21  
**Related Issues**: N/A

---

## Problem Statement

**What problem does this solve?**
- Public companies (especially mid-cap $2B-$20B) lack competitive intelligence resources that mega-cap peers ($100B+) enjoy through armies of IR analysts and expensive consulting firms
- Companies don't understand WHY their P/E multiples lag competitors despite superior operational metrics (combined ratio, ROE, reserve quality)
- Investor relations teams struggle to identify which competitor messaging strategies drive valuation premiums
- No automated system exists to track competitive narratives, linguistic patterns, and their correlation to valuation multiples
- CFOs/IR teams need actionable intelligence: "Progressive gets 20x P/E, we get 12x with better metrics - why and how do we fix it?"

**Current State:**
- Glistening generates single-company analysis (earnings, trading zones, volume) in 91 seconds
- No comparative analysis across peer groups
- No competitive messaging/sentiment tracking
- No valuation gap identification with actionable recommendations
- No linguistic analysis of what language patterns drive higher multiples

**Desired State:**
- Automated monthly "Competitive Intelligence Dashboard" comparing company vs. top 4-5 peers
- Sentiment analysis showing which competitor narratives resonate (e.g., "Progressive mentions 'technology' 3.2x more")
- Valuation gap forensics with specific actionable fixes ranked by impact
- "Steal Their Playbook" reports showing what competitors said that worked
- Track competitor strategy shifts in real-time with alerts

**Why is this important now?**
- B2B monetization opportunity: Companies will pay $15K-$25K/month for competitive intelligence (vs. $5K-10K for single-company analysis)
- Differentiates Glistening from competitors who only do single-company analysis
- Addresses the #1 question CFOs ask: "Why does [competitor] trade at higher multiple?"
- Creates sticky enterprise relationships (monthly subscriptions vs. one-time reports)

**What happens if we don't do this?**
- Miss significant B2B revenue opportunity (enterprise market is 10x larger than retail)
- Competitors will build this feature first
- Limited to commodity single-company reports
- Can't justify premium pricing ($15K-25K/month)

---

## Proposed Solution

**High-level approach:**
Build a multi-company comparative analysis pipeline that automatically:
1. Identifies peer group for target company (same sector, similar market cap)
2. Generates comprehensive analysis for target + top 4-5 peers (earnings, financials, technical)
3. Performs differential analysis: metric comparison, sentiment comparison, linguistic patterns, valuation gap identification
4. Creates actionable recommendations: messaging frameworks, timing strategies, narrative improvements
5. Tracks changes over time: month-over-month competitive positioning shifts

**Key architectural decisions:**
- Extend existing `ModernEarningsAnalyzer` with `CompetitiveIntelligenceOrchestrator`
- Reuse existing pipelines (earnings, balance sheet, cash flow, trading zones, volume) but run in parallel for peer group
- Add new `ComparativeAnalysisAgent` that synthesizes cross-company insights
- Add new `LinguisticAnalysisAgent` that extracts language patterns correlated with valuation premiums
- Store comparative results in new database tables for time-series tracking

**User/Developer Experience:**
- **API endpoint**: `POST /api/competitive-intelligence/generate`
- **Input**: `{"symbol": "WRB", "include_peers": true}` (peer auto-discovery) OR `{"symbol": "WRB", "peer_symbols": ["PGR", "CB", "TRV", "HIG"]}`
- **Output**: Comprehensive competitive intelligence report with 6 sections (see Design Details)
- **Processing time**: 300-400 seconds (5-6 companies × 60-80 seconds each + comparative analysis)
- **WordPress publishing**: Optional auto-publish to private blog posts for enterprise clients

---

## Design Details

### Architecture Changes

**Components Added/Modified:**

**New Components:**
- `orchestrators/competitive_intelligence_orchestrator.py` - Coordinates multi-company analysis
- `assistants/comparative_analysis_agent.py` - Synthesizes cross-company insights using LLM
- `assistants/linguistic_analysis_agent.py` - Extracts language patterns from earnings transcripts
- `assistants/valuation_gap_analyzer.py` - Identifies why P/E multiples differ despite similar metrics
- `assistants/peer_discovery_service.py` - Auto-identifies peer group (sector + market cap similarity)
- `routes/competitive_intelligence_routes.py` - New API endpoints
- `reports/competitive_intelligence_report_generator.py` - Formats output for WordPress/PDF

**Modified Components:**
- `orchestrators/orchestrator.py` - Add batch mode for processing multiple symbols in parallel
- `assistants/llm_pipelines/base_llm_pipeline.py` - Add `comparative_context` parameter
- `data_collecting/financial_data_retriever.py` - Add batch retrieval methods

**Data Flow:**
```
User Request (symbol="WRB")
    ↓
PeerDiscoveryService.identify_peers("WRB", sector="Insurance")
    → Returns: ["PGR", "CB", "TRV", "HIG"]
    ↓
CompetitiveIntelligenceOrchestrator.analyze_peer_group(["WRB", "PGR", "CB", "TRV", "HIG"])
    ↓
[Parallel Processing for each company]
    ├─→ ModernEarningsAnalyzer.analyze("WRB") → Earnings insights
    ├─→ BalanceSheetPipeline.process("WRB") → Financial metrics
    ├─→ TradingZonesAnalyzer.analyze("WRB") → Technical positioning
    └─→ VolumeAnalyzer.analyze("WRB") → Institutional flow
    ↓
[Store individual results in database]
    ↓
ComparativeAnalysisAgent.synthesize(all_results)
    ├─→ Metric comparison (ROE, combined ratio, reserve quality)
    ├─→ Sentiment comparison (management confidence, tone)
    ├─→ Technical comparison (valuation multiples, institutional positioning)
    └─→ Gap identification (why WRB trades at 12x vs PGR at 20x)
    ↓
LinguisticAnalysisAgent.analyze_transcripts(all_earnings_calls)
    ├─→ Extract key phrases ("technology", "data-driven", "AI-powered")
    ├─→ Frequency analysis (PGR mentions "technology" 34x, WRB mentions 8x)
    ├─→ Correlation analysis (phrase frequency vs P/E multiple)
    └─→ Generate recommended messaging adjustments
    ↓
ValuationGapAnalyzer.identify_drivers(target="WRB", peers=["PGR", "CB", "TRV", "HIG"])
    ├─→ Fundamental comparison (better metrics but lower multiple?)
    ├─→ Narrative gap identification (story clarity issues)
    ├─→ Perception vs reality delta (underappreciated strengths)
    └─→ Actionable fix ranking (18 recommendations sorted by impact)
    ↓
CompetitiveIntelligenceReportGenerator.format_output()
    ├─→ Executive summary (2 pages)
    ├─→ Competitive dashboard (comparison tables)
    ├─→ "Steal Their Playbook" section (what competitors said that worked)
    ├─→ Valuation gap forensics (why multiples differ)
    ├─→ Actionable recommendations (ranked by impact)
    └─→ Month-over-month tracking (if historical data exists)
    ↓
[Optional] Publish to WordPress (private post for enterprise client)
    ↓
Return JSON response + blog URL
```

**Integration Points:**
- **Existing pipelines**: Reuses `ModernEarningsAnalyzer`, `BalanceSheetPipeline`, `CashFlowPipeline`, `IncomeStatementPipeline`, `TradingZonesAnalyzer`, `VolumeAnalyzer`
- **New OpenAI assistant**: `CompetitiveIntelligenceAssistant` with custom prompt for cross-company synthesis
- **Financial data API**: Batch calls to FinancialModelingPrep for peer group data
- **Database**: New tables for storing comparative results over time
- **WordPress**: Publishes to client-specific private posts (password protected)

### Report Output Structure

**Section 1: Executive Summary**
- Target company overview (1 paragraph)
- Key finding: "WRB has best combined ratio (88.3) and 2nd-best ROE (18.4%) yet trades at lowest multiple (12.1x)"
- Root cause: 3 perception gaps identified
- Top 3 actionable recommendations

**Section 2: Competitive Dashboard (Comparison Table)**
```
| Metric | WRB | PGR | CB | TRV | HIG | WRB Rank | Market Perception |
|--------|-----|-----|----|-----|-----|----------|-------------------|
| P/E Ratio | 12.1x | 20.5x | 15.2x | 13.8x | 14.1x | #5 (worst) | Undervalued |
| ROE | 18.4% | 29.1% | 12.8% | 13.2% | 11.9% | #2 | Underappreciated |
| Combined Ratio | 88.3 | 90.2 | 89.1 | 92.8 | 91.4 | #1 (best) | Hidden strength |
| Reserve Development | +2.3% | -1.2% | +0.8% | +1.1% | -0.4% | #1 (best) | Not communicated |
| Management Sentiment | 78% | 85% | 72% | 69% | 64% | #2 | Adequate |
| Analyst Confusion | High | Low | Medium | Low | Medium | #5 (worst) | Root cause |
```

**Section 3: Hidden Strengths (That Wall Street Ignores)**
- Reserve quality advantage (40% more consistent than PGR)
- Capital efficiency edge (18.4% ROE with less leverage)
- Underwriting superiority (88.3 combined ratio beats all peers)
- Why analysts miss this (complexity, lack of clear communication)

**Section 4: "Steal Their Playbook" - What Competitors Said That Worked**
- Progressive's "tech moat" narrative (appears in 47% of sell-side reports)
- Chubb's "global diversification" messaging (mentioned 3.2x more than WRB)
- Travelers' "stable and boring" positioning (reduces perceived volatility)
- Hartford's turnaround story (8.2x → 14.1x P/E in 24 months)
- Linguistic analysis: PGR uses "technology" 34x in earnings calls, WRB uses 8x
- Exact phrases that correlate with higher multiples

**Section 5: Valuation Gap Forensics**
- Why Progressive trades at 20x (simplified "data company" story)
- Why Chubb trades at 15.2x (global reach = safety perception)
- Why WRB trades at 12.1x (specialty line complexity + analyst confusion)
- Perception vs reality delta (operational winner, narrative loser)
- 18 specific recommendations ranked by valuation impact

**Section 6: Actionable Fix Roadmap**
- Problem #1: "Why does Progressive trade at 20x when we have better metrics?"
  - Solution: Monthly competitive valuation reports
  - Specific talking points to elevate tech sophistication story
- Problem #2: "Analysts don't understand our specialty lines"
  - Solution: Communication frameworks from Chubb (analogies 2.1x more)
  - Side-by-side comparison templates
- Problem #3: "When should we execute buybacks?"
  - Solution: Track peer buyback timing vs technical zones
  - Quarterly recommendations based on competitive sweet spots
- Problem #4: "How to close P/E gap from 12x to 14.5x?"
  - Solution: 18-action roadmap (Hartford's playbook)
  - Monthly progress tracking: messaging → sentiment → multiple expansion

### Configuration Changes

**Environment Variables:**
```bash
# Competitive Intelligence Configuration
COMPETITIVE_INTEL_PROJECT_ID=<OpenAI project for competitive analysis>
COMPETITIVE_INTEL_ASSISTANT_ID=<Assistant ID for comparative synthesis>
LINGUISTIC_ANALYSIS_ASSISTANT_ID=<Assistant ID for language pattern extraction>

# Peer Discovery Settings
PEER_DISCOVERY_API_KEY=<FMP API key for peer data>
MAX_PEERS_PER_ANALYSIS=5  # Default: analyze target + 4 peers
MIN_MARKET_CAP_RATIO=0.3  # Peers must be 30% to 300% of target market cap
MAX_MARKET_CAP_RATIO=3.0

# Processing Configuration
PARALLEL_COMPANY_LIMIT=6  # Max concurrent company analyses
COMPETITIVE_REPORT_TIMEOUT=600  # 10 minutes max processing time

# Storage
STORE_COMPARATIVE_HISTORY=True  # Enable month-over-month tracking
HISTORY_RETENTION_MONTHS=24  # Keep 2 years of comparative data
```

**Settings Files:**
- `client_config.yaml` - Add `competitive_intelligence` section per client:
```yaml
clients:
  enterprise_tier_1:
    competitive_intelligence:
      enabled: true
      max_peers: 5
      auto_publish_wordpress: true
      report_frequency: monthly
      peer_discovery_mode: auto  # auto | manual
      custom_peer_groups:
        WRB: ["PGR", "CB", "TRV", "HIG"]  # Optional override
```

### API Changes

**New Endpoints:**

```python
POST /api/competitive-intelligence/generate
{
  "symbol": "WRB",
  "peer_symbols": ["PGR", "CB", "TRV", "HIG"],  # Optional, auto-discovered if null
  "include_sections": [  # Optional, defaults to all
    "executive_summary",
    "competitive_dashboard", 
    "hidden_strengths",
    "steal_playbook",
    "valuation_forensics",
    "actionable_roadmap"
  ],
  "publish_to_blog": true,
  "blog_visibility": "private",  # private | public
  "api_endpoint": "https://client.com/wp-json/custom-api/v1/create-blog",
  "api_key": "...",
  "blog_url": "https://client.com"
}

Response (200 OK):
{
  "success": true,
  "symbol": "WRB",
  "peer_symbols": ["PGR", "CB", "TRV", "HIG"],
  "processing_time_seconds": 387,
  "report_sections": {
    "executive_summary": "...",
    "competitive_dashboard": {...},
    "hidden_strengths": {...},
    "steal_playbook": {...},
    "valuation_forensics": {...},
    "actionable_roadmap": [...]
  },
  "key_insights": {
    "valuation_gap": "8.4x (12.1x vs peer avg 14.5x)",
    "operational_rank": "1st in combined ratio, 2nd in ROE",
    "narrative_score": "42/100 (low)",
    "top_recommendation": "Rebrand specialty underwriting as AI-powered risk assessment"
  },
  "post_url": "https://client.com/2025/10/21/wrb-competitive-intelligence-october-2025/",
  "historical_comparison": {
    "month_ago": {...},  # If available
    "changes": [...]
  }
}

POST /api/competitive-intelligence/discover-peers
{
  "symbol": "WRB",
  "sector": "Insurance",  # Optional, auto-detected if null
  "max_peers": 5
}

Response (200 OK):
{
  "success": true,
  "symbol": "WRB",
  "detected_sector": "Property & Casualty Insurance",
  "market_cap": 11.2B,
  "peers": [
    {"symbol": "PGR", "name": "Progressive Corp", "market_cap": 142B, "similarity_score": 0.87},
    {"symbol": "CB", "name": "Chubb Ltd", "market_cap": 108B, "similarity_score": 0.82},
    {"symbol": "TRV", "name": "Travelers Companies", "market_cap": 51B, "similarity_score": 0.79},
    {"symbol": "HIG", "name": "Hartford Financial", "market_cap": 29B, "similarity_score": 0.75},
    {"symbol": "AIG", "name": "American International Group", "market_cap": 48B, "similarity_score": 0.71}
  ]
}

GET /api/competitive-intelligence/history/{symbol}?months=12
{
  "success": true,
  "symbol": "WRB",
  "historical_data": [
    {
      "month": "2025-10",
      "pe_ratio": 12.1,
      "peer_avg_pe": 14.9,
      "gap": 2.8,
      "combined_ratio": 88.3,
      "roe": 18.4,
      "narrative_score": 42
    },
    // ... 11 more months
  ],
  "trends": {
    "valuation_gap": "widening (+0.5x from 12 months ago)",
    "operational_performance": "improving (combined ratio -1.2 points)",
    "narrative_effectiveness": "declining (score -8 points)"
  }
}
```

### Database/Storage Changes

**New Tables:**

```sql
-- Stores comparative analysis results over time
CREATE TABLE competitive_intelligence_reports (
    id SERIAL PRIMARY KEY,
    target_symbol VARCHAR(10) NOT NULL,
    report_date DATE NOT NULL,
    peer_symbols JSONB NOT NULL,  -- ["PGR", "CB", "TRV", "HIG"]
    report_data JSONB NOT NULL,   -- Full report structure
    processing_time_seconds INT,
    blog_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(target_symbol, report_date)
);

CREATE INDEX idx_target_symbol ON competitive_intelligence_reports(target_symbol);
CREATE INDEX idx_report_date ON competitive_intelligence_reports(report_date);

-- Stores individual company metrics for time-series
CREATE TABLE company_metrics_history (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    metric_date DATE NOT NULL,
    pe_ratio DECIMAL(5,2),
    market_cap_billions DECIMAL(8,2),
    roe DECIMAL(5,2),
    combined_ratio DECIMAL(5,2),  -- Insurance-specific
    reserve_development DECIMAL(5,2),  -- Insurance-specific
    management_sentiment_score INT,  -- 0-100
    analyst_confusion_score INT,  -- 0-100
    narrative_effectiveness_score INT,  -- 0-100
    earnings_call_word_count INT,
    tech_mention_frequency INT,  -- How many times "technology" / "AI" / "data" mentioned
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(symbol, metric_date)
);

CREATE INDEX idx_symbol_date ON company_metrics_history(symbol, metric_date);

-- Stores linguistic patterns extracted from earnings calls
CREATE TABLE linguistic_patterns (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    call_date DATE NOT NULL,
    phrase TEXT NOT NULL,
    frequency INT NOT NULL,
    context TEXT,  -- Surrounding sentences
    sentiment_score DECIMAL(3,2),  -- -1.0 to 1.0
    correlated_pe_change DECIMAL(5,2),  -- P/E change after earnings
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_linguistic_symbol ON linguistic_patterns(symbol);
CREATE INDEX idx_linguistic_phrase ON linguistic_patterns(phrase);

-- Stores peer group definitions (manual overrides)
CREATE TABLE peer_group_definitions (
    id SERIAL PRIMARY KEY,
    target_symbol VARCHAR(10) NOT NULL,
    peer_symbol VARCHAR(10) NOT NULL,
    reason TEXT,  -- Why this peer was selected
    similarity_score DECIMAL(3,2),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(target_symbol, peer_symbol)
);
```

---

## Implementation Plan

### Phase 1: Foundation (Week 1-2)
- [ ] Create `CompetitiveIntelligenceOrchestrator` class structure
- [ ] Implement `PeerDiscoveryService` with FMP API integration
- [ ] Add database tables and migrations
- [ ] Extend `orchestrator.py` with batch processing mode
- [ ] Create new OpenAI assistant (`CompetitiveIntelligenceAssistant`)
- [ ] Unit tests for peer discovery and batch orchestration

### Phase 2: Core Analysis Engines (Week 3-4)
- [ ] Implement `ComparativeAnalysisAgent` (metric comparison logic)
- [ ] Implement `LinguisticAnalysisAgent` (earnings transcript parsing)
- [ ] Implement `ValuationGapAnalyzer` (forensics logic)
- [ ] Add parallel processing for multiple companies
- [ ] Create comparative data storage service
- [ ] Integration tests with real WRB + peers data

### Phase 3: Report Generation (Week 5)
- [ ] Build `CompetitiveIntelligenceReportGenerator`
- [ ] Create report section templates (6 sections)
- [ ] Implement WordPress publishing for private posts
- [ ] Add PDF export capability (optional for enterprise)
- [ ] Format validation and error handling

### Phase 4: API & Integration (Week 6)
- [ ] Create `competitive_intelligence_routes.py` with 3 endpoints
- [ ] Register routes in `app.py`
- [ ] Add authentication/authorization for enterprise tier
- [ ] Implement rate limiting (expensive operation)
- [ ] End-to-end API testing with Postman

### Phase 5: Historical Tracking (Week 7)
- [ ] Build time-series data collection
- [ ] Implement month-over-month comparison logic
- [ ] Add trend identification (widening/narrowing gaps)
- [ ] Create historical analysis endpoint
- [ ] Dashboard visualizations (charts, graphs)

### Phase 6: Polish & Documentation (Week 8)
- [ ] Performance optimization (caching, parallel limits)
- [ ] Error handling improvements
- [ ] Client-facing documentation
- [ ] Sales demo materials
- [ ] Pricing tier configuration

**Estimated Effort:** 8 weeks (1 developer full-time)

---

## Testing Strategy

### Unit Tests
- `test_peer_discovery_service.py` - Peer identification logic
- `test_comparative_analysis_agent.py` - Metric comparison calculations
- `test_linguistic_analysis_agent.py` - Phrase extraction and frequency analysis
- `test_valuation_gap_analyzer.py` - Gap identification logic
- `test_report_generator.py` - Output formatting

**Coverage target:** 85%+

### Integration Tests
- `test_competitive_intelligence_orchestrator.py` - Full pipeline with mock data
- `test_competitive_intelligence_api.py` - API endpoint responses
- `test_wordpress_publishing.py` - Private post creation
- `test_historical_tracking.py` - Time-series data storage

### Manual Testing Scenarios
1. **Full WRB analysis**: Generate competitive intelligence report for WRB vs. PGR/CB/TRV/HIG
   - Verify all 6 sections populated
   - Check metric accuracy against actual financial data
   - Validate linguistic patterns match earnings transcripts
   - Confirm valuation gap math is correct
   
2. **Peer auto-discovery**: Request report for unknown company, verify peer selection makes sense

3. **Historical comparison**: Run report for same company 2 months in a row, verify trends calculated correctly

4. **WordPress publishing**: Ensure private posts are password-protected and formatted properly

5. **Performance**: Process 6 companies in under 10 minutes

**Acceptance Criteria:**
- [ ] Can generate full competitive intelligence report for any public company in < 10 minutes
- [ ] Peer auto-discovery selects appropriate comparables (same sector, similar market cap)
- [ ] All 6 report sections contain actionable, specific insights (not generic fluff)
- [ ] Linguistic analysis identifies at least 10 key phrase patterns per company
- [ ] Valuation gap analysis provides minimum 15 ranked recommendations
- [ ] Month-over-month trends calculated correctly when historical data exists
- [ ] WordPress publishing creates private, password-protected posts
- [ ] API returns proper error messages for invalid inputs
- [ ] System handles API rate limits gracefully (FMP, OpenAI)
- [ ] Database stores results for future historical queries

---

## Alternatives Considered

### Alternative 1: Manual Peer Selection Only (No Auto-Discovery)
**Pros:**
- Simpler implementation
- No need for sector classification logic
- Users have full control over peer selection

**Cons:**
- Requires users to know their competitive landscape
- Misses opportunity for discovering non-obvious peers
- Reduces "wow factor" of auto-intelligence

**Why rejected:** Auto-discovery is a key differentiator. Users expect AI to be smart enough to identify peers. We can offer manual override while defaulting to auto-discovery.

### Alternative 2: Build Custom NLP Engine (No OpenAI for Linguistic Analysis)
**Pros:**
- Lower per-report cost (no OpenAI API calls)
- Full control over analysis logic
- Faster processing (no external API latency)

**Cons:**
- Requires 2-3 months to build quality NLP models
- Won't be as sophisticated as GPT-4 for contextual understanding
- Ongoing maintenance burden

**Why rejected:** Time to market is critical. OpenAI's linguistic capabilities are superior. Can optimize costs later if needed.

### Alternative 3: Real-Time Competitive Monitoring (Daily Updates)
**Pros:**
- More valuable to clients (daily vs monthly intelligence)
- Higher perceived value = higher pricing
- Catches competitive moves immediately

**Cons:**
- 30x higher infrastructure costs (daily runs vs monthly)
- Most financial metrics only update quarterly
- Creates alert fatigue (too many updates)

**Why rejected:** Monthly cadence matches earnings cycle and client budget cycles. Can offer real-time monitoring as premium tier later.

### Alternative 4: Single-Agent Approach (No Specialized Agents)
**Pros:**
- Simpler architecture
- Faster development
- Lower OpenAI costs

**Cons:**
- Less sophisticated analysis
- Harder to ensure comprehensive coverage
- Reduces quality differentiation

**Why rejected:** Multi-agent approach is our core differentiator. Competitive intelligence requires specialized perspectives (financial, linguistic, technical, strategic).

---

## Dependencies

**External Dependencies:**
- `openai>=1.12.0` - For CompetitiveIntelligenceAssistant and LinguisticAnalysisAgent
- `psycopg2-binary>=2.9.0` - PostgreSQL adapter for new tables
- `pandas>=2.0.0` - For comparative data analysis and time-series
- `scikit-learn>=1.3.0` - For similarity scoring in peer discovery
- `yfinance>=0.2.28` - Backup source for market cap and P/E ratios

**Internal Dependencies:**
- Must be completed after: Basic pipeline infrastructure is stable (already done)
- Blocks: Enterprise sales launch (can't sell without this feature)

**Data Dependencies:**
- FinancialModelingPrep API: Company profiles, peer data, sector classifications
- OpenAI API: LLM processing for comparative synthesis
- Existing earnings/financial pipelines: Reuse for multi-company analysis

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **OpenAI API cost explosion** (6 companies × complex analysis × monthly = expensive) | High | Medium | Implement aggressive caching, batch OpenAI calls, set monthly cost limits per client, offer quarterly cadence as cost-saving option |
| **FMP API rate limits** (batch requests for peer data) | Medium | High | Implement request queuing, cache peer group data, upgrade FMP plan, add 2nd data source fallback |
| **Processing time > 10 minutes** (timeout issues) | Medium | Medium | Optimize parallel processing, implement streaming responses, add progress indicators, allow async report generation |
| **Peer auto-discovery selects poor comparables** (different business models in same sector) | High | Medium | Add manual review UI, allow peer group overrides in client_config, implement similarity scoring with multiple factors (not just sector) |
| **Linguistic analysis misses key patterns** (transcripts are noisy) | Medium | Medium | Train assistant with examples, implement pattern validation, add human-in-the-loop review for first 10 reports |
| **Valuation recommendations are too generic** ("improve communication") | High | High | Force specificity in prompts ("provide exact phrases"), include examples from successful peers, rank by estimated valuation impact |
| **Historical data storage grows rapidly** (6 companies × 20+ metrics × monthly = large DB) | Low | High | Implement data retention policies (24 months), archive old reports to S3, compress JSONB fields |
| **Enterprise clients demand custom peer groups** (don't trust auto-discovery) | Low | Medium | Build peer group management UI, allow CSV uploads of custom groups, store in peer_group_definitions table |

---

## Rollout Plan

### Phase 1: Development (Weeks 1-8)
- Complete implementation per plan above
- Internal testing with WRB, NFLX, AAPL examples
- Refine prompts based on output quality
- Performance optimization

### Phase 2: Alpha Testing (Weeks 9-10)
- Generate 5 sample reports (different sectors)
- Internal review: Are recommendations actionable?
- Validate linguistic patterns match reality
- Fix bugs and adjust prompts

### Phase 3: Beta Testing (Weeks 11-12)
- Offer free 3-month trial to 3-5 friendly companies
- Collect feedback: What's valuable? What's missing?
- Iterate on report structure
- Add requested features (if quick)

### Phase 4: Enterprise Launch (Week 13)
- Finalize pricing ($15K-25K/month based on beta feedback)
- Create sales materials (demo videos, case studies)
- Integrate with billing system
- Launch outreach campaign (starting with insurance sector)

### Phase 5: Monitoring & Iteration (Ongoing)
- Track usage metrics (which sections get read most?)
- Collect client testimonials
- Add new sectors (expand beyond insurance)
- Build self-service portal for peer group management

### Deployment Strategy
- Deploy to staging first, run WRB example end-to-end
- Enable for one test client in production (monitor closely)
- Gradual rollout to beta clients
- Full production release after 2 weeks of stable beta

### Rollback Strategy
- Feature flag: `COMPETITIVE_INTELLIGENCE_ENABLED=false` to disable
- Database backups before schema changes
- Keep old single-company endpoints unchanged (backwards compatible)
- If catastrophic failure: revert to previous git tag, restore database

### Monitoring
- **Processing time per report** (target: < 600 seconds)
- **OpenAI API cost per report** (target: < $50)
- **Report quality score** (client surveys: 1-10)
- **Section completion rate** (how many sections fail to generate?)
- **Error rate** (target: < 5% of requests)
- **Client retention** (do they renew after 3 months?)
- **Revenue per client** (track pricing tier distribution)

**Success Metrics:**
- 10 enterprise clients signed within 6 months of launch
- Average processing time < 8 minutes
- Client satisfaction score > 8/10
- 80%+ renewal rate after initial 3-month trial
- $150K+ monthly recurring revenue from competitive intelligence (10 clients × $15K avg)

---

## Open Questions

- [ ] **Peer group size**: Should we always analyze 5 peers, or allow clients to customize (e.g., "analyze vs. top 3 only")?
- [ ] **Sector-specific metrics**: Insurance has combined ratio, tech has revenue growth - how do we handle cross-sector comparisons?
- [ ] **Linguistic analysis depth**: Should we analyze full transcripts or just management remarks (Q&A excluded)?
- [ ] **Valuation forensics accuracy**: How do we validate that our "why multiples differ" explanations are correct? (No ground truth)
- [ ] **Report frequency**: Monthly is default, but should we offer weekly for higher tier? (More expensive, less data changes)
- [ ] **Self-service vs. white-glove**: Do enterprise clients want to generate reports themselves, or prefer scheduled delivery?
- [ ] **Multi-sector analysis**: Can a company request competitive intelligence across sectors (e.g., fintech company vs banks AND tech companies)?
- [ ] **Confidentiality**: How do we handle clients who don't want us analyzing their competitors (concerns about data leakage)?

---

## Future Considerations

**Out of Scope (for now):**
- **Real-time monitoring**: Daily competitive intelligence updates (too expensive, adds alert fatigue)
- **Predictive analytics**: "Progressive will likely announce X next quarter" (requires more sophisticated models)
- **Conference call comparison**: Side-by-side video/audio analysis (complex, limited ROI)
- **Social media sentiment**: Track competitor Twitter/LinkedIn activity (separate feature)
- **M&A target identification**: "Which competitors are acquisition targets?" (separate product)
- **Custom sector definitions**: Allow clients to define their own peer universe (complex UI)
- **API access for clients**: Let enterprises query competitive data programmatically (security concerns)

**Technical Debt:**
- Peer discovery uses simple market cap + sector matching - should implement ML-based similarity scoring later
- Linguistic analysis is English-only - international transcripts ignored
- Report generation is template-based - could use dynamic LLM-generated narratives for more customization
- Historical tracking is monthly snapshots - could track daily price/volume changes for richer analysis

**Potential Enhancements (6-12 months out):**
1. **Competitive alert system**: "Travelers just changed their reserve disclosure strategy - here's what it means"
2. **Messaging A/B testing**: "Try these 3 alternative narratives, see which resonates with analysts"
3. **Sentiment tracking over time**: "Your management sentiment score improved from 42 to 67 after messaging changes"
4. **IR strategy simulator**: "If you adopt Progressive's tech narrative, your P/E could expand by 1.8x based on historical patterns"
5. **Board presentation mode**: Auto-generate PowerPoint slides from competitive intelligence reports
6. **Sector benchmark reports**: "Here's how all P&C insurers stack up" (not company-specific)

---

## References

- [NFLX Case Study](https://dafo.biz/2025/10/21/nflx-inc-nflx-earnings-analysis-q2-2025/) - Proof of prediction accuracy
- [WRB Proposal Letter](../outreach/WRB_proposal_letter.md) - Sales narrative for competitive intelligence
- [Existing Earnings Pipeline](../assistants/llm_pipelines/earnings_call_pipeline.py) - Reusable components
- [Client Config Structure](../../client_config.yaml) - Multi-tenant configuration approach
- [API Documentation](../API_DOCUMENTATION.md) - Existing endpoint patterns to follow

---

## Market Validation

**Why this will sell:**
1. **Pain is real**: CFOs constantly ask "Why does [competitor] trade higher?"
2. **No good alternatives**: Current options are $100K+ consulting engagements (Bain, McKinsey) or manual analyst work
3. **Actionable intelligence**: Not just data dumps - specific "do this" recommendations
4. **Proven ROI**: Hartford's P/E expanded 2.4x in 24 months with better messaging (we show them how)
5. **Sticky revenue**: Monthly subscriptions create predictable recurring revenue

**Target customers:**
- Mid-cap public companies ($2B-$20B market cap)
- Companies with valuation discount vs peers despite good metrics
- Sectors: Insurance, Banking, Healthcare, Retail, Energy
- Decision makers: CFO, Head of IR, CEO (for strategic decisions)

**Pricing justification:**
- $15K-25K/month competitive intelligence
- vs. $100K+ one-time consulting engagement
- vs. $200K+ annual cost of full-time competitive analyst
- **ROI**: 1% P/E expansion on $10B market cap = $100M value creation

**This is a game-changer.** The market will love it.
