"""
Validation Models for Competitive Intelligence Reports

This module defines data structures for validation results, errors, and warnings
used throughout the schema validation process.
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues"""
    CRITICAL = "critical"  # Blocks report generation
    ERROR = "error"       # Significant issues that should be fixed
    WARNING = "warning"   # Minor issues that don't block generation
    INFO = "info"         # Informational messages


class ValidationCategory(str, Enum):
    """Categories of validation checks"""
    SCHEMA_COMPLIANCE = "schema_compliance"
    BUSINESS_RULES = "business_rules"
    CROSS_FIELD = "cross_field"
    DATA_QUALITY = "data_quality"
    COMPLETENESS = "completeness"
    NARRATIVE_CONTENT = "narrative_content"
    PROMPT_VALIDATION = "prompt_validation"


class ValidationIssue(BaseModel):
    """Individual validation issue"""
    severity: ValidationSeverity
    category: ValidationCategory
    code: str = Field(..., description="Unique error/warning code")
    message: str = Field(..., description="Human-readable issue description")
    field_path: Optional[str] = Field(None, description="JSON path to problematic field")
    expected_value: Optional[Union[str, int, float, bool]] = Field(None, description="Expected value if applicable")
    actual_value: Optional[Union[str, int, float, bool]] = Field(None, description="Actual value found")
    suggestion: Optional[str] = Field(None, description="Suggested fix for the issue")
    related_fields: Optional[List[str]] = Field(default_factory=list, description="Other fields related to this issue")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SectionValidationResult(BaseModel):
    """Validation result for a specific report section"""
    section_name: str
    is_valid: bool
    issues: List[ValidationIssue] = Field(default_factory=list)
    warnings_count: int = Field(default=0)
    errors_count: int = Field(default=0)
    critical_count: int = Field(default=0)
    
    def add_issue(self, issue: ValidationIssue) -> None:
        """Add a validation issue and update counters"""
        self.issues.append(issue)
        
        if issue.severity == ValidationSeverity.CRITICAL:
            self.critical_count += 1
            self.is_valid = False
        elif issue.severity == ValidationSeverity.ERROR:
            self.errors_count += 1
            self.is_valid = False
        elif issue.severity == ValidationSeverity.WARNING:
            self.warnings_count += 1


