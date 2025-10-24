"""
Comprehensive Schema Validator for Competitive Intelligence Reports

This module implements multi-level validation for competitive intelligence reports,
ensuring data quality, business rule compliance, and schema adherence.
"""

import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import statistics
from pathlib import Path

from .validation_models import (
    ValidationResult, 
    SectionValidationResult, 
    ValidationIssue, 
    ValidationSeverity, 
    ValidationCategory,
    ValidationErrorCodes,
    DataQualityAssessment,
    PerformanceMetrics
)
from ..models.report_schema_v2 import (
    CompetitiveIntelligenceReport,
    DataQuality,
    MarketPerceptionCategory,
    Priority
)


class CompetitiveIntelligenceReportValidator:
    """
    Comprehensive validator for competitive intelligence reports.
    
    Implements multi-level validation:
    1. Schema Compliance: Structure and type checking
    2. Business Rules: Mathematical relationships and logic
    3. Cross-Field Validation: Consistency across sections
    4. Data Quality: Completeness and freshness checks
    """
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize validator with configuration options.
        
        Args:
            strict_mode: If True, treats warnings as errors
        """
        self.strict_mode = strict_mode
        self.performance_metrics = PerformanceMetrics(total_duration_ms=0)
        
    def validate_report(self, report: Union[CompetitiveIntelligenceReport, Dict[str, Any]]) -> ValidationResult:
        """
        Validate complete competitive intelligence report.
        
        Args:
            report: Report to validate (Pydantic model or dict)
            
        Returns:
            Comprehensive validation result
        """
        start_time = time.time()
        
        # Initialize result
        result = ValidationResult()
        
        try:
            # Convert dict to Pydantic model if needed
            if isinstance(report, dict):
                try:
                    report = CompetitiveIntelligenceReport(**report)
                except Exception as e:
                    result.add_global_issue(ValidationIssue(
                        severity=ValidationSeverity.CRITICAL,
                        category=ValidationCategory.SCHEMA_COMPLIANCE,
                        code=ValidationErrorCodes.INVALID_DATA_TYPE,
                        message=f"Failed to parse report structure: {str(e)}",
                        suggestion="Check report structure matches expected schema"
                    ))
                    return result
            
            result.target_symbol = report.report_metadata.target_symbol
            result.schema_version = report.report_metadata.schema_version
            
            # Validate each section
            self._validate_report_metadata(report.report_metadata, result)
            self._validate_company_profile(report.company_profile, result)
            self._validate_peer_group(report.peer_group, result)
            self._validate_executive_summary(report.executive_summary, result)
            self._validate_competitive_dashboard(report.competitive_dashboard, result)
            self._validate_hidden_strengths(report.hidden_strengths, result)
            self._validate_steal_their_playbook(report.steal_their_playbook, result)
            self._validate_valuation_forensics(report.valuation_forensics, result)
            self._validate_actionable_roadmap(report.actionable_roadmap, result)
            
            # Cross-section validation
            self._validate_cross_references(report, result)
            
            # Business rule validation
            self._validate_business_rules(report, result)
            
            # Data quality assessment
            self._assess_data_quality(report, result)
            
        except Exception as e:
            result.add_global_issue(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category=ValidationCategory.SCHEMA_COMPLIANCE,
                code="VALIDATION_ERROR",
                message=f"Unexpected validation error: {str(e)}",
                suggestion="Check report format and try again"
            ))
        
        # Record performance metrics
        end_time = time.time()
        result.validation_duration_ms = (end_time - start_time) * 1000
        
        return result
    
    def validate_section(self, section_name: str, section_data: Any) -> SectionValidationResult:
        """
        Validate individual report section.
        
        Args:
            section_name: Name of the section
            section_data: Section data to validate
            
        Returns:
            Section-specific validation result
        """
        start_time = time.time()
        section_result = SectionValidationResult(section_name=section_name, is_valid=True)
        
        try:
            validator_method = getattr(self, f'_validate_{section_name}', None)
            if validator_method:
                # Create temporary result to capture issues
                temp_result = ValidationResult()
                validator_method(section_data, temp_result)
                
                # Transfer issues to section result
                if section_name in temp_result.section_results:
                    section_result = temp_result.section_results[section_name]
            else:
                section_result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category=ValidationCategory.SCHEMA_COMPLIANCE,
                    code="UNKNOWN_SECTION",
                    message=f"No validator found for section: {section_name}",
                    suggestion="Check section name spelling"
                ))
        
        except Exception as e:
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.SCHEMA_COMPLIANCE,
                code="SECTION_VALIDATION_ERROR",
                message=f"Error validating section {section_name}: {str(e)}"
            ))
        
        # Record timing
        duration_ms = (time.time() - start_time) * 1000
        self.performance_metrics.add_section_duration(section_name, duration_ms)
        
        return section_result
    
    def _validate_report_metadata(self, metadata: Any, result: ValidationResult) -> None:
        """Validate report metadata section"""
        section_result = SectionValidationResult(section_name="report_metadata", is_valid=True)
        
        # Check required fields
        if not metadata.target_symbol:
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category=ValidationCategory.SCHEMA_COMPLIANCE,
                code=ValidationErrorCodes.MISSING_REQUIRED_FIELD,
                message="Target symbol is required",
                field_path="report_metadata.target_symbol"
            ))
        
        if not metadata.client_id:
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category=ValidationCategory.SCHEMA_COMPLIANCE,
                code=ValidationErrorCodes.MISSING_REQUIRED_FIELD,
                message="Client ID is required",
                field_path="report_metadata.client_id"
            ))
        
        # Validate schema version
        if metadata.schema_version not in ["1.0", "1.1"]:
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.SCHEMA_COMPLIANCE,
                code="UNSUPPORTED_SCHEMA_VERSION",
                message=f"Schema version {metadata.schema_version} may not be fully supported",
                field_path="report_metadata.schema_version",
                suggestion="Use schema version 1.0 or 1.1"
            ))
        
        # Check generation timestamp
        if metadata.generated_at > datetime.now():
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.DATA_QUALITY,
                code="FUTURE_TIMESTAMP",
                message="Report generation timestamp is in the future",
                field_path="report_metadata.generated_at"
            ))
        
        result.add_section_result(section_result)
    
    def _validate_company_profile(self, profile: Any, result: ValidationResult) -> None:
        """Validate company profile section"""
        section_result = SectionValidationResult(section_name="company_profile", is_valid=True)
        
        # Validate market cap
        if profile.market_cap_billions <= 0:
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.BUSINESS_RULES,
                code=ValidationErrorCodes.FIELD_OUT_OF_RANGE,
                message="Market cap must be positive",
                field_path="company_profile.market_cap_billions",
                actual_value=profile.market_cap_billions
            ))
        
        # Check for reasonable market cap range (mid-cap focus)
        if profile.market_cap_billions < 2.0 or profile.market_cap_billions > 200.0:
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.DATA_QUALITY,
                code="UNUSUAL_MARKET_CAP",
                message=f"Market cap ${profile.market_cap_billions:.1f}B outside typical mid-cap range",
                field_path="company_profile.market_cap_billions",
                suggestion="Verify market cap calculation and currency"
            ))
        
        # Validate data freshness
        if hasattr(profile, 'calculation_date'):
            days_old = (datetime.now() - profile.calculation_date).days
            if days_old > 30:
                section_result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category=ValidationCategory.DATA_QUALITY,
                    code=ValidationErrorCodes.STALE_DATA,
                    message=f"Company profile data is {days_old} days old",
                    field_path="company_profile.calculation_date",
                    suggestion="Update with more recent data"
                ))
        
        result.add_section_result(section_result)
    
    def _validate_peer_group(self, peer_group: Any, result: ValidationResult) -> None:
        """Validate peer group section"""
        section_result = SectionValidationResult(section_name="peer_group", is_valid=True)
        
        # Check peer count
        peer_count = len(peer_group.peers)
        if peer_count < 3:
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category=ValidationCategory.BUSINESS_RULES,
                code=ValidationErrorCodes.INSUFFICIENT_DATA,
                message=f"Insufficient peers for analysis: {peer_count} (minimum 3)",
                field_path="peer_group.peers",
                suggestion="Add more peer companies for reliable analysis"
            ))
        
        if peer_count > 10:
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.BUSINESS_RULES,
                code="TOO_MANY_PEERS",
                message=f"Large peer group may dilute analysis: {peer_count} peers",
                field_path="peer_group.peers",
                suggestion="Consider focusing on most relevant peers"
            ))
        
        # Validate peer similarity scores
        similarity_scores = [peer.similarity_score for peer in peer_group.peers]
        avg_similarity = statistics.mean(similarity_scores)
        
        if avg_similarity < 60.0:
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.DATA_QUALITY,
                code="LOW_PEER_SIMILARITY",
                message=f"Low average peer similarity: {avg_similarity:.1f}%",
                field_path="peer_group.peers",
                suggestion="Review peer selection criteria"
            ))
        
        # Check for duplicate symbols
        symbols = [peer.symbol for peer in peer_group.peers]
        if len(symbols) != len(set(symbols)):
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.BUSINESS_RULES,
                code="DUPLICATE_PEERS",
                message="Duplicate peer symbols found",
                field_path="peer_group.peers"
            ))
        
        result.add_section_result(section_result)
    
    def _validate_competitive_dashboard(self, dashboard: Any, result: ValidationResult) -> None:
        """Validate competitive dashboard section"""
        section_result = SectionValidationResult(section_name="competitive_dashboard", is_valid=True)
        
        # Check company count
        company_count = len(dashboard.companies)
        expected_count = len(result.section_results.get("peer_group", {}).get("peers", [])) + 1
        
        if company_count < 4:
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.COMPLETENESS,
                code=ValidationErrorCodes.INSUFFICIENT_DATA,
                message=f"Insufficient companies in dashboard: {company_count}",
                field_path="competitive_dashboard.companies"
            ))
        
        # Validate metrics for each company
        for i, company in enumerate(dashboard.companies):
            self._validate_dashboard_company(company, i, section_result)
        
        # Validate ranking consistency
        self._validate_dashboard_rankings(dashboard.companies, section_result)
        
        # Check summary statistics
        if dashboard.summary_statistics.peer_count != company_count - 1:
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.CROSS_FIELD,
                code=ValidationErrorCodes.PEER_COUNT_MISMATCH,
                message="Summary statistics peer count doesn't match dashboard",
                field_path="competitive_dashboard.summary_statistics.peer_count"
            ))
        
        result.add_section_result(section_result)
    
    def _validate_dashboard_company(self, company: Any, index: int, section_result: SectionValidationResult) -> None:
        """Validate individual company in dashboard"""
        prefix = f"competitive_dashboard.companies[{index}]"
        
        # Validate P/E ratio
        if company.pe_ratio <= 0:
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.BUSINESS_RULES,
                code=ValidationErrorCodes.FIELD_OUT_OF_RANGE,
                message=f"Invalid P/E ratio for {company.symbol}: {company.pe_ratio}",
                field_path=f"{prefix}.pe_ratio"
            ))
        
        if company.pe_ratio > 100:
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.DATA_QUALITY,
                code=ValidationErrorCodes.OUTLIER_DATA,
                message=f"Extremely high P/E ratio for {company.symbol}: {company.pe_ratio}",
                field_path=f"{prefix}.pe_ratio",
                suggestion="Verify earnings and stock price data"
            ))
        
        # Validate ROE
        if company.roe_percentage < -100 or company.roe_percentage > 200:
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.DATA_QUALITY,
                code=ValidationErrorCodes.OUTLIER_DATA,
                message=f"Unusual ROE for {company.symbol}: {company.roe_percentage}%",
                field_path=f"{prefix}.roe_percentage"
            ))
        
        # Validate combined ratio (insurance specific)
        if company.combined_ratio and (company.combined_ratio < 50 or company.combined_ratio > 150):
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.DATA_QUALITY,
                code=ValidationErrorCodes.OUTLIER_DATA,
                message=f"Unusual combined ratio for {company.symbol}: {company.combined_ratio}",
                field_path=f"{prefix}.combined_ratio"
            ))
        
        # Validate sentiment scores
        if not (0 <= company.management_sentiment_score <= 100):
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.BUSINESS_RULES,
                code=ValidationErrorCodes.FIELD_OUT_OF_RANGE,
                message=f"Management sentiment score out of range: {company.management_sentiment_score}",
                field_path=f"{prefix}.management_sentiment_score"
            ))
        
        if not (0 <= company.analyst_confusion_score <= 100):
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.BUSINESS_RULES,
                code=ValidationErrorCodes.FIELD_OUT_OF_RANGE,
                message=f"Analyst confusion score out of range: {company.analyst_confusion_score}",
                field_path=f"{prefix}.analyst_confusion_score"
            ))
    
    def _validate_dashboard_rankings(self, companies: List[Any], section_result: SectionValidationResult) -> None:
        """Validate ranking consistency across dashboard companies"""
        company_count = len(companies)
        
        # Check overall rankings
        overall_ranks = [comp.overall_rank for comp in companies]
        expected_ranks = set(range(1, company_count + 1))
        actual_ranks = set(overall_ranks)
        
        if actual_ranks != expected_ranks:
            missing = expected_ranks - actual_ranks
            extra = actual_ranks - expected_ranks
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.BUSINESS_RULES,
                code=ValidationErrorCodes.INCONSISTENT_RANKINGS,
                message=f"Ranking inconsistency - Missing: {missing}, Extra: {extra}",
                field_path="competitive_dashboard.companies.overall_rank"
            ))
        
        # Check for ranking duplicates
        if len(overall_ranks) != len(set(overall_ranks)):
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.BUSINESS_RULES,
                code=ValidationErrorCodes.INCONSISTENT_RANKINGS,
                message="Duplicate overall rankings found",
                field_path="competitive_dashboard.companies.overall_rank"
            ))
    
    def _validate_valuation_forensics(self, valuation: Any, result: ValidationResult) -> None:
        """Validate valuation forensics section"""
        section_result = SectionValidationResult(section_name="valuation_forensics", is_valid=True)
        
        # Validate P/E consistency
        calculated_gap = valuation.current_pe - valuation.peer_average_pe
        if abs(calculated_gap - valuation.total_gap) > 0.01:
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.BUSINESS_RULES,
                code=ValidationErrorCodes.VALUATION_GAP_MISMATCH,
                message=f"Total gap ({valuation.total_gap}) doesn't match calculated gap ({calculated_gap:.2f})",
                field_path="valuation_forensics.total_gap"
            ))
        
        # Validate gap decomposition
        gap_sum = valuation.gap_decomposition.fundamental_component + valuation.gap_decomposition.narrative_component
        if abs(gap_sum - valuation.total_gap) > 0.01:
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.BUSINESS_RULES,
                code=ValidationErrorCodes.VALUATION_GAP_MISMATCH,
                message="Gap decomposition components don't sum to total gap",
                field_path="valuation_forensics.gap_decomposition"
            ))
        
        # Validate valuation bridge
        bridge_components = valuation.valuation_bridge.components
        if len(bridge_components) < 3:
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.COMPLETENESS,
                code="INSUFFICIENT_BRIDGE_COMPONENTS",
                message="Valuation bridge should have at least 3 components",
                field_path="valuation_forensics.valuation_bridge.components"
            ))
        
        # Validate bridge cumulative values
        for i, component in enumerate(bridge_components):
            if i == 0:
                # First component should match peer average
                if abs(component.cumulative - valuation.peer_average_pe) > 0.01:
                    section_result.add_issue(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.BUSINESS_RULES,
                        code="BRIDGE_START_MISMATCH",
                        message="Bridge starting point doesn't match peer average P/E",
                        field_path=f"valuation_forensics.valuation_bridge.components[{i}].cumulative"
                    ))
        
        # Last component should match current P/E
        if bridge_components:
            last_cumulative = bridge_components[-1].cumulative
            if abs(last_cumulative - valuation.current_pe) > 0.01:
                section_result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.BUSINESS_RULES,
                    code="BRIDGE_END_MISMATCH",
                    message="Bridge ending point doesn't match current P/E",
                    field_path="valuation_forensics.valuation_bridge.components[-1].cumulative"
                ))
        
        result.add_section_result(section_result)
    
    def _validate_executive_summary(self, summary: Any, result: ValidationResult) -> None:
        """Validate executive summary section"""
        section_result = SectionValidationResult(section_name="executive_summary", is_valid=True)
        
        # Check narrative lengths
        if len(summary.company_overview) < 200:
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.NARRATIVE_CONTENT,
                code=ValidationErrorCodes.NARRATIVE_TOO_SHORT,
                message=f"Company overview too short: {len(summary.company_overview)} characters",
                field_path="executive_summary.company_overview",
                suggestion="Expand to at least 200 characters"
            ))
        
        if len(summary.key_finding) < 100:
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.NARRATIVE_CONTENT,
                code=ValidationErrorCodes.NARRATIVE_TOO_SHORT,
                message="Key finding too brief",
                field_path="executive_summary.key_finding"
            ))
        
        # Check recommendations count
        if len(summary.top_recommendations) < 3:
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.COMPLETENESS,
                code=ValidationErrorCodes.MISSING_RECOMMENDATIONS,
                message="Need at least 3 top recommendations",
                field_path="executive_summary.top_recommendations"
            ))
        
        result.add_section_result(section_result)
    
    def _validate_hidden_strengths(self, strengths: Any, result: ValidationResult) -> None:
        """Validate hidden strengths section"""
        section_result = SectionValidationResult(section_name="hidden_strengths", is_valid=True)
        
        if len(strengths.strengths) < 3:
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.COMPLETENESS,
                code="INSUFFICIENT_STRENGTHS",
                message="Should identify at least 3 hidden strengths",
                field_path="hidden_strengths.strengths"
            ))
        
        result.add_section_result(section_result)
    
    def _validate_steal_their_playbook(self, playbook: Any, result: ValidationResult) -> None:
        """Validate steal their playbook section"""
        section_result = SectionValidationResult(section_name="steal_their_playbook", is_valid=True)
        
        if len(playbook.competitor_strategies) < 2:
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.COMPLETENESS,
                code="INSUFFICIENT_STRATEGIES",
                message="Should analyze at least 2 competitor strategies",
                field_path="steal_their_playbook.competitor_strategies"
            ))
        
        result.add_section_result(section_result)
    
    def _validate_actionable_roadmap(self, roadmap: Any, result: ValidationResult) -> None:
        """Validate actionable roadmap section"""
        section_result = SectionValidationResult(section_name="actionable_roadmap", is_valid=True)
        
        if len(roadmap.recommendations) < 10:
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.COMPLETENESS,
                code=ValidationErrorCodes.MISSING_RECOMMENDATIONS,
                message=f"Insufficient recommendations: {len(roadmap.recommendations)} (minimum 10)",
                field_path="actionable_roadmap.recommendations"
            ))
        
        # Check priority distribution
        priorities = [rec.priority for rec in roadmap.recommendations]
        high_count = priorities.count(Priority.HIGH)
        total_count = len(priorities)
        
        if high_count > total_count * 0.4:
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.BUSINESS_RULES,
                code="TOO_MANY_HIGH_PRIORITY",
                message=f"Too many high priority recommendations: {high_count}/{total_count}",
                field_path="actionable_roadmap.recommendations",
                suggestion="Limit high priority recommendations to 40% of total"
            ))
        
        result.add_section_result(section_result)
    
    def _validate_cross_references(self, report: Any, result: ValidationResult) -> None:
        """Validate cross-reference consistency across sections"""
        section_result = SectionValidationResult(section_name="cross_references", is_valid=True)
        
        target_symbol = report.report_metadata.target_symbol
        
        # Check symbol consistency
        if report.company_profile.symbol != target_symbol:
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.CROSS_FIELD,
                code=ValidationErrorCodes.SYMBOL_MISMATCH,
                message="Company profile symbol doesn't match report target",
                field_path="company_profile.symbol"
            ))
        
        if report.peer_group.target_symbol != target_symbol:
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.CROSS_FIELD,
                code=ValidationErrorCodes.SYMBOL_MISMATCH,
                message="Peer group target symbol doesn't match report target",
                field_path="peer_group.target_symbol"
            ))
        
        # Check target company in dashboard
        dashboard_symbols = [comp.symbol for comp in report.competitive_dashboard.companies]
        if target_symbol not in dashboard_symbols:
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.CROSS_FIELD,
                code="TARGET_NOT_IN_DASHBOARD",
                message="Target company not found in competitive dashboard",
                field_path="competitive_dashboard.companies"
            ))
        
        result.add_section_result(section_result)
    
    def _validate_business_rules(self, report: Any, result: ValidationResult) -> None:
        """Validate business logic and mathematical relationships"""
        section_result = SectionValidationResult(section_name="business_rules", is_valid=True)
        
        # Validate peer count consistency
        peer_count = len(report.peer_group.peers)
        dashboard_company_count = len(report.competitive_dashboard.companies)
        
        if dashboard_company_count != peer_count + 1:  # +1 for target company
            section_result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.BUSINESS_RULES,
                code=ValidationErrorCodes.PEER_COUNT_MISMATCH,
                message=f"Dashboard companies ({dashboard_company_count}) != peers ({peer_count}) + target (1)",
                field_path="peer_group.peers"
            ))
        
        result.add_section_result(section_result)
    
    def _assess_data_quality(self, report: Any, result: ValidationResult) -> None:
        """Assess overall data quality of the report"""
        # Calculate quality metrics
        total_companies = len(report.competitive_dashboard.companies)
        valid_companies = sum(1 for comp in report.competitive_dashboard.companies 
                            if comp.data_quality == DataQuality.VALID)
        
        completeness_score = (valid_companies / total_companies) * 100 if total_companies > 0 else 0
        
        # Add data quality assessment to result
        quality_assessment = DataQualityAssessment(
            completeness_score=completeness_score,
            freshness_score=self._calculate_freshness_score(report),
            accuracy_score=self._calculate_accuracy_score(report),
            consistency_score=self._calculate_consistency_score(report),
            overall_score=(completeness_score + 90 + 85 + 95) / 4,  # Placeholder calculation
            sufficient_for_analysis=completeness_score >= 80
        )
        
        # Add quality issues if needed
        if completeness_score < 80:
            result.add_global_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.DATA_QUALITY,
                code=ValidationErrorCodes.INSUFFICIENT_DATA,
                message=f"Data completeness below threshold: {completeness_score:.1f}%",
                suggestion="Review data collection and improve coverage"
            ))
    
    def _calculate_freshness_score(self, report: Any) -> float:
        """Calculate data freshness score"""
        # Placeholder implementation
        return 90.0
    
    def _calculate_accuracy_score(self, report: Any) -> float:
        """Calculate data accuracy score"""
        # Placeholder implementation
        return 85.0
    
    def _calculate_consistency_score(self, report: Any) -> float:
        """Calculate cross-field consistency score"""
        # Placeholder implementation
        return 95.0