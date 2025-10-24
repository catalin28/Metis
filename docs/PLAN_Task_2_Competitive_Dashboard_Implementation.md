# PLAN: Task 2 - Competitive Dashboard Implementation

## 📊 TASK OVERVIEW

**Task**: Implement Section 2 (Competitive Dashboard) of the competitive intelligence report
**Status**: 🔄 **NOT STARTED**
**Priority**: High (builds on validated Executive Summary pattern)
**Dependencies**: Task 1.3 (Schema Design) ✅ COMPLETED

## Purpose & Objectives

### Primary Goal
Implement the Competitive Dashboard section that presents a tabular comparison of the target company versus 3-5 peer companies across 11 key financial and sentiment metrics.

### Key Characteristics
- **LLM Integration**: Generates market perception explanations for each metric
- **11 Comparison Metrics**: Market Cap, P/E, ROE, Revenue Growth, Debt/Equity, Combined Ratio, Management Sentiment, Analyst Confusion, Overall Rank, Market Perception
- **Ranking System**: 1 = Best, Higher = Worse for each metric
- **Data Reuse**: All metrics already calculated during data collection phase - NO recalculation needed
- **Main Work**: Extract metrics from company_data, apply rankings, calculate summary stats, generate LLM explanations

## Detailed Implementation Plan

### **Subtask 2.1: Pydantic Schema Models for Dashboard** 
**Priority**: Critical (defines data structure)
**Status**: 🔄 **NOT STARTED**

**Activities**:
1. **Create Dashboard Section Models**
   ```python
   # File: src/metis/models/report_schema_v2.py (extend existing file)
   
   class CompanyMetrics(BaseModel):
       """Individual company metrics for dashboard row"""
       symbol: str = Field(..., description="Stock ticker symbol")
       company_name: str = Field(..., description="Full company name")
       market_cap_billions: float = Field(..., gt=0, description="Market cap in billions USD")
       pe_ratio: Optional[float] = Field(None, gt=0, description="Price-to-Earnings ratio")
       roe_percentage: Optional[float] = Field(None, description="Return on Equity %")
       revenue_growth_percentage: Optional[float] = Field(None, description="YoY revenue growth %")
       debt_to_equity: Optional[float] = Field(None, ge=0, description="Debt-to-equity ratio")
       combined_ratio: Optional[float] = Field(None, description="Insurance underwriting ratio")
       management_sentiment_score: Optional[int] = Field(None, ge=0, le=100, description="Management sentiment 0-100")
       analyst_confusion_score: Optional[int] = Field(None, ge=0, le=100, description="Analyst confusion 0-100")
       overall_rank: int = Field(..., ge=1, description="Overall ranking (1=best)")
       market_perception: str = Field(..., description="Market perception category")
       calculation_date: datetime = Field(..., description="When metrics were calculated")
       data_quality: str = Field(default="valid", description="Data quality flag")
       
       # Individual metric rankings
       rankings: Dict[str, Optional[int]] = Field(..., description="Rankings for each metric")
   
   class DashboardSummaryStats(BaseModel):
       """Summary statistics for dashboard"""
       target_symbol: str
       peer_count: int = Field(..., ge=1)
       metrics_calculated: int = Field(default=11)
       
       # Peer averages
       averages: Dict[str, float] = Field(..., description="Average values for each metric")
       
       # Target vs peer gaps
       target_vs_peer_gaps: Dict[str, float] = Field(..., description="Target - peer average for each metric")
   
   class OutlierAnalysis(BaseModel):
       """Outlier detection results"""
       outliers: List[Dict[str, Any]] = Field(default_factory=list, description="Detected outliers")
       best_performers: Dict[str, Dict[str, Any]] = Field(..., description="Best performer for each metric")
       worst_performers: Dict[str, Dict[str, Any]] = Field(..., description="Worst performer for each metric")
   
   class CompetitiveDashboard(BaseModel):
       """Complete Competitive Dashboard section"""
       companies: List[CompanyMetrics] = Field(..., min_items=2, description="Target + peers metrics")
       summary_statistics: DashboardSummaryStats = Field(..., description="Summary stats")
       outlier_analysis: OutlierAnalysis = Field(..., description="Outlier detection")
       
       @validator('companies')
       def validate_target_included(cls, v, values):
           """Ensure target company is in the list"""
           if 'summary_statistics' in values:
               target_symbol = values['summary_statistics'].target_symbol
               symbols = [c.symbol for c in v]
               if target_symbol not in symbols:
                   raise ValueError(f"Target company {target_symbol} must be in companies list")
           return v
   ```