class ValidationResult(BaseModel):
    """Complete validation result for a report"""
    is_valid: bool = Field(default=True)
    timestamp: datetime = Field(default_factory=datetime.now)
    schema_version: str = Field(default="1.0")
    target_symbol: Optional[str] = None
    
    # Section-specific results
    section_results: Dict[str, SectionValidationResult] = Field(default_factory=dict)
    
    # Overall counters
    total_issues: int = Field(default=0)
    critical_count: int = Field(default=0)
    errors_count: int = Field(default=0)
    warnings_count: int = Field(default=0)
    info_count: int = Field(default=0)
    
    # Performance metrics
    validation_duration_ms: Optional[float] = None
    sections_validated: int = Field(default=0)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def add_section_result(self, section_result: SectionValidationResult) -> None:
        """Add section validation result and update overall counters"""
        self.section_results[section_result.section_name] = section_result
        self.sections_validated += 1
        
        # Update overall counters
        self.total_issues += len(section_result.issues)
        self.critical_count += section_result.critical_count
        self.errors_count += section_result.errors_count
        self.warnings_count += section_result.warnings_count
        
        # Update overall validity
        if not section_result.is_valid:
            self.is_valid = False
    
    def add_global_issue(self, issue: ValidationIssue) -> None:
        """Add a global validation issue (not section-specific)"""
        # Add to a special "global" section
        if "global" not in self.section_results:
            self.section_results["global"] = SectionValidationResult(
                section_name="global",
                is_valid=True
            )
        
        self.section_results["global"].add_issue(issue)
        self.total_issues += 1
        
        if issue.severity == ValidationSeverity.CRITICAL:
            self.critical_count += 1
            self.is_valid = False
        elif issue.severity == ValidationSeverity.ERROR:
            self.errors_count += 1
            self.is_valid = False
        elif issue.severity == ValidationSeverity.WARNING:
            self.warnings_count += 1
        elif issue.severity == ValidationSeverity.INFO:
            self.info_count += 1
    
    def get_issues_by_severity(self, severity: ValidationSeverity) -> List[ValidationIssue]:
        """Get all issues of a specific severity level"""
        issues = []
        for section_result in self.section_results.values():
            for issue in section_result.issues:
                if issue.severity == severity:
                    issues.append(issue)
        return issues
    
    def get_issues_by_category(self, category: ValidationCategory) -> List[ValidationIssue]:
        """Get all issues of a specific category"""
        issues = []
        for section_result in self.section_results.values():
            for issue in section_result.issues:
                if issue.category == category:
                    issues.append(issue)
        return issues
    
    def has_blocking_issues(self) -> bool:
        """Check if there are issues that would block report generation"""
        return self.critical_count > 0 or self.errors_count > 0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary for reporting"""
        return {
            "overall_valid": self.is_valid,
            "blocking_issues": self.has_blocking_issues(),
            "sections_validated": self.sections_validated,
            "issue_counts": {
                "critical": self.critical_count,
                "errors": self.errors_count,
                "warnings": self.warnings_count,
                "info": self.info_count,
                "total": self.total_issues
            },
            "performance": {
                "duration_ms": self.validation_duration_ms,
                "sections_per_second": (
                    self.sections_validated / (self.validation_duration_ms / 1000)
                    if self.validation_duration_ms and self.validation_duration_ms > 0
                    else None
                )
            },
            "timestamp": self.timestamp.isoformat()
        }


class DataQualityAssessment(BaseModel):
    """Assessment of data quality for report components"""
    completeness_score: float = Field(..., ge=0.0, le=100.0, description="Percentage of required data present")
    freshness_score: float = Field(..., ge=0.0, le=100.0, description="Recency of data used")
    accuracy_score: float = Field(..., ge=0.0, le=100.0, description="Estimated accuracy of calculations")
    consistency_score: float = Field(..., ge=0.0, le=100.0, description="Cross-field consistency")
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Weighted overall quality score")
    
    # Detailed metrics
    missing_data_points: int = Field(default=0)
    estimated_data_points: int = Field(default=0)
    stale_data_points: int = Field(default=0)
    outlier_data_points: int = Field(default=0)
    
    # Quality flags
    sufficient_for_analysis: bool = Field(default=True)
    confidence_level: str = Field(default="high", description="high|medium|low")
    quality_warnings: List[str] = Field(default_factory=list)


class PerformanceMetrics(BaseModel):
    """Performance metrics for validation process"""
    total_duration_ms: float
    section_durations: Dict[str, float] = Field(default_factory=dict)
    validation_rules_executed: int = Field(default=0)
    cache_hits: int = Field(default=0)
    cache_misses: int = Field(default=0)
    memory_usage_mb: Optional[float] = None
    
    def add_section_duration(self, section_name: str, duration_ms: float) -> None:
        """Add timing for a specific section"""
        self.section_durations[section_name] = duration_ms
    
    def get_slowest_sections(self, limit: int = 5) -> List[tuple]:
        """Get the slowest validation sections"""
        sorted_sections = sorted(
            self.section_durations.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_sections[:limit]


# Validation error codes for consistent error handling
class ValidationErrorCodes:
    """Standard error codes for validation issues"""
    
    # Schema compliance errors
    MISSING_REQUIRED_FIELD = "SCHEMA_001"
    INVALID_DATA_TYPE = "SCHEMA_002"
    INVALID_ENUM_VALUE = "SCHEMA_003"
    FIELD_OUT_OF_RANGE = "SCHEMA_004"
    
    # Business rule errors
    INVALID_CALCULATION = "BUSINESS_001"
    INCONSISTENT_RANKINGS = "BUSINESS_002"
    INVALID_PERCENTILE = "BUSINESS_003"
    VALUATION_GAP_MISMATCH = "BUSINESS_004"
    
    # Cross-field validation errors
    PEER_COUNT_MISMATCH = "CROSS_001"
    TIMESTAMP_INCONSISTENCY = "CROSS_002"
    SYMBOL_MISMATCH = "CROSS_003"
    RANKING_INCONSISTENCY = "CROSS_004"
    
    # Data quality errors
    INSUFFICIENT_DATA = "QUALITY_001"
    STALE_DATA = "QUALITY_002"
    OUTLIER_DATA = "QUALITY_003"
    MISSING_CALCULATION_COMPONENTS = "QUALITY_004"
    
    # Narrative content errors
    EMPTY_NARRATIVE = "NARRATIVE_001"
    NARRATIVE_TOO_SHORT = "NARRATIVE_002"
    NARRATIVE_TOO_LONG = "NARRATIVE_003"
    MISSING_RECOMMENDATIONS = "NARRATIVE_004"
    
    # Prompt validation errors
    PROMPT_FILE_NOT_FOUND = "PROMPT_001"
    MISSING_PROMPT_VARIABLES = "PROMPT_002"
    PROMPT_FORMATTING_ERROR = "PROMPT_003"