"""
Create Competitive Intelligence Tables

This migration creates the core database tables needed for the competitive
intelligence feature including reports, company metrics, and linguistic patterns.

Author: Metis Development Team
Created: 2025-10-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    """Create competitive intelligence tables."""
    
    # competitive_intelligence_reports table
    op.create_table(
        'competitive_intelligence_reports',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('report_id', sa.String(36), unique=True, nullable=False, index=True),
        sa.Column('target_symbol', sa.String(10), nullable=False, index=True),
        sa.Column('client_id', sa.String(100), nullable=True, index=True),
        sa.Column('report_data', postgresql.JSONB, nullable=False),
        sa.Column('processing_time_seconds', sa.Float, nullable=False),
        sa.Column('llm_tokens_used', sa.Integer, nullable=False, default=0),
        sa.Column('llm_cost_cents', sa.Integer, nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        
        # Indexes for performance
        sa.Index('idx_reports_target_symbol_created', 'target_symbol', 'created_at'),
        sa.Index('idx_reports_client_created', 'client_id', 'created_at'),
        sa.Index('idx_reports_created_at', 'created_at'),
    )
    
    # company_metrics_history table for time-series tracking
    op.create_table(
        'company_metrics_history',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('symbol', sa.String(10), nullable=False, index=True),
        sa.Column('as_of_date', sa.Date, nullable=False, index=True),
        sa.Column('market_cap', sa.BigInteger, nullable=True),
        sa.Column('pe_ratio', sa.Float, nullable=True),
        sa.Column('revenue_ttm', sa.BigInteger, nullable=True),
        sa.Column('revenue_growth_yoy', sa.Float, nullable=True),
        sa.Column('roe', sa.Float, nullable=True),
        sa.Column('debt_to_equity', sa.Float, nullable=True),
        sa.Column('sector', sa.String(100), nullable=True),
        sa.Column('industry', sa.String(200), nullable=True),
        sa.Column('country', sa.String(50), nullable=True),
        sa.Column('raw_metrics', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        
        # Unique constraint to prevent duplicates
        sa.UniqueConstraint('symbol', 'as_of_date', name='unique_symbol_date'),
        
        # Indexes for time-series queries
        sa.Index('idx_metrics_symbol_date', 'symbol', 'as_of_date'),
        sa.Index('idx_metrics_sector_date', 'sector', 'as_of_date'),
    )
    
    # linguistic_patterns table for earnings call analysis
    op.create_table(
        'linguistic_patterns',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('symbol', sa.String(10), nullable=False, index=True),
        sa.Column('earnings_date', sa.Date, nullable=False, index=True),
        sa.Column('quarter', sa.String(10), nullable=False),  # e.g., 'Q1-2025'
        sa.Column('transcript_id', sa.String(100), nullable=True),
        sa.Column('narrative_score', sa.Float, nullable=True),
        sa.Column('confidence_phrases', postgresql.JSONB, nullable=True),
        sa.Column('uncertainty_phrases', postgresql.JSONB, nullable=True),
        sa.Column('growth_language', postgresql.JSONB, nullable=True),
        sa.Column('risk_language', postgresql.JSONB, nullable=True),
        sa.Column('sentiment_score', sa.Float, nullable=True),
        sa.Column('abnormal_return_1d', sa.Float, nullable=True),
        sa.Column('abnormal_return_3d', sa.Float, nullable=True),
        sa.Column('abnormal_return_5d', sa.Float, nullable=True),
        sa.Column('volume_ratio', sa.Float, nullable=True),
        sa.Column('raw_analysis', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        
        # Unique constraint
        sa.UniqueConstraint('symbol', 'earnings_date', name='unique_symbol_earnings_date'),
        
        # Indexes for analysis queries
        sa.Index('idx_linguistic_symbol_quarter', 'symbol', 'quarter'),
        sa.Index('idx_linguistic_earnings_date', 'earnings_date'),
        sa.Index('idx_linguistic_narrative_score', 'narrative_score'),
    )
    
    # peer_relationships table for caching peer discovery results
    op.create_table(
        'peer_relationships',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('target_symbol', sa.String(10), nullable=False, index=True),
        sa.Column('peer_symbol', sa.String(10), nullable=False, index=True),
        sa.Column('similarity_score', sa.Float, nullable=False),
        sa.Column('source_method', sa.String(50), nullable=False),  # 'screener', 'fmp_peers', 'manual'
        sa.Column('similarity_components', postgresql.JSONB, nullable=True),
        sa.Column('discovered_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        
        # Unique constraint for peer relationships
        sa.UniqueConstraint('target_symbol', 'peer_symbol', name='unique_peer_relationship'),
        
        # Indexes for peer discovery queries
        sa.Index('idx_peers_target_score', 'target_symbol', 'similarity_score'),
        sa.Index('idx_peers_discovered_at', 'discovered_at'),
    )


def downgrade():
    """Drop competitive intelligence tables."""
    op.drop_table('peer_relationships')
    op.drop_table('linguistic_patterns')
    op.drop_table('company_metrics_history')
    op.drop_table('competitive_intelligence_reports')