2. **Validators for Business Rules**
   - Validate ranking consistency (no duplicate ranks except for ties)
   - Ensure target symbol appears in companies list
   - Verify peer_count matches actual peer companies
   - Check that all metrics have corresponding rankings

**Deliverables**:
- ✅ CompanyMetrics model with all 11 metrics
- ✅ DashboardSummaryStats model
- ✅ OutlierAnalysis model
- ✅ CompetitiveDashboard model with validators
- ✅ Unit tests for all models

---

### **Subtask 2.2: Metrics Extraction & Ranking Logic**
**Priority**: Critical (core functionality)
**Status**: 🔄 **NOT STARTED**

**Activities**:
1. **Create Dashboard Metrics Ranker**
   ```python
   # File: src/metis/data_collecting/dashboard_ranker.py
   
   class DashboardMetricsRanker:
       """Extract and rank dashboard metrics (NO recalculation - data already exists)"""
       
       def __init__(self, company_data: Dict[str, Dict], target_symbol: str):
           self.company_data = company_data
           self.target_symbol = target_symbol
       
       def extract_and_rank_all_metrics(self) -> Dict[str, List[Dict]]:
           """Extract metrics from company_data and apply rankings"""
           # NOTE: All these metrics are already calculated in company_data
           # from CompetitiveDataCollector._collect_single_company()
           return {
               'market_cap_data': self._extract_and_rank(field='market_cap', higher_is_better=True),
               'pe_ratio_data': self._extract_and_rank(field='pe_ratio', higher_is_better=False),
               'roe_data': self._extract_and_rank(field='roe', higher_is_better=True),
               'revenue_growth_data': self._extract_and_rank(field='revenue_growth', higher_is_better=True),
               'debt_equity_data': self._extract_and_rank(field='debt_to_equity', higher_is_better=False),
               'combined_ratio_data': self._extract_and_rank(field='combined_ratio', higher_is_better=False),
               # Sentiment scores from transcripts (if available)
               'sentiment_data': self._extract_sentiment_scores()
           }
       
       def _extract_and_rank(self, field: str, higher_is_better: bool) -> List[Dict]:
           """Apply rankings to all metrics"""
           # Market Cap: higher is better (rank 1 = largest)
           metrics_data['market_cap_data'] = self._rank_metric(
               metrics_data['market_cap_data'], 'market_cap_billions', higher_is_better=True)
           
           # P/E Ratio: lower is often better for value (rank 1 = lowest)
           metrics_data['pe_ratio_data'] = self._rank_metric(
               metrics_data['pe_ratio_data'], 'pe_ratio', higher_is_better=False)
           
           # ROE: higher is better (rank 1 = highest)
           metrics_data['roe_data'] = self._rank_metric(
               metrics_data['roe_data'], 'roe_percentage', higher_is_better=True)
           
           # Revenue Growth: higher is better (rank 1 = highest growth)
           metrics_data['revenue_growth_data'] = self._rank_metric(
               metrics_data['revenue_growth_data'], 'growth_percentage', higher_is_better=True)
           
           # Debt/Equity: lower is better (rank 1 = lowest debt)
           metrics_data['debt_equity_data'] = self._rank_metric(
               metrics_data['debt_equity_data'], 'debt_to_equity', higher_is_better=False)
           
           # Combined Ratio: lower is better (rank 1 = best underwriting)
           metrics_data['combined_ratio_data'] = self._rank_metric(
               metrics_data['combined_ratio_data'], 'combined_ratio', higher_is_better=False)
           
           # Management Sentiment: higher is better (rank 1 = most positive)
           # Analyst Confusion: lower is better (rank 1 = least confused)
           # Handle in sentiment data processing
           
           """Extract field from company_data and apply ranking"""
           # Extract metric for all companies
           metric_data = [
               {
                   'symbol': symbol,
                   'value': data.get(field),
                   'company_name': data.get('name', symbol)
               }
               for symbol, data in self.company_data.items()
               if data.get('available', True)  # Skip failed collections
           ]
           
           # Sort and rank
           sorted_data = sorted(
               metric_data, 
               key=lambda x: x['value'] if x['value'] is not None else (-float('inf') if higher_is_better else float('inf')),
               reverse=higher_is_better
           )
           
           for rank, item in enumerate(sorted_data, 1):
               item['rank'] = rank if item['value'] is not None else None
           
           return sorted_datam['rank'] = rank
               else:
                   item['rank'] = None  # Missing data
           return data
       
       def calculate_overall_rank(self, company_symbol: str, all_rankings: Dict) -> int:
           """Calculate weighted overall rank from individual metric ranks"""
           # Weights for each metric (sum to 1.0)
           weights = {
               'pe_ratio': 0.20,
               'roe': 0.20,
2. **Data Extraction from Existing company_data**
   - NO API calls needed - all metrics already in company_data from CompetitiveDataCollector
   - Extract: market_cap, pe_ratio, roe, revenue_growth, debt_to_equity, combined_ratio
   - Sentiment scores: Extract from transcripts if available, or skip if no transcripts

**Deliverables**:
- ✅ DashboardMetricsRanker class (renamed from Calculator)
- ✅ Ranking logic for all 11 metrics
- ✅ Overall rank calculation with weighted average
- ✅ Unit tests for ranking edge cases (ties, missing data)
           for metric, weight in weights.items():
               rank = all_rankings.get(metric, {}).get(company_symbol, {}).get('rank')
               if rank is not None:
                   weighted_sum += rank * weight
           
           return round(weighted_sum)
   ```

