"""
Cross-reference similarity analysis with vulnerability results.
Identifies clone pairs that share the same vulnerabilities.
"""

import json


def load_reports():
    """Load similarity and vulnerability reports."""
    with open('similarity_report.json', 'r') as f:
        similarity = json.load(f)
    
    with open('vulnerability_report.json', 'r') as f:
        vulnerabilities = json.load(f)
    
    return similarity, vulnerabilities


def find_high_risk_clones(similarity, threshold=0.95):
    """Extract high-risk clone pairs (≥95% similarity)."""
    high_risk = []
    
    for pair_key, data in similarity.items():
        full_sim = data.get('full_similarity', 0)
        partial_sim = data.get('partial_similarity', 0)
        
        if full_sim >= threshold or partial_sim >= threshold:
            high_risk.append({
                'contract1': data['contract1'],
                'contract2': data['contract2'],
                'full_similarity': full_sim,
                'partial_similarity': partial_sim,
                'max_similarity': max(full_sim, partial_sim)
            })
    
    # Sort by similarity (highest first)
    high_risk.sort(key=lambda x: x['max_similarity'], reverse=True)
    
    return high_risk


def get_vulnerability_summary(address, vuln_data):
    """Get summary of vulnerabilities for a contract."""
    if address not in vuln_data:
        return {
            'success': False,
            'error': 'Not analyzed',
            'total': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }
    
    data = vuln_data[address]
    
    if not data.get('success'):
        return {
            'success': False,
            'error': data.get('error', 'Unknown error'),
            'total': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }
    
    severity = data.get('severity_breakdown', {})
    
    return {
        'success': True,
        'total': data.get('issue_count', 0),
        'high': severity.get('High', 0),
        'medium': severity.get('Medium', 0),
        'low': severity.get('Low', 0),
        'issues': data.get('issues', [])
    }


def compare_vulnerabilities(issues1, issues2):
    """Find shared vulnerability types between two contracts."""
    if not issues1 or not issues2:
        return []
    
    # Extract vulnerability types
    types1 = set(issue['type'] for issue in issues1)
    types2 = set(issue['type'] for issue in issues2)
    
    # Find shared types
    shared = types1 & types2
    
    # Get details for shared vulnerabilities
    shared_vulns = []
    for vuln_type in shared:
        # Get severity from first occurrence
        severity = None
        for issue in issues1:
            if issue['type'] == vuln_type:
                severity = issue['severity']
                break
        
        shared_vulns.append({
            'type': vuln_type,
            'severity': severity
        })
    
    # Sort by severity
    severity_order = {'High': 0, 'Medium': 1, 'Low': 2, 'Informational': 3, 'Optimization': 4}
    shared_vulns.sort(key=lambda x: severity_order.get(x['severity'], 99))
    
    return shared_vulns


def main():
    """Generate cross-reference report."""
    print("="*80)
    print("CLONE PAIRS WITH SHARED VULNERABILITIES")
    print("="*80)
    print()
    
    # Load reports
    print("Loading reports...")
    similarity, vulnerabilities = load_reports()
    print(f"✓ Loaded {len(similarity)} similarity pairs")
    print(f"✓ Loaded {len(vulnerabilities)} vulnerability reports")
    print()
    
    # Find high-risk clones
    print("Identifying high-risk clone pairs (≥95% similarity)...")
    high_risk_pairs = find_high_risk_clones(similarity)
    print(f"✓ Found {len(high_risk_pairs)} high-risk clone pairs")
    print()
    
    # Analyze each pair
    print("="*80)
    print("ANALYZING CLONE PAIRS FOR SHARED VULNERABILITIES")
    print("="*80)
    print()
    
    results = []
    pairs_with_shared_vulns = 0
    pairs_both_analyzed = 0
    
    for idx, pair in enumerate(high_risk_pairs, 1):
        addr1 = pair['contract1']
        addr2 = pair['contract2']
        similarity_score = pair['max_similarity']
        
        # Get vulnerability summaries
        vuln1 = get_vulnerability_summary(addr1, vulnerabilities)
        vuln2 = get_vulnerability_summary(addr2, vulnerabilities)
        
        # Check if both were successfully analyzed
        both_analyzed = vuln1['success'] and vuln2['success']
        
        if both_analyzed:
            pairs_both_analyzed += 1
            
            # Compare vulnerabilities
            shared = compare_vulnerabilities(vuln1.get('issues', []), vuln2.get('issues', []))
            
            if shared:
                pairs_with_shared_vulns += 1
                
                result = {
                    'pair_number': idx,
                    'contract1': addr1,
                    'contract2': addr2,
                    'similarity': similarity_score,
                    'contract1_vulns': {
                        'total': vuln1['total'],
                        'high': vuln1['high'],
                        'medium': vuln1['medium'],
                        'low': vuln1['low']
                    },
                    'contract2_vulns': {
                        'total': vuln2['total'],
                        'high': vuln2['high'],
                        'medium': vuln2['medium'],
                        'low': vuln2['low']
                    },
                    'shared_vulnerabilities': shared,
                    'shared_count': len(shared)
                }
                
                results.append(result)
                
                # Print summary
                print(f"[{idx}/{len(high_risk_pairs)}] Pair #{idx} - {similarity_score*100:.1f}% similar")
                print(f"  Contract 1: {addr1}")
                print(f"    Issues: {vuln1['total']} (🔴{vuln1['high']} 🟡{vuln1['medium']} 🟢{vuln1['low']})")
                print(f"  Contract 2: {addr2}")
                print(f"    Issues: {vuln2['total']} (🔴{vuln2['high']} 🟡{vuln2['medium']} 🟢{vuln2['low']})")
                print(f"  Shared Vulnerabilities: {len(shared)}")
                
                for vuln in shared[:5]:  # Show first 5
                    emoji = {'High': '🔴', 'Medium': '🟡', 'Low': '🟢'}.get(vuln['severity'], '•')
                    print(f"    {emoji} {vuln['type']} ({vuln['severity']})")
                
                if len(shared) > 5:
                    print(f"    ... and {len(shared)-5} more")
                
                print()
    
    # Save detailed results
    with open('CLONE_VULNERABILITY_CROSSREF.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Generate summary
    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"High-Risk Clone Pairs: {len(high_risk_pairs)}")
    print(f"Pairs Where Both Were Analyzed: {pairs_both_analyzed}")
    print(f"Pairs With Shared Vulnerabilities: {pairs_with_shared_vulns}")
    print()
    print(f"📊 {pairs_with_shared_vulns}/{pairs_both_analyzed} analyzed pairs ({pairs_with_shared_vulns/pairs_both_analyzed*100 if pairs_both_analyzed > 0 else 0:.1f}%) share vulnerabilities")
    print()
    print(f"💾 Detailed results saved to: CLONE_VULNERABILITY_CROSSREF.json")
    print("="*80)
    
    # Create markdown report
    create_markdown_report(results, high_risk_pairs, pairs_both_analyzed, pairs_with_shared_vulns)


