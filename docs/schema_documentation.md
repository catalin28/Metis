# Competitive Intelligence Report Schema Documentation

## Overview

This document provides comprehensive documentation for the Competitive Intelligence Report Schema v2.0, including field definitions, validation rules, usage examples, and implementation guidelines.

## Table of Contents

1. [Schema Overview](#schema-overview)
2. [Core Components](#core-components)
3. [Field Definitions](#field-definitions)
4. [Validation Rules](#validation-rules)
5. [Business Logic](#business-logic)
6. [Usage Examples](#usage-examples)
7. [Implementation Guide](#implementation-guide)
8. [Error Handling](#error-handling)
9. [Version History](#version-history)

## Schema Overview

The Competitive Intelligence Report Schema is designed to standardize the structure and validation of comprehensive competitive analysis reports. The schema supports:

- **Multi-company analysis** with target and peer companies
- **Financial metric comparisons** with ranking and analysis
- **Strategic recommendations** categorized by action type
- **Data quality assessment** and source tracking
- **Cross-field validation** for business logic consistency
- **Extensible design** for future enhancements

### Key Design Principles

1. **Sector Agnostic**: Works across all industries and business sectors
2. **Data Quality Focus**: Explicit tracking of data sources and quality indicators
3. **Validation Comprehensive**: Multi-level validation from schema to business rules
4. **API Ready**: JSON-first design optimized for API consumption
5. **Human Readable**: Clear field names and comprehensive documentation

## Core Components

### 1. Report Metadata
**Purpose**: Tracking and versioning information for the report
**Required Fields**: `target_symbol`, `generated_at`, `version`, `report_id`
**Optional Fields**: `processing_time_seconds`

### 2. Data Sources
**Purpose**: Documentation of all data sources used in analysis
**Validation**: Minimum 1 source required, maximum 50 sources
**Quality Tracking**: Explicit quality assessment for each source

### 3. Peer Group
**Purpose**: Target company profile and identified peer companies
**Discovery Methods**: Multiple algorithms supported for peer identification
**Validation**: Symbol uniqueness and sector consistency

### 4. Executive Summary
**Purpose**: High-level findings and strategic overview
**Structure**: Overview narrative, key insights (3-5), top recommendations (3-5)
**Length Limits**: Balanced between completeness and readability

### 5. Competitive Dashboard
**Purpose**: Quantitative metric comparisons and competitive positioning
**Components**: Metric comparisons, overall ranking, strengths/weaknesses
**Flexibility**: Supports any number of financial/operational metrics

### 6. Actionable Roadmap
**Purpose**: Specific, implementable strategic recommendations
**Categories**: DO (actions), SAY (messaging), SHOW (demonstrations)
**Requirements**: Minimum 5 recommendations with balanced category distribution

## Field Definitions

### ReportMetadata

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `target_symbol` | string | Yes | Primary company ticker symbol | Pattern: `^[A-Z]{1,5}$` |
| `generated_at` | datetime | Yes | Report generation timestamp | ISO 8601 format |
| `version` | string | Yes | Schema version | Pattern: `^\d+\.\d+$` |
| `report_id` | string | Yes | Unique report identifier | Length: 10-100 chars |
| `processing_time_seconds` | number | No | Generation time in seconds | Range: 0-3600 |

### DataSource

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `source_type` | enum | Yes | Type of data source | See DataSourceType enum |
| `provider` | string | Yes | Data provider name | Length: 1-100 chars |
| `quality` | enum | Yes | Data quality assessment | See DataQuality enum |
| `data_date` | datetime | No | Data point timestamp | ISO 8601 format |
| `coverage` | string | No | Coverage description | Max 200 chars |

#### DataSourceType Enum
- `financial_api`: Financial data APIs (FMP, Alpha Vantage, etc.)
- `earnings_transcript`: Earnings call transcripts
- `market_data`: Real-time market data feeds
- `analyst_report`: Professional analyst research
- `company_filing`: SEC filings and regulatory documents
- `news_article`: News and media sources
- `social_media`: Social media sentiment and mentions
- `alternative_data`: Alternative data sources (satellite, web scraping, etc.)

#### DataQuality Enum
- `VALID`: High-quality, recent, complete data
- `ESTIMATED`: Estimated or modeled data points
- `STALE`: Older data that may not reflect current conditions
- `INCOMPLETE`: Partial data with missing components
- `POOR`: Low-quality data with known issues

### CompanyProfile

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `symbol` | string | Yes | Company ticker symbol | Pattern: `^[A-Z]{1,5}$` |
| `company_name` | string | Yes | Official company name | Length: 1-200 chars |
| `sector` | string | Yes | Business sector | Length: 1-100 chars |
| `market_cap` | number/null | No | Market capitalization (USD) | Range: 0 to 10^13 |
| `pe_ratio` | number/null | No | Price-to-earnings ratio | Range: -100 to 1000 |
| `revenue_ttm` | number/null | No | Trailing 12-month revenue | Range: 0 to 10^12 |
| `similarity_score` | number/null | No | Similarity to target (peers only) | Range: 0-1 |

### MetricComparison

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `metric_name` | string | Yes | Name of compared metric | Length: 1-100 chars |
| `target_value` | number/null | Yes | Target company value | Any numeric value |
| `peer_values` | object | Yes | Peer company values | Keys: ticker symbols |
| `target_ranking` | integer/null | No | Target ranking (1=best) | Min: 1 |
| `analysis` | string | Yes | Metric analysis | Length: 20-1000 chars |

### Recommendation

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `title` | string | Yes | Recommendation summary | Length: 5-150 chars |
| `description` | string | Yes | Detailed description | Length: 20-2000 chars |
| `category` | enum | Yes | Action category | DO/SAY/SHOW |
| `priority` | enum | Yes | Priority level | HIGH/MEDIUM/LOW |
| `expected_impact` | string | Yes | Expected business impact | Length: 10-500 chars |
| `implementation_complexity` | enum | No | Complexity assessment | LOW/MEDIUM/HIGH |
| `estimated_cost` | enum | No | Cost estimate | LOW/MEDIUM/HIGH/VERY_HIGH |
| `timeframe` | enum | No | Implementation timeframe | IMMEDIATE/SHORT_TERM/MEDIUM_TERM/LONG_TERM |

#### RecommendationCategory Enum
- `DO`: Operational actions to take
- `SAY`: Messaging and communication strategies  
- `SHOW`: Demonstrations and showcasing opportunities

#### RecommendationPriority Enum
- `HIGH`: Critical recommendations requiring immediate attention
- `MEDIUM`: Important recommendations for near-term implementation
- `LOW`: Nice-to-have recommendations for longer-term consideration

## Validation Rules

### Schema Validation
1. **Required Fields**: All required fields must be present and non-null
2. **Type Validation**: Field values must match specified data types
3. **Format Validation**: String fields must match specified patterns/formats
4. **Range Validation**: Numeric fields must be within specified ranges
5. **Length Validation**: String fields must meet length requirements

### Business Rule Validation
1. **Symbol Consistency**: `metadata.target_symbol` must match `peer_group.target_company.symbol`
2. **Peer Uniqueness**: All peer symbols must be unique and different from target
3. **Ranking Consistency**: Rankings must be consistent with peer group size
4. **Category Distribution**: Recommendations should include mix of DO/SAY/SHOW categories
5. **Minimum Requirements**: Must have at least 1 data source, 1 peer, 5 recommendations

### Data Quality Validation
1. **Data Freshness**: Data sources should be recent (warning if >12 months old)
2. **Quality Flags**: Assessment of data quality indicators across sources
3. **Completeness**: Detection of missing critical financial metrics
4. **Outlier Detection**: Identification of extreme or unreasonable values
5. **Consistency**: Cross-validation of related metrics

### Cross-Field Validation
1. **Executive Summary Alignment**: Summary claims should align with dashboard rankings
2. **Recommendation Relevance**: Recommendations should address identified weaknesses
3. **Timeline Realism**: Implementation timeline should match recommendation complexity
4. **Success Metrics Alignment**: Success metrics should relate to recommendations
5. **Sector Consistency**: Peer companies should be in similar business sectors

## Business Logic

### Peer Discovery Logic
```python
def validate_peer_selection(target_company, peers):
    """Validate peer group composition"""
    # Check sector alignment
    target_sector = target_company.sector
    sector_mismatches = [p for p in peers if p.sector != target_sector]
    
    # Check market cap similarity (within 10x range recommended)
    if target_company.market_cap:
        cap_outliers = [p for p in peers 
                       if p.market_cap and 
                       (p.market_cap < target_company.market_cap / 10 or
                        p.market_cap > target_company.market_cap * 10)]
    
    # Return validation results
    return ValidationResult(
        issues=sector_mismatches + cap_outliers,
        severity=determine_severity(sector_mismatches, cap_outliers)
    )
```

### Recommendation Validation Logic
```python
def validate_recommendation_distribution(recommendations):
    """Ensure balanced recommendation categories"""
    categories = [r.category for r in recommendations]
    category_counts = {
        'DO': categories.count(RecommendationCategory.DO),
        'SAY': categories.count(RecommendationCategory.SAY),
        'SHOW': categories.count(RecommendationCategory.SHOW)
    }
    
    # Warn if any category is missing
    missing_categories = [cat for cat, count in category_counts.items() if count == 0]
    
    # Warn if distribution is heavily skewed (>80% in one category)
    total = len(recommendations)
    skewed = any(count / total > 0.8 for count in category_counts.values())
    
    return ValidationResult(
        issues=build_distribution_issues(missing_categories, skewed),
        severity=ValidationSeverity.WARNING if missing_categories or skewed else ValidationSeverity.INFO
    )
```

### Financial Metric Reasonableness
```python
def validate_financial_metrics(company_profile):
    """Check financial metric reasonableness"""
    issues = []
    
    # P/E ratio checks
    if company_profile.pe_ratio:
        if company_profile.pe_ratio < 0:
            issues.append("Negative P/E ratio may indicate losses")
        elif company_profile.pe_ratio > 100:
            issues.append("Extremely high P/E ratio (>100) may indicate data error")
    
    # Market cap vs revenue checks
    if company_profile.market_cap and company_profile.revenue_ttm:
        price_sales = company_profile.market_cap / company_profile.revenue_ttm
        if price_sales > 50:
            issues.append("Extremely high Price/Sales ratio may indicate growth stock or data error")
    
    return ValidationResult(
        issues=issues,
        severity=ValidationSeverity.WARNING if issues else ValidationSeverity.INFO
    )
```

## Usage Examples

### Creating a Complete Report
```python
from metis.reports.report_builder_v2 import CompetitiveIntelligenceReportBuilder
from metis.models.report_schema_v2 import *

# Initialize builder
builder = CompetitiveIntelligenceReportBuilder()

# Build complete report
report = (builder
    .set_metadata("AAPL", version="1.0")
    .add_data_source("financial_api", "FinancialModelingPrep", DataQuality.VALID)
    .set_target_company("AAPL", "Apple Inc.", "Technology", 3000000000000, 25.5)
    .add_peer_company("MSFT", "Microsoft Corporation", 0.85)
    .add_peer_company("GOOGL", "Alphabet Inc.", 0.78)
    .set_executive_summary(
        "Apple maintains strong competitive position...",
        ["Strong brand loyalty", "High margins", "Innovation leadership"],
        ["Expand AI", "Diversify supply chain", "Improve services"]
    )
    .add_metric_comparison("P/E Ratio", 25.5, {"MSFT": 28.2, "GOOGL": 22.1}, 2, "Apple discount")
    .set_competitive_dashboard(2, ["Brand strength"], ["China dependency"])
    .add_recommendation("Expand AI capabilities", "Integrate AI across products", 
                       RecommendationCategory.DO, RecommendationPriority.HIGH,
                       "Competitive advantage")
    # ... add 4 more recommendations for minimum requirement
    .build())

# Validate report
validation_result = builder.validate()
if validation_result.is_valid:
    print("Report is valid!")
else:
    print(f"Validation issues: {validation_result.issues}")
```

### JSON Serialization Example
```python
import json
from datetime import datetime

# Serialize to JSON
report_json = report.model_dump(mode='json')

# Pretty print
print(json.dumps(report_json, indent=2, default=str))

# Save to file
with open('competitive_analysis.json', 'w') as f:
    json.dump(report_json, f, indent=2, default=str)
```

### Loading and Validation
```python
from metis.models.validation_models import SchemaValidator

# Load from JSON
with open('competitive_analysis.json', 'r') as f:
    data = json.load(f)

# Parse and validate
try:
    report = CompetitiveIntelligenceReport.model_validate(data)
    
    # Additional business rule validation
    validator = SchemaValidator()
    validation_result = validator.validate_report(report)
    
    if validation_result.is_valid:
        print("Report loaded and validated successfully!")
    else:
        print(f"Validation warnings: {validation_result.issues}")
        
except ValidationError as e:
    print(f"Schema validation failed: {e}")
```

## Implementation Guide

### Setting Up Validation Pipeline
```python
from metis.models.validation_models import *

class ComprehensiveValidator:
    def __init__(self):
        self.schema_validator = SchemaValidator()
        self.business_validator = BusinessRuleValidator()
        self.quality_validator = DataQualityValidator()
        self.cross_validator = CrossFieldValidator()
    
    def validate_complete(self, report):
        """Run comprehensive validation pipeline"""
        results = []
        
        # Run all validators
        results.append(self.schema_validator.validate_report(report))
        results.append(self.business_validator.validate_business_rules(report))
        results.append(self.quality_validator.validate_data_quality(report))
        results.append(self.cross_validator.validate_cross_field_consistency(report))
        
        # Aggregate results
        return self.aggregate_validation_results(results)
    
    def aggregate_validation_results(self, results):
        """Combine multiple validation results"""
        all_issues = []
        max_severity = ValidationSeverity.INFO
        overall_valid = True
        
        for result in results:
            all_issues.extend(result.issues)
            if result.severity.value > max_severity.value:
                max_severity = result.severity
            if not result.is_valid:
                overall_valid = False
        
        return ValidationResult(
            is_valid=overall_valid,
            severity=max_severity,
            issues=all_issues,
            validation_time=sum(r.validation_time for r in results)
        )
```

### Custom Validation Rules
```python
class CustomBusinessValidator(BusinessRuleValidator):
    def validate_sector_specific_rules(self, report):
        """Add sector-specific validation rules"""
        issues = []
        
        if report.peer_group.target_company.sector == "Technology":
            # Technology-specific validations
            if report.peer_group.target_company.pe_ratio and report.peer_group.target_company.pe_ratio < 10:
                issues.append("Technology companies typically have higher P/E ratios")
        
        elif report.peer_group.target_company.sector == "Utilities":
            # Utility-specific validations
            if report.peer_group.target_company.pe_ratio and report.peer_group.target_company.pe_ratio > 25:
                issues.append("Utilities typically have lower P/E ratios")
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            severity=ValidationSeverity.WARNING if issues else ValidationSeverity.INFO,
            issues=issues
        )
```

### Performance Optimization
```python
from functools import lru_cache
import hashlib

class CachedValidator:
    def __init__(self):
        self.validator = SchemaValidator()
    
    @lru_cache(maxsize=1000)
    def validate_cached(self, report_hash):
        """Cache validation results by report hash"""
        # This would need to be implemented with proper cache invalidation
        pass
    
    def get_report_hash(self, report):
        """Generate hash of report for caching"""
        report_json = report.model_dump_json()
        return hashlib.sha256(report_json.encode()).hexdigest()
```

## Error Handling

### Common Validation Errors

#### Schema Validation Errors
```python
# Missing required field
{
    "error": "ValidationError",
    "message": "Field required",
    "field": "metadata.target_symbol",
    "type": "missing"
}

# Invalid data type
{
    "error": "ValidationError", 
    "message": "Input should be a valid number",
    "field": "peer_group.target_company.market_cap",
    "type": "float_parsing"
}

# Pattern validation failure
{
    "error": "ValidationError",
    "message": "String should match pattern '^[A-Z]{1,5}$'",
    "field": "metadata.target_symbol",
    "type": "string_pattern_mismatch"
}
```

#### Business Rule Validation Errors
```python
# Symbol consistency failure
{
    "error": "BusinessRuleViolation",
    "message": "Target symbol mismatch: metadata has 'AAPL' but peer_group has 'MSFT'",
    "rule": "symbol_consistency",
    "severity": "ERROR"
}

# Insufficient recommendations
{
    "error": "BusinessRuleViolation",
    "message": "At least 5 recommendations are required, found 3",
    "rule": "minimum_recommendations",
    "severity": "ERROR"
}
```

#### Data Quality Warnings
```python
# Stale data warning
{
    "error": "DataQualityIssue",
    "message": "Data source 'financial_api' is 18 months old",
    "source": "FinancialModelingPrep",
    "severity": "WARNING"
}

# Missing financial data
{
    "error": "DataQualityIssue",
    "message": "Missing critical financial metrics for peer MSFT",
    "field": "peer_group.peers[0].pe_ratio",
    "severity": "WARNING"
}
```

### Error Recovery Strategies

#### Graceful Degradation
```python
def build_report_with_fallbacks(builder):
    """Build report with fallback strategies for missing data"""
    try:
        return builder.build()
    except ValidationError as e:
        if "recommendations" in str(e):
            # Add default recommendations to meet minimum
            builder.add_default_recommendations()
            return builder.build()
        elif "data_sources" in str(e):
            # Add fallback data source
            builder.add_data_source("fallback", "Manual Analysis", DataQuality.ESTIMATED)
            return builder.build()
        else:
            raise
```

#### Partial Report Generation
```python
def generate_partial_report(builder):
    """Generate partial report when full validation fails"""
    try:
        return builder.build()
    except ValidationError:
        # Return partial report with disclaimers
        return builder.build_partial()
```

## Version History

### Version 2.0 (Current)
- **Released**: January 2024
- **Changes**:
  - Complete rewrite using Pydantic v2
  - Enhanced validation framework with multi-level validation
  - Added comprehensive business rule validation
  - Expanded data quality tracking
  - Added cross-field consistency validation
  - Improved JSON schema specification
  - Added fluent API report builder

### Version 1.0 (Legacy)
- **Released**: October 2023  
- **Changes**:
  - Initial schema design
  - Basic field validation
  - Simple JSON structure
  - Limited business rule validation

### Migration Guide (v1.0 → v2.0)

#### Breaking Changes
1. **Field Renames**: Some fields renamed for clarity
2. **Type Changes**: Some fields changed from string to enum
3. **Validation**: Stricter validation rules
4. **Structure**: Flattened some nested structures

#### Migration Script
```python
def migrate_v1_to_v2(v1_report):
    """Migrate v1 report to v2 schema"""
    # Handle field renames
    if 'company_symbol' in v1_report['metadata']:
        v1_report['metadata']['target_symbol'] = v1_report['metadata'].pop('company_symbol')
    
    # Convert string enums to proper enums
    for source in v1_report.get('data_sources', []):
        if source.get('quality') == 'good':
            source['quality'] = 'VALID'
        elif source.get('quality') == 'poor':
            source['quality'] = 'POOR'
    
    # Validate and return v2 report
    return CompetitiveIntelligenceReport.model_validate(v1_report)
```

## Best Practices

### Data Collection
1. **Multiple Sources**: Use multiple data sources for critical metrics
2. **Quality Assessment**: Always assess and document data quality
3. **Freshness**: Prefer recent data, flag stale information
4. **Completeness**: Ensure core financial metrics are available

### Peer Selection
1. **Sector Focus**: Primary focus on same-sector companies
2. **Size Similarity**: Market cap within reasonable range (2-10x)
3. **Business Model**: Consider business model similarities
4. **Geographic Scope**: Account for geographic market differences

### Recommendation Development
1. **Specificity**: Make recommendations specific and actionable
2. **Balance**: Include mix of DO/SAY/SHOW categories
3. **Prioritization**: Clear priority levels with justification
4. **Impact**: Quantify expected business impact where possible

### Validation Strategy
1. **Comprehensive**: Run all validation levels
2. **Early Validation**: Validate during construction, not just at end
3. **User Feedback**: Provide clear, actionable validation messages
4. **Performance**: Cache validation results for repeated reports

---

*This documentation is maintained alongside the schema and updated with each release. For technical support or questions, please refer to the development team.*