2. **Data Reuse from Executive Summary**
   - Avoid redundant FMP API calls
   - Reuse: Market Cap, P/E, ROE, Revenue Growth, Debt/Equity
   - Only calculate NEW metrics: Combined Ratio, Sentiment Scores

**Deliverables**:
- ✅ DashboardMetricsCalculator class
- ✅ Ranking logic for all 11 metrics
- ✅ Overall rank calculation with weighted average
- ✅ Unit tests for ranking edge cases (ties, missing data)

---

### **Subtask 2.3: Input Model Transformer for Dashboard**
**Priority**: High (data preparation)
**Status**: 🔄 **NOT STARTED**

**Activities**:
       Returns:
           CompetitiveDashboardInput ready for Pydantic validation
       """
       
       # Extract and rank metrics (NO calculation - already in company_data)
       ranker = DashboardMetricsRanker(company_data, target_symbol)
       ranked_metrics = ranker.extract_and_rank_all_metrics()
       comparative_metrics: Dict[str, Any]
   ) -> CompetitiveDashboardInput:
       """
       Transform raw data into CompetitiveDashboard input model
       
       Args:
           target_symbol: Target company symbol
           company_data: Raw company data from FMP
           comparative_metrics: Pre-calculated metrics from Executive Summary
       
       Returns:
           CompetitiveDashboardInput ready for Pydantic validation
       """
       
       # Calculate dashboard-specific metrics
       calculator = DashboardMetricsCalculator(company_data, target_symbol)
       metrics_data = calculator.calculate_all_metrics()
       ranked_metrics = calculator.apply_rankings(metrics_data)
       
       # Build company metrics list
       companies = []
       for symbol in [target_symbol] + list(company_data.keys()):
           if symbol == target_symbol:
               continue  # Skip target in peer list
           
           # Gather all metrics for this company
           company_metrics = CompanyMetrics(
               symbol=symbol,
               company_name=company_data[symbol]['name'],
               market_cap_billions=self._extract_metric(ranked_metrics, 'market_cap_data', symbol, 'market_cap_billions'),
               pe_ratio=self._extract_metric(ranked_metrics, 'pe_ratio_data', symbol, 'pe_ratio'),
               roe_percentage=self._extract_metric(ranked_metrics, 'roe_data', symbol, 'roe_percentage'),
               revenue_growth_percentage=self._extract_metric(ranked_metrics, 'revenue_growth_data', symbol, 'growth_percentage'),
               debt_to_equity=self._extract_metric(ranked_metrics, 'debt_equity_data', symbol, 'debt_to_equity'),
               combined_ratio=self._extract_metric(ranked_metrics, 'combined_ratio_data', symbol, 'combined_ratio'),
               management_sentiment_score=self._extract_metric(ranked_metrics, 'sentiment_data', symbol, 'management_sentiment_score'),
               analyst_confusion_score=self._extract_metric(ranked_metrics, 'sentiment_data', symbol, 'analyst_confusion_score'),
               overall_rank=calculator.calculate_overall_rank(symbol, ranked_metrics),
               market_perception=self._determine_market_perception(symbol, ranked_metrics),
               calculation_date=datetime.now(),
               data_quality="valid",
**Deliverables**:
- ✅ create_competitive_dashboard_input() method
- ✅ Helper methods for metric extraction from company_data
- ✅ Summary statistics calculation (peer averages, gaps)
- ✅ Outlier detection logic
- ✅ Unit tests with real company_data structuree_summary_stats(target_symbol, companies, ranked_metrics)
       
       # Perform outlier analysis
       outlier_analysis = self._analyze_outliers(companies, ranked_metrics)
       
       return CompetitiveDashboard(
           companies=companies,
           summary_statistics=summary_stats,
           outlier_analysis=outlier_analysis
       )
   ```

**Deliverables**:
- ✅ create_competitive_dashboard_input() method
- ✅ Helper methods for metric extraction and ranking aggregation
- ✅ Summary statistics calculation
- ✅ Outlier detection logic
- ✅ Unit tests with mock company data

---

### **Subtask 2.4: Report Generator Integration with LLM**
**Priority**: High (orchestration + LLM generation)
**Status**: 🔄 **NOT STARTED**

**Activities**:
1. **Add Dashboard Generation Method with LLM Integration**
   ```python
   # File: src/metis/orchestrators/report_generator.py (extend existing)
   
   async def generate_competitive_dashboard(
       self,
       target_symbol: str,
       company_data: Dict[str, Dict],
       comparative_metrics: Dict[str, Any]
   ) -> CompetitiveDashboard:
       """
       Generate Competitive Dashboard section with LLM-generated market perception explanations
       
       Args:
           target_symbol: Target company symbol
           company_data: Already collected company data (from Executive Summary step)
           comparative_metrics: Already calculated metrics (from Executive Summary step)
       
       Returns:
           CompetitiveDashboard Pydantic model with LLM-generated explanations
       """
       logger.info(f"Generating Competitive Dashboard for {target_symbol}")
       
       # Step 1: Transform data into input model (raw metrics + rankings)
       dashboard_input = self.input_transformer.create_competitive_dashboard_input(
           target_symbol=target_symbol,
           company_data=company_data,
           comparative_metrics=comparative_metrics
       )
       
       # Step 2: Generate LLM explanations for each metric's market perception
       # Uses generic_llm_agent with structured output to explain:
       # - Why each metric matters for valuation
       # - What the market perception is (undervalued, fair, premium, etc.)
       # - How this specific metric impacts the valuation gap
       
       # MANDATORY: Load prompt from file
       prompt_template = self._load_prompt("prompts/competitive_analysis/dashboard_explanations.txt")
       
       # Format prompt with dashboard data
       prompt = prompt_template.format(
           target_symbol=target_symbol,
           company_name=company_data[target_symbol]['name'],
           metrics_json=json.dumps(dashboard_input.model_dump(), indent=2),
           peer_count=len(dashboard_input.peer_symbols)
       )
       
       # Step 3: Call LLM to generate market perception explanations
       # Returns CompetitiveDashboard with perception_explanation filled for each metric
       dashboard_with_explanations = await self.llm_agent.generate_structured_output(
           prompt=prompt,
           response_format=CompetitiveDashboard
       )
       
       logger.info(f"✓ Competitive Dashboard generated for {target_symbol} with {len(dashboard_with_explanations.metrics)} metrics")
       return dashboard_with_explanations
   ```

2. **Create Dashboard Explanations Prompt File**
   ```
   # File: prompts/competitive_analysis/dashboard_explanations.txt
   
   You are a financial analyst explaining competitive metrics for {target_symbol} ({company_name}).
   
   For each metric in the dashboard below, provide:
   1. Market perception category (Undervalued/Underappreciated/Fair/Premium/Overvalued)
   2. A 50-300 character explanation of WHY this perception exists and its valuation impact
   
   Focus on:
   - Hidden strengths (good metrics with low P/E = underappreciated)
   - Perception gaps (strong performance not reflected in valuation)
   - Communication issues (complex metrics analysts don't understand)
   
   Dashboard Data:
   {metrics_json}
   
   Generate structured CompetitiveDashboard output with market_perception and perception_explanation for each metric.
   ```

3. **Update Report Generation Workflow**
   - Generate Executive Summary (Section 1) ✅ Already working
   - Generate Competitive Dashboard (Section 2) - NEW with LLM explanations
   - Skip Sections 3-6 for now (future work)

**Deliverables**:
- ✅ generate_competitive_dashboard() method with LLM integration
- ✅ Dashboard explanations prompt file
- ✅ Integration with existing data collection pipeline
- ✅ No redundant API calls (reuses Executive Summary data)
- ✅ LLM-generated market perception explanations for context

---

### **Subtask 2.5: Testing & Validation**
**Priority**: Critical (quality assurance)
**Status**: 🔄 **NOT STARTED**

**Activities**:
1. **Create Test Script**
   ```python
   # File: test_competitive_dashboard.py
   
   async def test_competitive_dashboard():
       """Test Competitive Dashboard generation"""
       
       # Step 4: Calculate comparative metrics (already done, just reuse)
       comparative_metrics = generator.data_collector.calculate_comparative_metrics(
           company_data=company_data,
           target_symbol=target_symbol
       )
       # NOTE: company_data already has ALL metrics calculated
       # (market_cap, pe_ratio, roe, revenue_growth, debt_to_equity, combined_ratio, etc.)eer_service = PeerDiscoveryService()
       
       # Step 2: Discover peers
       peers = await peer_service.identify_peers(symbol=target_symbol, max_peers=3)
       peer_symbols = [p['symbol'] for p in peers]
       
       # Step 3: Collect data (reuse from Executive Summary)
       company_data = generator.data_collector.collect_all_company_data(
           target_symbol=target_symbol,
           peer_symbols=peer_symbols,
           max_workers=3
       )
       
       # Step 4: Calculate comparative metrics
       comparative_metrics = generator.data_collector.calculate_comparative_metrics(
           company_data=company_data,
           target_symbol=target_symbol
       )
       
       # Step 5: Generate Competitive Dashboard
       dashboard = await generator.generate_competitive_dashboard(
           target_symbol=target_symbol,
           company_data=company_data,
           comparative_metrics=comparative_metrics
       )
       
       # Step 6: Validate and display results
       assert len(dashboard.companies) == 4  # Target + 3 peers
       assert dashboard.summary_statistics.target_symbol == target_symbol
       assert dashboard.summary_statistics.peer_count == 3
       
       # Save to JSON
       output_file = f"test_competitive_dashboard_{target_symbol.lower()}.json"
       with open(output_file, 'w') as f:
           json.dump(dashboard.model_dump(), f, indent=2, default=str)
       
       print(f"✓ Dashboard saved to {output_file}")
       return dashboard
   ```

2. **Validation Checks**
   - All 11 metrics present for each company
   - Rankings are consistent (1 = best, no gaps)
   - Summary statistics match individual metrics
   - Outlier detection flags extreme values correctly
   - Target company included in companies list

**Deliverables**:
- ✅ test_competitive_dashboard.py script
- ✅ Validation for all business rules
- ✅ JSON output file with complete dashboard
- ✅ Edge case tests (missing data, ties in rankings)

---

## Success Criteria

**Section 2 (Competitive Dashboard) is COMPLETE when:**

1. ✅ All Pydantic models created and validated
2. ✅ All 11 metrics calculated correctly with proper rankings
**Required (Already Complete)**:
- ✅ Task 1.3: Schema Design
- ✅ Executive Summary generation working
- ✅ Data collection pipeline operational (CompetitiveDataCollector calculates all metrics)
- ✅ Peer discovery service functional

**No External Dependencies**:
- No new FMP API calls required (all data already collected)
- LLM calls needed for market perception explanations only
- Reuses all existing infrastructure and calculated metrics-3 hours
- **Subtask 2.2** (Metrics & Ranking): 3-4 hours
- **Subtask 2.3** (Input Transformer): 2-3 hours
- **Subtask 2.4** (Report Generator): 1-2 hours
- **Subtask 2.5** (Testing): 2-3 hours

**Total Estimated Time**: 10-15 hours

## Dependencies

**Required (Already Complete)**:
- ✅ Task 1.3: Schema Design
- ✅ Executive Summary generation working
- ✅ Data collection pipeline operational
- ✅ Peer discovery service functional

**No External Dependencies**:
- No new APIs or services required
- No LLM calls needed (pure data section)
- Reuses all existing infrastructure

## Next Steps After Completion

After Section 2 is complete, proceed to:
- **Section 3**: Hidden Strengths (narrative + rankings)
- **Section 4**: Steal Their Playbook (linguistic analysis)
- **Section 5**: Valuation Forensics (bridge analysis)
- **Section 6**: Actionable Roadmap (recommendations)
