# Example: What Data Gets Sent to LLM for Competitive Dashboard

## Flow Overview

1. **Data Collection** → `company_data` has ALL metrics already calculated
2. **Ranker Extraction** → `DashboardMetricsRanker` extracts and ranks metrics
3. **Input Model** → `CompetitiveDashboardInput` formatted for LLM
4. **Prompt Template** → Formatted with input data
5. **LLM Call** → Generates `CompetitiveDashboard` with explanations

---

## Example Input Data (CIB + 3 Peers)

### Target Company: CIB (Grupo Cibest S.A.)
### Peers: AVAL, BSAC, BCH

---

## What the LLM Receives (CompetitiveDashboardInput)

```json
{
  "target_symbol": "CIB",
  "peer_symbols": ["AVAL", "BSAC", "BCH"],
  "metrics": [
    {
      "metric_name": "Market Cap",
      "target_value": 13241953057,  // $13.2B
      "peer_values": {
        "AVAL": 8500000000,    // $8.5B
        "BSAC": 15200000000,   // $15.2B  
        "BCH": 11000000000     // $11.0B
      },
      "target_rank": 2  // 2nd largest
    },
    {
      "metric_name": "P/E Ratio",
      "target_value": 7.65,
      "peer_values": {
        "AVAL": 11.20,
        "BSAC": 12.50,
        "BCH": 12.05
      },
      "target_rank": 4  // Lowest P/E (worst rank for valuation)
    },
    {
      "metric_name": "ROE",
      "target_value": 14.2,  // 14.2%
      "peer_values": {
        "AVAL": 18.5,
        "BSAC": 16.1,
        "BCH": 12.8
      },
      "target_rank": 3  // 3rd out of 4
    },
    {
      "metric_name": "Revenue Growth",
      "target_value": 8.5,  // 8.5%
      "peer_values": {
        "AVAL": 12.3,
        "BSAC": 6.2,
        "BCH": 9.1
      },
      "target_rank": 3  // 3rd out of 4
    },
    {
      "metric_name": "Debt/Equity",
      "target_value": 0.45,
      "peer_values": {
        "AVAL": 0.62,
        "BSAC": 0.38,
        "BCH": 0.51
      },
      "target_rank": 2  // 2nd lowest (2nd best)
    },
    {
      "metric_name": "Gross Margin",
      "target_value": 68.3,  // 68.3%
      "peer_values": {
        "AVAL": 72.1,
        "BSAC": 65.4,
        "BCH": 70.2
      },
      "target_rank": 3  // 3rd out of 4
    },
    {
      "metric_name": "Operating Margin",
      "target_value": 42.5,  // 42.5%
      "peer_values": {
        "AVAL": 48.2,
        "BSAC": 38.9,
        "BCH": 45.1
      },
      "target_rank": 3  // 3rd out of 4
    },
    {
      "metric_name": "Net Margin",
      "target_value": 28.1,  // 28.1%
      "peer_values": {
        "AVAL": 32.5,
        "BSAC": 24.8,
        "BCH": 29.3
      },
      "target_rank": 3  // 3rd out of 4
    }
  ]
}
```

---

## What the Prompt Looks Like (After Formatting)

```
Generate competitive dashboard with market perception analysis for CIB.

**Target Company**: CIB
**Peer Companies**: ['AVAL', 'BSAC', 'BCH']

**Raw Metrics Data**:
[
  {
    "metric_name": "Market Cap",
    "target_value": 13241953057,
    "peer_values": {"AVAL": 8500000000, "BSAC": 15200000000, "BCH": 11000000000},
    "target_rank": 2
  },
  {
    "metric_name": "P/E Ratio",
    "target_value": 7.65,
    "peer_values": {"AVAL": 11.20, "BSAC": 12.50, "BCH": 12.05},
    "target_rank": 4
  },
  {
    "metric_name": "ROE",
    "target_value": 14.2,
    "peer_values": {"AVAL": 18.5, "BSAC": 16.1, "BCH": 12.8},
    "target_rank": 3
  },
  ... (5 more metrics)
]

**Instructions**:
Analyze each metric to determine market perception and generate explanations...

[REST OF PROMPT TEMPLATE]
```

