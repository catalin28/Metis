# SUBTASK 1.3.2: Pydantic Model Implementation

## 📊 STATUS OVERVIEW
**Status**: 🔄 **PARTIALLY IMPLEMENTED** - Basic v2 models created, needs expansion for full plan  
**Progress**: 60% - Basic v2 models ✅, full expansion pending ❌  
**Priority**: Critical (foundational for all report generation)

---

## CURRENT STATE

### What's Already Done ✅
- Basic Pydantic v2 models in `src/metis/models/report_schema_v2.py` (simplified version)
- Comprehensive type hints and inline documentation
- Basic validation structure

### What Needs to Be Done ❌
- **Custom validators for business logic enforcement** (pending)
- **Model inheritance hierarchy for code reuse** (pending full expansion)
- **Full 6-section schema expansion** per original RFC-001 specifications

---

## IMPLEMENTATION REQUIREMENTS

### 1. Create Base Model Structure ✅ PARTIALLY DONE

**File**: `src/metis/models/report_schema.py`

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
from uuid import uuid4
```

### 2. Implement Core Data Models - NEEDS FULL EXPANSION

**Current simplified models need to be expanded to include:**

#### **ReportMetadata** 
- Report identification, timestamps, version info, client data

#### **CompanyProfile** 
- Target company information (symbol, name, sector, industry, market cap, country)

#### **PeerGroup** 
- Peer companies list with similarity scores, selection method, manual override flags

#### **Fundamentals** 
- TTM metrics, peer comparisons, rankings, hidden strengths identification

#### **Valuation** 
- P/E gaps, decomposition analysis, valuation bridge components

#### **Sentiment** 
- Narrative scores, linguistic patterns, peer comparisons, event study results

#### **Recommendations** 
- Executive summary, actionable insights (Do/Say/Show), steal-their-playbook insights

#### **ProcessingMetadata** 
- Cost tracking, timing, confidence scores, error handling

---

## DETAILED SECTION SPECIFICATIONS

### Section 1: Executive Summary (Narrative Required ✅)

**Pydantic Model Requirements:**
```python
class ExecutiveSummary(BaseModel):
    company_overview: str = Field(..., min_length=200, max_length=2000, description="Target company overview (1 paragraph narrative)")
    key_finding: str = Field(..., min_length=50, description="Valuation gap with specific numbers (e.g., 'trades at 12.1x vs peer avg 14.5x')")
    root_cause: str = Field(..., min_length=50, description="Number of perception gaps identified (e.g., '3 perception gaps')")
    top_recommendations: List[str] = Field(..., min_items=3, max_items=3, description="Top 3 actionable recommendations with impact estimates")
    
    @validator('key_finding')
    def validate_key_finding_has_numbers(cls, v):
        # Must contain P/E ratio comparisons and specific numbers
        if not any(char.isdigit() for char in v):
            raise ValueError("Key finding must include specific numerical comparisons")
        return v
```

**Narrative Generation Integration:**
- **Primary Tool**: `src/metis.assistants.generic_llm_agent.py`
- **MANDATORY Prompt Management**: All prompts stored in `prompts/narrative_generation/` directory
- **Methods Used**:
  * `generate_text_sync()` - For executive summaries and explanatory content
  * `generate_structured_output()` - For recommendations with consistent formatting
  * `generate_json_output()` - For structured insights requiring specific data formatting

### Section 2: Competitive Dashboard (No Narrative Required ❌)

**Pydantic Model Requirements:**
```python
class MarketPerception(BaseModel):
    category: Literal["Undervalued", "Underappreciated", "Hidden Strength", "Fair Value", "Premium", "Overvalued"]
    explanation: str = Field(..., min_length=100, max_length=500)
    analysis: Dict[str, Any] = Field(..., description="LLM-generated detailed analysis")
    calculation_date: datetime