def create_markdown_report(results, all_pairs, analyzed_pairs, shared_pairs):
    """Create a human-readable markdown report."""
    
    md = []
    md.append("# Clone Pairs with Shared Vulnerabilities\n")
    md.append(f"**Analysis Date:** October 31, 2025\n")
    md.append(f"**Total High-Risk Clone Pairs:** {len(all_pairs)}\n")
    md.append(f"**Pairs Successfully Analyzed:** {analyzed_pairs}\n")
    md.append(f"**Pairs with Shared Vulnerabilities:** {shared_pairs}\n")
    md.append("\n---\n\n")
    
    md.append("## Summary Statistics\n\n")
    md.append(f"- **Clone Detection Threshold:** ≥95% similarity\n")
    md.append(f"- **High-Risk Pairs Found:** {len(all_pairs)}\n")
    md.append(f"- **Both Contracts Analyzed:** {analyzed_pairs}/{len(all_pairs)} ({analyzed_pairs/len(all_pairs)*100:.1f}%)\n")
    md.append(f"- **Sharing Vulnerabilities:** {shared_pairs}/{analyzed_pairs} ({shared_pairs/analyzed_pairs*100 if analyzed_pairs > 0 else 0:.1f}%)\n")
    md.append("\n---\n\n")
    
    md.append("## High-Risk Clone Pairs with Shared Vulnerabilities\n\n")
    
    if not results:
        md.append("*No clone pairs with shared vulnerabilities found.*\n")
    else:
        for result in results:
            md.append(f"### Pair #{result['pair_number']} - {result['similarity']*100:.1f}% Similar\n\n")
            
            md.append(f"**Contract 1:** `{result['contract1']}`\n")
            md.append(f"- Total Issues: {result['contract1_vulns']['total']}\n")
            md.append(f"- 🔴 High: {result['contract1_vulns']['high']}\n")
            md.append(f"- 🟡 Medium: {result['contract1_vulns']['medium']}\n")
            md.append(f"- 🟢 Low: {result['contract1_vulns']['low']}\n\n")
            
            md.append(f"**Contract 2:** `{result['contract2']}`\n")
            md.append(f"- Total Issues: {result['contract2_vulns']['total']}\n")
            md.append(f"- 🔴 High: {result['contract2_vulns']['high']}\n")
            md.append(f"- 🟡 Medium: {result['contract2_vulns']['medium']}\n")
            md.append(f"- 🟢 Low: {result['contract2_vulns']['low']}\n\n")
            
            md.append(f"**Shared Vulnerabilities ({result['shared_count']}):**\n\n")
            
            for vuln in result['shared_vulnerabilities']:
                emoji = {'High': '🔴', 'Medium': '🟡', 'Low': '🟢', 
                        'Informational': 'ℹ️', 'Optimization': '⚡'}.get(vuln['severity'], '•')
                md.append(f"- {emoji} **{vuln['type']}** ({vuln['severity']})\n")
            
            md.append("\n---\n\n")
    
    # Save markdown report (with UTF-8 encoding)
    with open('CLONE_VULNERABILITY_CROSSREF.md', 'w', encoding='utf-8') as f:
        f.writelines(md)
    
    print(f"📄 Markdown report saved to: CLONE_VULNERABILITY_CROSSREF.md")


if __name__ == "__main__":
    main()