---

## What the LLM Returns (CompetitiveDashboard)

```json
{
  "metrics": [
    {
      "metric_name": "Market Cap",
      "target_value": 13241953057,
      "peer_values": {"AVAL": 8500000000, "BSAC": 15200000000, "BCH": 11000000000},
      "target_rank": 2,
      "rank_qualifier": "2nd largest",
      "market_perception": "Adequate",
      "perception_explanation": "Mid-tier market cap positioning aligns with operational scale. Adequate size for regional banking franchise without significant premium or discount."
    },
    {
      "metric_name": "P/E Ratio",
      "target_value": 7.65,
      "peer_values": {"AVAL": 11.20, "BSAC": 12.50, "BCH": 12.05},
      "target_rank": 4,
      "rank_qualifier": "lowest",
      "market_perception": "Root cause",
      "perception_explanation": "Lowest P/E multiple at 7.65x vs peer average 11.92x reflects market skepticism about growth sustainability despite solid profitability metrics, driving -35.8% valuation discount."
    },
    {
      "metric_name": "ROE",
      "target_value": 14.2,
      "peer_values": {"AVAL": 18.5, "BSAC": 16.1, "BCH": 12.8},
      "target_rank": 3,
      "rank_qualifier": "3rd",
      "market_perception": "Undervalued",
      "perception_explanation": "ROE of 14.2% is competitive (above one peer) but trading at lowest P/E suggests market undervalues profitability quality relative to growth concerns."
    },
    {
      "metric_name": "Debt/Equity",
      "target_value": 0.45,
      "peer_values": {"AVAL": 0.62, "BSAC": 0.38, "BCH": 0.51},
      "target_rank": 2,
      "rank_qualifier": "2nd best",
      "market_perception": "Hidden strength",
      "perception_explanation": "Conservative leverage at 0.45 debt/equity (2nd best) demonstrates prudent capital management but market doesn't reward this financial discipline given low valuation multiple."
    }
    ... (4 more metrics)
  ],
  "overall_target_rank": 3,
  "key_strengths_summary": "CIB demonstrates financial discipline with conservative leverage (0.45 debt/equity, #2), mid-tier market cap scale ($13.2B, #2), and competitive profitability (ROE 14.2%, above BCH).",
  "key_weaknesses_summary": "Valuation discount driven by lowest P/E (7.65x, #4), below-average growth momentum (8.5% revenue growth, #3), and margin compression relative to top performers (operating margin 42.5%, #3).",
  "perception_gap_count": 2
}
```

---

## Key Points

1. **9 Metrics Sent** (from CIB example):
   - Market Cap, P/E Ratio, ROE, Revenue Growth, Debt/Equity
   - Gross Margin, Operating Margin, Net Margin
   - Combined Ratio (skipped if not applicable - only for insurance companies)

2. **Each Metric Includes**:
   - `metric_name`: Display name (e.g., "P/E Ratio")
   - `target_value`: Target company's raw value (e.g., 7.65)
   - `peer_values`: Dict of peer symbols → values (e.g., {"AVAL": 11.20, ...})
   - `target_rank`: Ranking position (1 = best)

3. **LLM Adds** (for each metric):
   - `rank_qualifier`: Human description ("lowest", "2nd best")
   - `market_perception`: Enum (Undervalued, Hidden strength, etc.)
   - `perception_explanation`: 20-500 char WHY explanation

4. **LLM Also Generates**:
   - `overall_target_rank`: Weighted average rank
   - `key_strengths_summary`: Top 3 strengths narrative
   - `key_weaknesses_summary`: Top 3 weaknesses narrative
   - `perception_gap_count`: Count of strong metrics + low valuation

---

## Data Flow Summary

```
company_data (from FMP)
  ↓
DashboardMetricsRanker.extract_and_rank_all_metrics()
  ↓
CompetitiveDashboardInput (9 metrics with values + ranks)
  ↓
Prompt Template (formats as JSON + instructions)
  ↓
LLM (gpt-4o-mini)
  ↓
CompetitiveDashboard (9 metrics with explanations + summaries)
```

**Cost**: ~$0.50-1.00 per dashboard generation (depends on number of metrics and explanation length)