class CompanyMetric(BaseModel):
    symbol: str = Field(..., regex=r'^[A-Z]{1,5}$')
    pe_ratio: Optional[float] = Field(None, gt=0, description="Price-to-Earnings multiple")
    roe_percentage: Optional[float] = Field(None, ge=0, le=100, description="Return on Equity percentage")
    revenue_growth_percentage: Optional[float] = Field(None, ge=-100, le=1000, description="Year-over-year revenue growth")
    market_cap_billions: Optional[float] = Field(None, gt=0, description="Market capitalization in billions")
    debt_to_equity: Optional[float] = Field(None, ge=0, description="Debt-to-equity ratio")
    combined_ratio: Optional[float] = Field(None, gt=0, description="Insurance underwriting performance")
    management_sentiment_score: Optional[int] = Field(None, ge=0, le=100, description="Management communication sentiment")
    analyst_confusion_score: Optional[int] = Field(None, ge=0, le=100, description="Analyst uncertainty level")
    overall_rank: Optional[int] = Field(None, ge=1, description="Composite ranking position")
    market_perception: Optional[MarketPerception] = None
    calculation_date: datetime
    data_quality: Literal["valid", "estimated", "outlier", "excluded", "stale"]
    rankings: Dict[str, Optional[int]] = Field(default_factory=dict, description="Ranking by metric")

class CompetitiveDashboard(BaseModel):
    companies: List[CompanyMetric] = Field(..., min_items=2, max_items=10, description="Target company + peers")
    summary_statistics: Dict[str, Any] = Field(..., description="Summary stats and averages")
    outlier_analysis: Dict[str, Any] = Field(..., description="Outlier detection and best/worst performers")
    
    @validator('companies')
    def validate_target_company_present(cls, v):
        # Ensure target company is first in list
        if not v or len(v) < 2:
            raise ValueError("Must have at least target company + 1 peer")
        return v
