#!/usr/bin/env python3
"""Test peer selection rationale feature"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from metis.orchestrators.report_generator import ReportGenerator


async def test_peer_rationale():
    """Generate minimal report and check peer selection rationale"""
    
    print("Initializing report generator...")
    generator = ReportGenerator()
    
    print("Generating report for ASML with 3 peers...")
    report = await generator.generate_complete_report(
        target_symbol='ASML',
        peer_symbols=['NXPI', 'STM', 'TSM'],
        max_workers=3
    )
    
    # Convert to dict
    report_dict = report.model_dump()
    
    # Check if peer selection rationale exists
    print("\n" + "="*80)
    print("PEER SELECTION RATIONALE")
    print("="*80)
    
    rationale = report_dict['peer_group'].get('selection_rationale')
    
    if rationale:
        print("\n✓ Peer selection rationale found!\n")
        print(f"Methodology:\n{rationale['methodology']}\n")
        print(f"Structural Differences:\n{rationale['structural_differences']}\n")
        print(f"Interpretation Guidance:\n{rationale['interpretation_guidance']}\n")
        
        if rationale.get('alternative_peer_considerations'):
            print(f"Alternative Considerations:\n{rationale['alternative_peer_considerations']}\n")
    else:
        print("\n✗ Peer selection rationale NOT FOUND\n")
    
    # Save full report
    output_file = 'asml_full_report_with_rationale.json'
    with open(output_file, 'w') as f:
        json.dump(report_dict, f, indent=2)
    
    print(f"\n✓ Full report saved to: {output_file}")
    print(f"  Peer group includes {len(report_dict['peer_group']['peers'])} peers")
    

if __name__ == '__main__':
    asyncio.run(test_peer_rationale())
