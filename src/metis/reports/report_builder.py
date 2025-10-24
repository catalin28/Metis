"""
Report Builder for Competitive Intelligence Reports

This module provides a fluent API for assembling competitive intelligence reports
with integrated validation and error handling.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from ..models.report_schema_v2 import (
    CompetitiveIntelligenceReport,
    ReportMetadata,
    ProcessingMetadata,
    CompanyProfile,
    PeerGroup,
    ExecutiveSummary,
    CompetitiveDashboard,
    HiddenStrengths,
    StealTheirPlaybook,
    ValuationForensics,
    ActionableRoadmap
)
from ..utils.schema_validator import CompetitiveIntelligenceReportValidator
from ..utils.validation_models import ValidationResult, ValidationSeverity


class ReportBuilderError(Exception):
    """Raised when report building fails"""
    pass


class CompetitiveIntelligenceReportBuilder:
    """
    Fluent API builder for competitive intelligence reports.
    
    Usage:
        builder = CompetitiveIntelligenceReportBuilder("WRB", "client_123")
        report = (builder
            .add_company_profile(profile_data)
            .add_peer_group(peer_data)
            .add_executive_summary(summary_data)
            .add_competitive_dashboard(dashboard_data)
            .add_hidden_strengths(strengths_data)
            .add_steal_their_playbook(playbook_data)
            .add_valuation_forensics(valuation_data)
            .add_actionable_roadmap(roadmap_data)
            .build()
        )
    """
    
    def __init__(self, target_symbol: str, client_id: str, schema_version: str = "1.0"):
        """
        Initialize builder with required metadata.
        
        Args:
            target_symbol: Stock symbol for target company
            client_id: Client identifier
            schema_version: Schema version to use
        """
        self.target_symbol = target_symbol.upper()
        self.client_id = client_id
        self.schema_version = schema_version
        
        # Initialize components
        self._metadata: Optional[ReportMetadata] = None
        self._company_profile: Optional[CompanyProfile] = None
        self._peer_group: Optional[PeerGroup] = None
        self._executive_summary: Optional[ExecutiveSummary] = None
        self._competitive_dashboard: Optional[CompetitiveDashboard] = None
        self._hidden_strengths: Optional[HiddenStrengths] = None
        self._steal_their_playbook: Optional[StealTheirPlaybook] = None
        self._valuation_forensics: Optional[ValuationForensics] = None
        self._actionable_roadmap: Optional[ActionableRoadmap] = None
        
        # Validation and tracking
        self._validator = CompetitiveIntelligenceReportValidator()
        self._processing_metadata = ProcessingMetadata()
        self._build_errors: List[str] = []
        
        # Initialize metadata
        self._create_metadata()
    
    def _create_metadata(self) -> None:
        """Create initial report metadata"""
        self._metadata = ReportMetadata(
            target_symbol=self.target_symbol,
            client_id=self.client_id,
            schema_version=self.schema_version,
            processing_metadata=self._processing_metadata
        )
    
    def add_metadata(self, metadata: ReportMetadata) -> 'CompetitiveIntelligenceReportBuilder':
        """
        Add or update report metadata.
        
        Args:
            metadata: Report metadata object
            
        Returns:
            Self for method chaining
        """
        # Validate symbol consistency
        if metadata.target_symbol != self.target_symbol:
            raise ReportBuilderError(
                f"Metadata target symbol ({metadata.target_symbol}) doesn't match builder ({self.target_symbol})"
            )
        
        self._metadata = metadata
        return self
    
    def add_company_profile(self, profile: CompanyProfile) -> 'CompetitiveIntelligenceReportBuilder':
        """
        Add company profile section.
        
        Args:
            profile: Company profile data
            
        Returns:
            Self for method chaining
        """
        # Validate symbol consistency
        if profile.symbol != self.target_symbol:
            raise ReportBuilderError(
                f"Profile symbol ({profile.symbol}) doesn't match target ({self.target_symbol})"
            )
        
        # Validate section
        validation_result = self._validator.validate_section("company_profile", profile)
        if validation_result.critical_count > 0 or validation_result.errors_count > 0:
            self._build_errors.extend([issue.message for issue in validation_result.issues])
        
        self._company_profile = profile
        return self
    
    def add_peer_group(self, peer_group: PeerGroup) -> 'CompetitiveIntelligenceReportBuilder':
        """
        Add peer group section.
        
        Args:
            peer_group: Peer group data
            
        Returns:
            Self for method chaining
        """
        # Validate target symbol consistency
        if peer_group.target_symbol != self.target_symbol:
            raise ReportBuilderError(
                f"Peer group target ({peer_group.target_symbol}) doesn't match builder ({self.target_symbol})"
            )
        
        # Validate that target is not in peer list
        peer_symbols = [peer.symbol for peer in peer_group.peers]
        if self.target_symbol in peer_symbols:
            raise ReportBuilderError(f"Target symbol {self.target_symbol} cannot be in peer group")
        
        # Validate section
        validation_result = self._validator.validate_section("peer_group", peer_group)
        if validation_result.critical_count > 0 or validation_result.errors_count > 0:
            self._build_errors.extend([issue.message for issue in validation_result.issues])
        
        self._peer_group = peer_group
        return self
    
    def add_executive_summary(self, summary: ExecutiveSummary) -> 'CompetitiveIntelligenceReportBuilder':
        """
        Add executive summary section.
        
        Args:
            summary: Executive summary data
            
        Returns:
            Self for method chaining
        """
        # Validate section
        validation_result = self._validator.validate_section("executive_summary", summary)
        if validation_result.critical_count > 0 or validation_result.errors_count > 0:
            self._build_errors.extend([issue.message for issue in validation_result.issues])
        
        self._executive_summary = summary
        return self
    
    def add_competitive_dashboard(self, dashboard: CompetitiveDashboard) -> 'CompetitiveIntelligenceReportBuilder':
        """
        Add competitive dashboard section.
        
        Args:
            dashboard: Competitive dashboard data
            
        Returns:
            Self for method chaining
        """
        # Validate that target company is included
        dashboard_symbols = [comp.symbol for comp in dashboard.companies]
        if self.target_symbol not in dashboard_symbols:
            raise ReportBuilderError(f"Target symbol {self.target_symbol} not found in dashboard")
        
        # Validate peer consistency if peer group is already set
        if self._peer_group:
            expected_symbols = {self.target_symbol} | {peer.symbol for peer in self._peer_group.peers}
            actual_symbols = set(dashboard_symbols)
            
            if expected_symbols != actual_symbols:
                missing = expected_symbols - actual_symbols
                extra = actual_symbols - expected_symbols
                raise ReportBuilderError(
                    f"Dashboard symbols don't match peer group. Missing: {missing}, Extra: {extra}"
                )
        
        # Validate section
        validation_result = self._validator.validate_section("competitive_dashboard", dashboard)
        if validation_result.critical_count > 0 or validation_result.errors_count > 0:
            self._build_errors.extend([issue.message for issue in validation_result.issues])
        
        self._competitive_dashboard = dashboard
        return self
    
    def add_hidden_strengths(self, strengths: HiddenStrengths) -> 'CompetitiveIntelligenceReportBuilder':
        """
        Add hidden strengths section.
        
        Args:
            strengths: Hidden strengths data
            
        Returns:
            Self for method chaining
        """
        # Validate section
        validation_result = self._validator.validate_section("hidden_strengths", strengths)
        if validation_result.critical_count > 0 or validation_result.errors_count > 0:
            self._build_errors.extend([issue.message for issue in validation_result.issues])
        
        self._hidden_strengths = strengths
        return self
    
    def add_steal_their_playbook(self, playbook: StealTheirPlaybook) -> 'CompetitiveIntelligenceReportBuilder':
        """
        Add steal their playbook section.
        
        Args:
            playbook: Competitor strategy analysis data
            
        Returns:
            Self for method chaining
        """
        # Validate that strategies reference known peers
        if self._peer_group:
            peer_symbols = {peer.symbol for peer in self._peer_group.peers}
            strategy_symbols = {strategy.peer_symbol for strategy in playbook.competitor_strategies}
            
            unknown_peers = strategy_symbols - peer_symbols
            if unknown_peers:
                raise ReportBuilderError(f"Strategies reference unknown peers: {unknown_peers}")
        
        # Validate section
        validation_result = self._validator.validate_section("steal_their_playbook", playbook)
        if validation_result.critical_count > 0 or validation_result.errors_count > 0:
            self._build_errors.extend([issue.message for issue in validation_result.issues])
        
        self._steal_their_playbook = playbook
        return self
    
    def add_valuation_forensics(self, forensics: ValuationForensics) -> 'CompetitiveIntelligenceReportBuilder':
        """
        Add valuation forensics section.
        
        Args:
            forensics: Valuation analysis data
            
        Returns:
            Self for method chaining
        """
        # Validate section
        validation_result = self._validator.validate_section("valuation_forensics", forensics)
        if validation_result.critical_count > 0 or validation_result.errors_count > 0:
            self._build_errors.extend([issue.message for issue in validation_result.issues])
        
        self._valuation_forensics = forensics
        return self
    
    def add_actionable_roadmap(self, roadmap: ActionableRoadmap) -> 'CompetitiveIntelligenceReportBuilder':
        """
        Add actionable roadmap section.
        
        Args:
            roadmap: Actionable recommendations data
            
        Returns:
            Self for method chaining
        """
        # Validate section
        validation_result = self._validator.validate_section("actionable_roadmap", roadmap)
        if validation_result.critical_count > 0 or validation_result.errors_count > 0:
            self._build_errors.extend([issue.message for issue in validation_result.issues])
        
        self._actionable_roadmap = roadmap
        return self
    
    def update_processing_metadata(self, **kwargs) -> 'CompetitiveIntelligenceReportBuilder':
        """
        Update processing metadata with additional information.
        
        Args:
            **kwargs: Metadata fields to update
            
        Returns:
            Self for method chaining
        """
        for key, value in kwargs.items():
            if hasattr(self._processing_metadata, key):
                setattr(self._processing_metadata, key, value)
        
        # Update metadata object
        if self._metadata:
            self._metadata.processing_metadata = self._processing_metadata
        
        return self
    
    def validate_current_state(self) -> ValidationResult:
        """
        Validate current builder state without building the final report.
        
        Returns:
            Validation result for current state
        """
        # Create temporary report for validation
        try:
            temp_report = self._create_report_object()
            return self._validator.validate_report(temp_report)
        except Exception as e:
            # Create minimal validation result with error
            result = ValidationResult(is_valid=False)
            result.add_global_issue({
                "severity": ValidationSeverity.CRITICAL,
                "category": "BUILDER_ERROR",
                "code": "BUILD_VALIDATION_ERROR",
                "message": f"Error validating builder state: {str(e)}"
            })
            return result
    
    def get_completion_status(self) -> Dict[str, bool]:
        """
        Get completion status of all required sections.
        
        Returns:
            Dictionary mapping section names to completion status
        """
        return {
            "metadata": self._metadata is not None,
            "company_profile": self._company_profile is not None,
            "peer_group": self._peer_group is not None,
            "executive_summary": self._executive_summary is not None,
            "competitive_dashboard": self._competitive_dashboard is not None,
            "hidden_strengths": self._hidden_strengths is not None,
            "steal_their_playbook": self._steal_their_playbook is not None,
            "valuation_forensics": self._valuation_forensics is not None,
            "actionable_roadmap": self._actionable_roadmap is not None
        }
    
    def get_missing_sections(self) -> List[str]:
        """
        Get list of missing required sections.
        
        Returns:
            List of missing section names
        """
        completion = self.get_completion_status()
        return [section for section, completed in completion.items() if not completed]
    
    def is_complete(self) -> bool:
        """
        Check if all required sections are present.
        
        Returns:
            True if all sections are complete
        """
        return len(self.get_missing_sections()) == 0
    
    def build(self, validate: bool = True) -> CompetitiveIntelligenceReport:
        """
        Build the final competitive intelligence report.
        
        Args:
            validate: Whether to perform full validation before building
            
        Returns:
            Complete competitive intelligence report
            
        Raises:
            ReportBuilderError: If required sections are missing or validation fails
        """
        # Check for missing sections
        missing_sections = self.get_missing_sections()
        if missing_sections:
            raise ReportBuilderError(f"Missing required sections: {missing_sections}")
        
        # Check for build errors
        if self._build_errors:
            raise ReportBuilderError(f"Build errors found: {'; '.join(self._build_errors)}")
        
        # Create report object
        report = self._create_report_object()
        
        # Validate if requested
        if validate:
            validation_result = self._validator.validate_report(report)
            
            if not validation_result.is_valid:
                critical_errors = [
                    issue.message for issue in validation_result.get_issues_by_severity(ValidationSeverity.CRITICAL)
                ]
                major_errors = [
                    issue.message for issue in validation_result.get_issues_by_severity(ValidationSeverity.ERROR)
                ]
                
                if critical_errors or major_errors:
                    error_msg = "Validation failed:\n"
                    if critical_errors:
                        error_msg += f"Critical: {'; '.join(critical_errors)}\n"
                    if major_errors:
                        error_msg += f"Errors: {'; '.join(major_errors)}"
                    
                    raise ReportBuilderError(error_msg)
        
        return report
    
    def _create_report_object(self) -> CompetitiveIntelligenceReport:
        """Create the report object from current builder state"""
        return CompetitiveIntelligenceReport(
            report_metadata=self._metadata,
            company_profile=self._company_profile,
            peer_group=self._peer_group,
            executive_summary=self._executive_summary,
            competitive_dashboard=self._competitive_dashboard,
            hidden_strengths=self._hidden_strengths,
            steal_their_playbook=self._steal_their_playbook,
            valuation_forensics=self._valuation_forensics,
            actionable_roadmap=self._actionable_roadmap
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert current builder state to dictionary.
        
        Returns:
            Dictionary representation of current report state
        """
        try:
            report = self._create_report_object()
            return report.dict()
        except Exception:
            # Return partial state if full report can't be created
            return {
                "report_metadata": self._metadata.dict() if self._metadata else None,
                "company_profile": self._company_profile.dict() if self._company_profile else None,
                "peer_group": self._peer_group.dict() if self._peer_group else None,
                "executive_summary": self._executive_summary.dict() if self._executive_summary else None,
                "competitive_dashboard": self._competitive_dashboard.dict() if self._competitive_dashboard else None,
                "hidden_strengths": self._hidden_strengths.dict() if self._hidden_strengths else None,
                "steal_their_playbook": self._steal_their_playbook.dict() if self._steal_their_playbook else None,
                "valuation_forensics": self._valuation_forensics.dict() if self._valuation_forensics else None,
                "actionable_roadmap": self._actionable_roadmap.dict() if self._actionable_roadmap else None
            }
    
    def reset(self) -> 'CompetitiveIntelligenceReportBuilder':
        """
        Reset builder to initial state.
        
        Returns:
            Self for method chaining
        """
        # Reset all sections
        self._company_profile = None
        self._peer_group = None
        self._executive_summary = None
        self._competitive_dashboard = None
        self._hidden_strengths = None
        self._steal_their_playbook = None
        self._valuation_forensics = None
        self._actionable_roadmap = None
        
        # Reset tracking
        self._build_errors.clear()
        self._processing_metadata = ProcessingMetadata()
        
        # Recreate metadata
        self._create_metadata()
        
        return self
    
    def clone(self) -> 'CompetitiveIntelligenceReportBuilder':
        """
        Create a copy of the current builder.
        
        Returns:
            New builder instance with same state
        """
        clone = CompetitiveIntelligenceReportBuilder(
            target_symbol=self.target_symbol,
            client_id=self.client_id,
            schema_version=self.schema_version
        )
        
        # Copy all sections
        if self._company_profile:
            clone._company_profile = self._company_profile.copy()
        if self._peer_group:
            clone._peer_group = self._peer_group.copy()
        if self._executive_summary:
            clone._executive_summary = self._executive_summary.copy()
        if self._competitive_dashboard:
            clone._competitive_dashboard = self._competitive_dashboard.copy()
        if self._hidden_strengths:
            clone._hidden_strengths = self._hidden_strengths.copy()
        if self._steal_their_playbook:
            clone._steal_their_playbook = self._steal_their_playbook.copy()
        if self._valuation_forensics:
            clone._valuation_forensics = self._valuation_forensics.copy()
        if self._actionable_roadmap:
            clone._actionable_roadmap = self._actionable_roadmap.copy()
        
        # Copy processing metadata
        clone._processing_metadata = self._processing_metadata.copy()
        clone._build_errors = self._build_errors.copy()
        
        return clone


# Factory functions for convenience
def create_report_builder(target_symbol: str, client_id: str, schema_version: str = "1.0") -> CompetitiveIntelligenceReportBuilder:
    """
    Factory function to create a new report builder.
    
    Args:
        target_symbol: Stock symbol for target company
        client_id: Client identifier
        schema_version: Schema version to use
        
    Returns:
        New report builder instance
    """
    return CompetitiveIntelligenceReportBuilder(target_symbol, client_id, schema_version)


def build_report_from_dict(report_data: Dict[str, Any]) -> CompetitiveIntelligenceReport:
    """
    Build report directly from dictionary data.
    
    Args:
        report_data: Complete report data as dictionary
        
    Returns:
        Validated competitive intelligence report
        
    Raises:
        ReportBuilderError: If report data is invalid
    """
    try:
        return CompetitiveIntelligenceReport(**report_data)
    except Exception as e:
        raise ReportBuilderError(f"Failed to build report from dictionary: {str(e)}")