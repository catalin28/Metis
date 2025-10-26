"""
Prompt Generator - Creates populated LLM prompts from competitive intelligence JSON.
"""

from typing import Dict, Any
from pathlib import Path


class PromptGenerator:
    """Generates populated prompt templates for LLM analysis."""
    
    def __init__(self, template_path: str = None):
        """
        Initialize with template path.
        
        Args:
            template_path: Path to prompt template file. If None, uses default.
        """
        if template_path is None:
            # Get path relative to project root
            project_root = Path(__file__).parent.parent.parent.parent
            template_path = project_root / "prompts" / "swing_trading" / "swing_trader_analysis_prompt_template.txt"
        
        self.template_path = Path(template_path)
        
        if not self.template_path.exists():
            raise FileNotFoundError(
                f"Template not found: {self.template_path}\n"
                f"Looked in: {self.template_path.absolute()}"
            )
        
        self.template = self._load_template()
    
    def _load_template(self) -> str:
        """Load prompt template from file."""
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template not found: {self.template_path}")
        
        with open(self.template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    def format_currency(value: float) -> str:
        """Format large numbers as readable currency strings."""
        if value >= 1_000_000_000:
            return f"{value / 1_000_000_000:.2f}B"
        elif value >= 1_000_000:
            return f"{value / 1_000_000:.2f}M"
        else:
            return f"{value:,.0f}"
    
    def populate_template(self, report_data: Dict[str, Any]) -> str:
        """
        Populate template with report data.
        
        Args:
            report_data: Competitive intelligence report JSON
            
        Returns:
            Populated prompt ready for LLM
        """
        # Extract data
        target_company = report_data.get('peer_group', {}).get('target_company', {})
        valuation = report_data.get('valuation_context', {})
        dashboard = report_data.get('section_2_competitive_dashboard', {})
        
        # Build replacements dictionary
        replacements = {
            '{target_symbol}': report_data.get('target_symbol', 'N/A'),
            '{target_company_name}': target_company.get('company_name', 'N/A'),
            '{target_sector}': target_company.get('sector', 'N/A'),
            '{target_market_cap}': self.format_currency(target_company.get('market_cap', 0)),
            '{target_pe}': f"{target_company.get('pe_ratio', 0):.2f}",
            '{target_revenue_ttm}': self.format_currency(target_company.get('revenue_ttm', 0)),
            '{peer_avg_pe}': f"{valuation.get('peer_average_pe', 0):.2f}",
            '{premium_vs_peer_percent}': f"{valuation.get('premium_vs_peer_percent', 0):.2f}",
            '{downside_to_peer_multiple_percent}': f"{valuation.get('downside_to_peer_multiple_percent', 0):.2f}",
            '{valuation_gap_dollars}': self.format_currency(abs(valuation.get('valuation_gap_dollars', 0))),
            '{implied_market_cap}': self.format_currency(valuation.get('implied_market_cap', 0)),
            '{overall_rank}': str(dashboard.get('overall_target_rank', 'N/A')),
            '{total_companies}': str(len(report_data.get('peer_symbols', [])) + 1),
        }
        
        # Add peer list
        replacements['{peer_list}'] = self._extract_peer_list(report_data)
        
        # Add competitive metrics table
        replacements['{competitive_metrics_table}'] = self._extract_competitive_metrics_table(report_data)
        
        # Add rankings
        replacements['{top_3_metrics}'] = self._extract_top_bottom_metrics(report_data, top=True, n=3)
        replacements['{bottom_3_metrics}'] = self._extract_top_bottom_metrics(report_data, top=False, n=3)
        
        # Add analyst data
        self._add_analyst_replacements(replacements, report_data)
        
        # Add analyst actions table
        replacements['{peer_analyst_actions_table}'] = self._extract_peer_analyst_actions_table(report_data)
        
        # Add hidden strengths
        replacements['{hidden_strengths_list}'] = self._extract_hidden_strengths_list(report_data)
        
        # Perform replacements
        result = self.template
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, str(value))
        
        return result
    
    def _extract_peer_list(self, data: Dict[str, Any]) -> str:
        """Extract and format peer company list."""
        peers = data.get('peer_group', {}).get('peers', [])
        peer_strings = []
        for i, peer in enumerate(peers, 1):
            peer_strings.append(
                f"{i}. {peer['symbol']} - {peer['company_name']} "
                f"(Similarity: {peer.get('similarity_score', 0.8):.2f})"
            )
        return "\n".join(peer_strings)
    
    def _extract_competitive_metrics_table(self, data: Dict[str, Any]) -> str:
        """Create a formatted table of competitive metrics with rankings."""
        metrics = data.get('section_2_competitive_dashboard', {}).get('metrics', [])
        
        if not metrics:
            return "No metrics data available"
        
        # Build header
        target_symbol = data['target_symbol']
        peer_symbols = data['peer_symbols']
        header = f"| Metric | {target_symbol} | " + " | ".join(peer_symbols) + " | Rank | Perception |\n"
        separator = "|--------|" + "--------|" * (len(peer_symbols) + 1) + "------------|-------------|\n"
        
        rows = []
        for metric in metrics:
            metric_name = metric['metric_name']
            target_val = metric['target_value']
            
            # Format target value
            if metric_name == 'Market Cap':
                target_str = f"${self.format_currency(target_val)}"
            elif metric_name == 'P/E Ratio':
                target_str = f"{target_val:.2f}x"
            elif metric_name in ['ROE', 'ROA', 'Revenue Growth', 'Gross Margin', 'Operating Margin', 'Net Margin']:
                target_str = f"{target_val * 100:.2f}%" if abs(target_val) < 1 else f"{target_val:.2f}%"
            elif metric_name == 'Debt/Equity':
                target_str = f"{target_val:.2f}"
            else:
                target_str = f"{target_val:.2f}"
            
            # Format peer values
            peer_vals = []
            peer_values = metric.get('peer_values', {})
            for peer_sym in peer_symbols:
                peer_val = peer_values.get(peer_sym, 0)
                if metric_name == 'Market Cap':
                    peer_vals.append(f"${self.format_currency(peer_val)}")
                elif metric_name == 'P/E Ratio':
                    peer_vals.append(f"{peer_val:.2f}x")
                elif metric_name in ['ROE', 'ROA', 'Revenue Growth', 'Gross Margin', 'Operating Margin', 'Net Margin']:
                    peer_vals.append(f"{peer_val * 100:.2f}%" if abs(peer_val) < 1 else f"{peer_val:.2f}%")
                elif metric_name == 'Debt/Equity':
                    peer_vals.append(f"{peer_val:.2f}")
                else:
                    peer_vals.append(f"{peer_val:.2f}")
            
            rank = f"#{metric['target_rank']} ({metric['rank_qualifier']})"
            perception = metric.get('market_perception', 'N/A')
            
            row = f"| {metric_name} | {target_str} | " + " | ".join(peer_vals) + f" | {rank} | {perception} |"
            rows.append(row)
        
        return header + separator + "\n".join(rows)
    
    def _extract_top_bottom_metrics(self, data: Dict[str, Any], top: bool = True, n: int = 3) -> str:
        """Extract top N or bottom N metrics by rank."""
        metrics = data.get('section_2_competitive_dashboard', {}).get('metrics', [])
        
        # Sort by rank
        sorted_metrics = sorted(metrics, key=lambda x: x['target_rank'])
        
        if top:
            selected = sorted_metrics[:n]
        else:
            selected = sorted_metrics[-n:]
        
        result = []
        for metric in selected:
            result.append(
                f"#{metric['target_rank']} {metric['metric_name']} "
                f"({metric['rank_qualifier']})"
            )
        
        return ", ".join(result)
    
    def _add_analyst_replacements(self, replacements: Dict[str, str], data: Dict[str, Any]) -> None:
        """Add analyst sentiment replacements to dictionary."""
        target_analyst = data.get('section_2_5_analyst_consensus', {}).get('target_analysis', {})
        target_latest = target_analyst.get('latest_action', {})
        
        replacements.update({
            '{target_coverage_breadth}': str(target_analyst.get('coverage_breadth', 0)),
            '{target_recent_actions_90d}': str(target_analyst.get('recent_actions_90d', 0)),
            '{target_upgrades_90d}': str(target_analyst.get('upgrades_90d', 0)),
            '{target_downgrades_90d}': str(target_analyst.get('downgrades_90d', 0)),
            '{target_maintains_90d}': str(target_analyst.get('maintains_90d', 0)),
            '{target_net_sentiment}': target_analyst.get('net_sentiment', 'N/A'),
            '{target_latest_action_date}': target_latest.get('date', 'N/A'),
            '{target_latest_action_firm}': target_latest.get('grading_company', 'N/A'),
            '{target_latest_action_type}': target_latest.get('action', 'N/A').upper(),
            '{target_latest_action_new_grade}': target_latest.get('new_grade', 'N/A'),
        })
    
    def _extract_peer_analyst_actions_table(self, data: Dict[str, Any]) -> str:
        """Create a table comparing analyst actions across peers."""
        target_symbol = data['target_symbol']
        target_analyst = data.get('section_2_5_analyst_consensus', {}).get('target_analysis', {})
        peer_analysts = data.get('section_2_5_analyst_consensus', {}).get('peer_analysis', [])
        
        # Build header
        header = "| Company | Coverage | Recent Actions (90d) | Upgrades | Downgrades | Maintains | Sentiment | Latest Action |\n"
        separator = "|---------|----------|----------------------|----------|------------|-----------|-----------|---------------|\n"
        
        rows = []
        
        # Add target row
        target_latest = target_analyst.get('latest_action', {})
        target_row = (
            f"| **{target_symbol}** | {target_analyst.get('coverage_breadth', 0)} | "
            f"{target_analyst.get('recent_actions_90d', 0)} | "
            f"{target_analyst.get('upgrades_90d', 0)} | "
            f"{target_analyst.get('downgrades_90d', 0)} | "
            f"{target_analyst.get('maintains_90d', 0)} | "
            f"{target_analyst.get('net_sentiment', 'N/A')} | "
            f"{target_latest.get('date', 'N/A')}: {target_latest.get('action', 'N/A').upper()} |"
        )
        rows.append(target_row)
        
        # Add peer rows
        for peer in peer_analysts:
            peer_latest = peer.get('latest_action', {})
            peer_row = (
                f"| {peer['symbol']} | {peer.get('coverage_breadth', 0)} | "
                f"{peer.get('recent_actions_90d', 0)} | "
                f"{peer.get('upgrades_90d', 0)} | "
                f"{peer.get('downgrades_90d', 0)} | "
                f"{peer.get('maintains_90d', 0)} | "
                f"{peer.get('net_sentiment', 'N/A')} | "
                f"{peer_latest.get('date', 'N/A')}: {peer_latest.get('action', 'N/A').upper()} |"
            )
            rows.append(peer_row)
        
        return header + separator + "\n".join(rows)
    
    def _extract_hidden_strengths_list(self, data: Dict[str, Any]) -> str:
        """Extract and format hidden strengths with details."""
        strengths = data.get('section_3_hidden_strengths', {}).get('strengths', [])
        
        if not strengths:
            return "No hidden strengths data available"
        
        result = []
        for i, strength in enumerate(strengths, 1):
            metric_name = strength['metric_name'].upper()
            target_val = strength['target_value']
            peer_avg = strength['peer_average']
            outperformance = strength['outperformance_magnitude']
            why_ignored = strength['why_wall_street_ignores']
            valuation_impact = strength['valuation_impact']
            
            # Format values based on metric type
            if 'margin' in metric_name.lower() or 'roe' in metric_name.lower() or 'roa' in metric_name.lower():
                target_str = f"{target_val * 100:.2f}%"
                peer_str = f"{peer_avg * 100:.2f}%"
            elif 'cap' in metric_name.lower():
                target_str = f"${self.format_currency(target_val)}"
                peer_str = f"${self.format_currency(peer_avg)}"
            elif 'growth' in metric_name.lower():
                target_str = f"{target_val:.2f}%"
                peer_str = f"{peer_avg:.2f}%"
            elif 'debt' in metric_name.lower() or 'equity' in metric_name.lower():
                target_str = f"{target_val:.2f}"
                peer_str = f"{peer_avg:.2f}"
            else:
                target_str = f"{target_val:.2f}"
                peer_str = f"{peer_avg:.2f}"
            
            strength_text = f"""
**{i}. {metric_name}**
- Target Value: {target_str}
- Peer Average: {peer_str}
- Outperformance: {outperformance}
- Why Wall Street Ignores: {why_ignored}
- Estimated Valuation Impact: {valuation_impact}
"""
            result.append(strength_text.strip())
        
        return "\n\n".join(result)