```

### Section 3: Hidden Strengths (Narrative Required ✅)

**Pydantic Model Requirements:**
```python
class HiddenStrength(BaseModel):
    title: str = Field(..., min_length=10, max_length=100, description="Concise strength title")
    description: str = Field(..., min_length=50, max_length=500, description="Detailed explanation with quantification")
    quantification: str = Field(..., min_length=20, description="Specific metrics (e.g., 'Reserve quality 40% more consistent than PGR')")
    why_hidden: str = Field(..., min_length=30, description="Root cause analysis: Why analysts miss this strength")
    supporting_data: Dict[str, Any] = Field(default_factory=dict, description="Supporting metrics and calculations")
    
    @validator('quantification')
    def validate_quantification_has_numbers(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError("Quantification must include specific numerical comparisons")
        return v

class HiddenStrengths(BaseModel):
    strengths: List[HiddenStrength] = Field(..., min_items=3, max_items=5, description="3-5 bullet points where target excels but market ignores")
    summary: str = Field(..., min_length=100, description="Overall hidden strengths narrative")
```

### Section 4: Steal Their Playbook (Narrative Required ✅)

**Pydantic Model Requirements:**
```python
class LinguisticData(BaseModel):
    phrase: str = Field(..., min_length=1, description="Specific phrase or term")
    target_frequency: int = Field(..., ge=0, description="How often target company uses this phrase")
    peer_frequency: int = Field(..., ge=0, description="How often peer company uses this phrase")
    correlation_with_valuation: Optional[float] = Field(None, ge=-1, le=1, description="Correlation with P/E premium")
    impact_score: Optional[float] = Field(None, ge=0, le=100, description="Measured impact on valuation")

class CompetitorStrategy(BaseModel):
    peer: str = Field(..., regex=r'^[A-Z]{1,5}$', description="Peer company symbol")
    strategy: str = Field(..., min_length=10, max_length=100, description="Strategy name/title")
    impact: str = Field(..., description="Quantified impact (e.g., 'Appears in 47% of sell-side reports')")
    linguistic_data: LinguisticData = Field(..., description="Phrase frequency and correlation data")
    recommendation: str = Field(..., min_length=30, description="Actionable language recommendation")
    supporting_evidence: List[str] = Field(default_factory=list, description="Supporting quotes or data points")

class StealTheirPlaybook(BaseModel):
    competitor_strategies: List[CompetitorStrategy] = Field(..., min_items=1, max_items=5, description="Competitor messaging strategies with quantified impact")
    linguistic_analysis_summary: str = Field(..., min_length=100, description="Overall linguistic analysis findings")
    top_phrases_to_adopt: List[str] = Field(..., min_items=1, description="Exact phrases correlated with higher multiples")
```

### Section 5: Valuation Forensics (Narrative Required ✅)

**Pydantic Model Requirements:**
```python
class ValuationBridgeComponent(BaseModel):
    name: str = Field(..., min_length=5, description="Component name (e.g., 'ROE Adjustment')")
    value: float = Field(..., description="Numerical impact on P/E multiple")
    explanation: str = Field(..., min_length=50, max_length=300, description="Detailed explanation of this component")
    calculation_details: Dict[str, Any] = Field(default_factory=dict, description="Underlying calculation data")
    
    @validator('explanation')
    def validate_explanation_not_empty(cls, v):
        if not v or v.strip() == "":
            raise ValueError("Bridge component explanation cannot be empty")
        return v

class ValuationGapDecomposition(BaseModel):
    fundamental_component: float = Field(..., description="Gap explained by fundamental differences")
    narrative_component: float = Field(..., description="Gap due to perception/narrative differences")
    
    @validator('narrative_component')
    def validate_gap_components_sum(cls, v, values):
        if 'fundamental_component' in values:
            # Total gap should equal sum of components (within rounding tolerance)
            total = v + values['fundamental_component']
            # This will be validated at parent level with total_gap
        return v

class ValuationForensics(BaseModel):
    current_pe: float = Field(..., gt=0, description="Current P/E ratio of target company")
    peer_average_pe: float = Field(..., gt=0, description="Peer group average P/E ratio")
    total_gap: float = Field(..., description="Total valuation gap (current_pe - peer_average_pe)")
    gap_decomposition: ValuationGapDecomposition = Field(..., description="Fundamental vs narrative gap breakdown")
    valuation_bridge: List[ValuationBridgeComponent] = Field(..., min_items=3, description="Waterfall bridge components")
    forensics_narrative: str = Field(..., min_length=200, description="Detailed valuation analysis explanation")
    
    @validator('total_gap')
    def validate_total_gap_calculation(cls, v, values):
        if 'current_pe' in values and 'peer_average_pe' in values:
            expected_gap = values['current_pe'] - values['peer_average_pe']
            if abs(v - expected_gap) > 0.01:  # Allow small rounding differences
                raise ValueError(f"Total gap {v} does not match calculation {expected_gap}")
        return v
```

### Section 6: Actionable Roadmap (Narrative Required ✅)

**Pydantic Model Requirements:**
```python
class Recommendation(BaseModel):
    id: int = Field(..., ge=1, description="Unique recommendation ID")
    title: str = Field(..., min_length=10, max_length=100, description="Concise recommendation title")
    category: Literal["Do", "Say", "Show"] = Field(..., description="Do/Say/Show categorization")
    priority: Literal["High", "Medium", "Low"] = Field(..., description="Implementation priority")
    problem_statement: str = Field(..., min_length=30, description="Clear problem this recommendation addresses")
    solution_framework: str = Field(..., min_length=50, description="Specific solution and implementation approach")
    expected_impact: str = Field(..., min_length=20, description="Expected outcome and valuation impact")
    timeline: str = Field(..., min_length=10, description="Implementation timeline")
    implementation_details: str = Field(..., min_length=30, description="Specific steps and guidance")
    success_metrics: List[str] = Field(default_factory=list, description="How to measure success")
    
    @validator('id')
    def validate_positive_id(cls, v):
        if v <= 0:
            raise ValueError("Recommendation ID must be positive")
        return v

class ActionableRoadmap(BaseModel):
    recommendations: List[Recommendation] = Field(..., min_items=3, max_items=25, description="18+ recommendations ranked by valuation impact")
    roadmap_summary: str = Field(..., min_length=100, description="Overall roadmap narrative")
    quick_wins: List[str] = Field(default_factory=list, description="Immediate actions with high impact")
    long_term_initiatives: List[str] = Field(default_factory=list, description="Strategic long-term recommendations")
    
    @validator('recommendations')
    def validate_unique_ids(cls, v):
        ids = [rec.id for rec in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Recommendation IDs must be unique")
        return v
```

---

## 3. Advanced Validation Logic - NEEDS IMPLEMENTATION

### Business Rule Validation
- Ensure required fields presence and correct types
- Validate data ranges (P/E ratios > 0, scores 0-100, percentiles 0-100)
- Check date formats and logical temporal constraints
- Validate enum values (categories, priorities, peer types)
- Cross-field validation (total gap = fundamental + narrative components)
- Business rule validation (peer count consistency, ranking logic)

### Narrative Content Validation
- Minimum length requirements for executive summaries (>200 characters)
- Maximum length limits to prevent bloat (<2000 characters per section)
- Required narrative fields cannot be empty strings
- Recommendation count validation (minimum 3, maximum 25)
- Bridge component explanation presence validation

---

## MAIN REPORT SCHEMA - NEEDS FULL INTEGRATION

```python
class CompetitiveIntelligenceReport(BaseModel):
    """Main report schema integrating all 6 sections"""
    
    # Report metadata
    report_metadata: ReportMetadata = Field(..., description="Report identification and metadata")
    
    # Core 6 sections
    executive_summary: ExecutiveSummary = Field(..., description="Section 1: Executive summary with key insights")
    competitive_dashboard: CompetitiveDashboard = Field(..., description="Section 2: Comparative metrics table")
    hidden_strengths: HiddenStrengths = Field(..., description="Section 3: Unrecognized competitive advantages")
    steal_their_playbook: StealTheirPlaybook = Field(..., description="Section 4: Successful competitor strategies")
    valuation_forensics: ValuationForensics = Field(..., description="Section 5: Valuation gap analysis")
    actionable_roadmap: ActionableRoadmap = Field(..., description="Section 6: Implementation recommendations")
    
    # Processing metadata
    processing_metadata: ProcessingMetadata = Field(..., description="Generation timing, costs, and quality metrics")
    
    class Config:
        schema_extra = {
            "example": {
                # Full example with all 6 sections populated
                # Based on WRB insurance example from plan
            }
        }
    
    @validator('competitive_dashboard')
    def validate_dashboard_peer_count(cls, v, values):
        """Ensure peer count consistency across sections"""
        # Cross-validate peer counts between sections
        return v
    
    @validator('valuation_forensics')
    def validate_gap_decomposition_math(cls, v):
        """Ensure valuation gap math is correct"""
        gap_decomp = v.gap_decomposition
        total_components = gap_decomp.fundamental_component + gap_decomp.narrative_component
        if abs(total_components - v.total_gap) > 0.01:
            raise ValueError("Gap decomposition components must sum to total gap")
        return v
```

---

## IMPLEMENTATION DELIVERABLES

### 🔄 **PARTIALLY COMPLETED**
- 🔄 Complete Pydantic model definitions in `src/metis/models/report_schema_v2.py` (simplified version exists)
- ✅ Comprehensive type hints and inline documentation

### ❌ **PENDING IMPLEMENTATION**
- ❌ Custom validators for business logic enforcement
- ❌ Model inheritance hierarchy for code reuse (pending full expansion)
- ❌ Full 6-section schema expansion per original RFC-001 specifications

---

## NEXT STEPS

1. **Expand Current Simplified Models**: Take the existing `report_schema_v2.py` and expand it with all 6 sections
2. **Add Custom Validators**: Implement business logic validation for cross-field relationships
3. **Create Model Hierarchy**: Organize models with proper inheritance for code reuse
4. **Integration Testing**: Ensure models work with existing test suite and JSON schema

---

## MANDATORY PROMPT INTEGRATION

**Agent Specialization for Narrative Sections:**
- ExecutiveSummaryAgent - Uses `prompts/narrative_generation/executive_summary.txt`
- HiddenStrengthsAgent - Uses `prompts/narrative_generation/hidden_strengths_identification.txt`
- MessagingStrategyAgent - Uses `prompts/narrative_generation/competitor_messaging_analysis.txt`
- ValuationForensicsAgent - Uses `prompts/valuation_analysis/valuation_gap_decomposition.txt`
- ActionableRoadmapAgent - Uses `prompts/narrative_generation/actionable_recommendations.txt`

**Prompt Loading Pattern**: All agents must use `PromptLoader` utility for file-based prompt management.