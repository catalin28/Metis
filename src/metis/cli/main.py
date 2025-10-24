"""Command line interface for Metis."""

import click
from typing import List, Optional

from metis.core.config import settings
from metis.orchestrators.competitive_intelligence_orchestrator import (
    CompetitiveIntelligenceOrchestrator,
)
from metis.assistants.peer_discovery_service import PeerDiscoveryService


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Metis - Competitive Intelligence Platform."""
    pass


@main.command()
@click.option("--symbol", required=True, help="Stock symbol to analyze")
@click.option("--max-peers", default=5, help="Maximum number of peers to analyze")
@click.option("--output", default="report.json", help="Output file path")
@click.option("--include-sections", multiple=True, help="Sections to include in report")
def analyze(symbol: str, max_peers: int, output: str, include_sections: tuple):
    """Generate competitive intelligence report for a company."""
    click.echo(f"Analyzing {symbol} with up to {max_peers} peers...")
    
    orchestrator = CompetitiveIntelligenceOrchestrator()
    
    try:
        result = orchestrator.generate_report(
            symbol=symbol,
            max_peers=max_peers,
            include_sections=list(include_sections) if include_sections else None
        )
        
        with open(output, 'w') as f:
            import json
            json.dump(result, f, indent=2)
            
        click.echo(f"Report generated successfully: {output}")
        
    except Exception as e:
        click.echo(f"Error generating report: {e}", err=True)
        raise click.Abort()


@main.command()
@click.option("--symbol", required=True, help="Stock symbol to find peers for")
@click.option("--sector", help="Sector override (auto-detected if not provided)")
@click.option("--max-peers", default=5, help="Maximum number of peers to return")
@click.option("--similarity-threshold", default=0.6, help="Minimum similarity score")
def discover_peers(symbol: str, sector: Optional[str], max_peers: int, similarity_threshold: float):
    """Discover peer companies for a given symbol."""
    click.echo(f"Discovering peers for {symbol}...")
    
    peer_service = PeerDiscoveryService()
    
    try:
        peers = peer_service.identify_peers(
            symbol=symbol,
            sector=sector,
            max_peers=max_peers,
            min_similarity=similarity_threshold
        )
        
        click.echo(f"Found {len(peers)} peers:")
        for peer in peers:
            click.echo(f"  {peer['symbol']}: {peer['name']} (similarity: {peer['similarity_score']:.2f})")
            
    except Exception as e:
        click.echo(f"Error discovering peers: {e}", err=True)
        raise click.Abort()


@main.command()
@click.option("--symbols", required=True, help="Comma-separated list of symbols")
@click.option("--output-dir", default="./reports", help="Output directory for reports")
@click.option("--parallel", is_flag=True, help="Process symbols in parallel")
def batch(symbols: str, output_dir: str, parallel: bool):
    """Process multiple symbols in batch."""
    symbol_list = [s.strip() for s in symbols.split(",")]
    click.echo(f"Processing {len(symbol_list)} symbols: {symbol_list}")
    
    if parallel:
        click.echo("Processing in parallel mode...")
    
    # Implementation would go here
    click.echo("Batch processing completed!")


if __name__ == "__main__":
    main()