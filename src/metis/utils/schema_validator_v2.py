"""
Simplified Schema Validator for Competitive Intelligence Reports (v2)

This module implements basic validation for competitive intelligence reports.
"""

from typing import List
from datetime import datetime

from ..models.validation_models import (
    ValidationResult,
    ValidationSeverity,
    ValidationIssue,
    ValidationCategory
)
from ..models.report_schema_v2 import (
    CompetitiveIntelligenceReport,
    DataQuality
)


class CompetitiveIntelligenceReportValidator:
    """
    Simplified validator for competitive intelligence reports.
    """
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize validator with configuration options.
        
        Args:
            strict_mode: If True, treats warnings as errors
        """
        self.strict_mode = strict_mode
    
    def validate_report(self, report: CompetitiveIntelligenceReport) -> ValidationResult:
        """
        Validate a complete competitive intelligence report.
        
        Args:
            report: The report to validate
            
        Returns:
            ValidationResult: Comprehensive validation results
        """
        issues = []
        
        # Basic structure validation
        issues.extend(self._validate_metadata(report))
        issues.extend(self._validate_peer_group(report))
        issues.extend(self._validate_executive_summary(report))
        issues.extend(self._validate_recommendations(report))
        
        # Determine overall severity
        if any(issue.severity == ValidationSeverity.ERROR for issue in issues):
            overall_severity = ValidationSeverity.ERROR
        elif any(issue.severity == ValidationSeverity.WARNING for issue in issues):
            overall_severity = ValidationSeverity.WARNING
        else:
            overall_severity = ValidationSeverity.INFO
        
        # In strict mode, warnings become errors
        if self.strict_mode and overall_severity == ValidationSeverity.WARNING:
            overall_severity = ValidationSeverity.ERROR
        
        is_valid = overall_severity != ValidationSeverity.ERROR
        
        return ValidationResult(
            is_valid=is_valid,
            severity=overall_severity,
            issues=[issue.message for issue in issues],
            details={
                'total_issues': len(issues),
                'errors': len([i for i in issues if i.severity == ValidationSeverity.ERROR]),
                'warnings': len([i for i in issues if i.severity == ValidationSeverity.WARNING]),
                'validated_at': datetime.now().isoformat()
            }
        )
    
    def _validate_metadata(self, report: CompetitiveIntelligenceReport) -> List[ValidationIssue]:
        """Validate report metadata"""
        issues = []
        
        if not report.metadata.target_symbol:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.SCHEMA_COMPLIANCE,
                code="MISSING_TARGET_SYMBOL",
                message="Target symbol is required"
            ))
        
        if len(report.metadata.target_symbol) > 5:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.DATA_QUALITY,
                code="LONG_SYMBOL",
                message="Target symbol is unusually long"
            ))
        
        return issues
    
    def _validate_peer_group(self, report: CompetitiveIntelligenceReport) -> List[ValidationIssue]:
        """Validate peer group information"""
        issues = []
        
        if len(report.peer_group.peers) == 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="At least one peer company is required"
            ))
        
        if len(report.peer_group.peers) > 10:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="More than 10 peers may indicate poor peer selection"
            ))
        
        # Check for symbol consistency
        target_symbol = report.metadata.target_symbol
        if report.peer_group.target_company.symbol != target_symbol:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"Target symbol mismatch: {target_symbol} vs {report.peer_group.target_company.symbol}"
            ))
        
        return issues
    
    def _validate_executive_summary(self, report: CompetitiveIntelligenceReport) -> List[ValidationIssue]:
        """Validate executive summary"""
        issues = []
        
        if len(report.executive_summary.key_insights) < 3:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="At least 3 key insights are required"
            ))
        
        if len(report.executive_summary.top_recommendations) < 3:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="At least 3 top recommendations are required"
            ))
        
        if len(report.executive_summary.overview) < 100:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Executive summary overview is quite brief"
            ))
        
        return issues
    
    def _validate_recommendations(self, report: CompetitiveIntelligenceReport) -> List[ValidationIssue]:
        """Validate actionable recommendations"""
        issues = []
        
        recommendations = report.actionable_roadmap.recommendations
        
        if len(recommendations) < 5:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="At least 5 recommendations are required"
            ))
        
        # Check for category distribution
        categories = [rec.category for rec in recommendations]
        from ..models.report_schema_v2 import RecommendationCategory
        
        if RecommendationCategory.DO not in categories:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Missing 'DO' category recommendations"
            ))
        
        if RecommendationCategory.SAY not in categories:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Missing 'SAY' category recommendations"
            ))
        
        if RecommendationCategory.SHOW not in categories:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Missing 'SHOW' category recommendations"
            ))
        
        return issues


# Export main class
__all__ = ['CompetitiveIntelligenceReportValidator']