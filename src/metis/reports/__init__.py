"""
Reports Module

This module contains the report building and assembly functionality for
competitive intelligence reports.
"""

from .report_builder_v2 import (
    CompetitiveIntelligenceReportBuilder,
    create_sample_report
)

__all__ = [
    'CompetitiveIntelligenceReportBuilder',
    'create_sample_report'
]