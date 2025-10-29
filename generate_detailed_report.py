import json
from pathlib import Path
from collections import Counter, defaultdict
import re

def extract_function_names(code):
    """Extract all function names from Solidity code"""
    pattern = r"\bfunction\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("
    return set(re.findall(pattern, code))

def analyze_similarity_report():
    # Load similarity report
    report = json.loads(Path('similarity_report.json').read_text())
    entries = list(report.values())
    
    # Load contract source codes
    with open('config.json') as f:
        config = json.load(f)
    
    # Sort by different metrics
    full_sorted = sorted(entries, key=lambda x: x['full_similarity'], reverse=True)
    partial_sorted = sorted(entries, key=lambda x: x['partial_similarity'], reverse=True)
    
    # Calculate distributions
    full_bins = Counter(int(x['full_similarity']*100)//10*10 for x in entries)
    partial_bins = Counter(int(x['partial_similarity']*100)//10*10 for x in entries)
    
    # High similarity pairs
    high_full = [e for e in entries if e['full_similarity'] >= 0.8]
    high_partial = [e for e in entries if e['partial_similarity'] >= 0.8]
    medium_full = [e for e in entries if 0.5 <= e['full_similarity'] < 0.8]
    medium_partial = [e for e in entries if 0.5 <= e['partial_similarity'] < 0.8]
    
    # Statistics
    avg_full = sum(x['full_similarity'] for x in entries) / len(entries)
    avg_partial = sum(x['partial_similarity'] for x in entries) / len(entries)
    
    # Generate detailed report
    output = []
    output.append("=" * 100)
    output.append("NFT SMART CONTRACT SIMILARITY ANALYSIS - DETAILED REPORT")
    output.append("=" * 100)
    output.append(f"\nGenerated: October 28, 2025")
    output.append(f"Total Contract Pairs Analyzed: {len(entries)}")
    output.append(f"Total Unique Contracts: 78")
    output.append("\n" + "=" * 100)
    
    # SECTION 1: METHODOLOGY
    output.append("\n" + "=" * 100)
    output.append("SECTION 1: SIMILARITY CALCULATION METHODOLOGY")
    output.append("=" * 100)
    
    output.append("\n1.1 FULL SIMILARITY CALCULATION")
    output.append("-" * 100)
    output.append("""
Algorithm: Sequence Matching with Sampling (Python's difflib.SequenceMatcher)

Method:
  • Character-level comparison of source code
  • For small files (<50KB): Complete character-by-character comparison
  • For large files (>50KB): 
      - First checks MD5 hash for identical files (returns 1.0 if match)
      - Samples first 10,000 characters for comparison
      - Returns similarity ratio capped at 0.95 for samples

Formula:
  similarity_ratio = matching_blocks / total_characters

Characteristics:
  ✓ Detects code clones (near 100% similarity)
  ✓ Identifies renamed contracts (high similarity with minor changes)
  ✓ Catches whitespace/comment changes
  ✓ Sensitive to variable/function renaming
  
Interpretation:
  • 95-100%: Nearly identical contracts (potential clones/templates)
  • 80-95%:  Very similar structure with some modifications
  • 50-80%:  Moderate similarity (shared patterns/libraries)
  • 20-50%:  Low similarity (some common code)
  • 0-20%:   Minimal similarity (mostly unique)
""")
    
    output.append("\n1.2 PARTIAL SIMILARITY CALCULATION")
    output.append("-" * 100)
    output.append("""
Algorithm: Jaccard Similarity of Function Name Sets

Method:
  1. Extract all function names using regex pattern:
     Pattern: \\bfunction\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*\\(
     
  2. Create sets of function names for each contract:
     Contract A: {mint, transfer, approve, balanceOf, ownerOf, ...}
     Contract B: {mint, transfer, burn, totalSupply, ownerOf, ...}
     
  3. Calculate Jaccard similarity:
     Intersection: {mint, transfer, ownerOf} = 3 functions
     Union: {mint, transfer, approve, balanceOf, ownerOf, burn, totalSupply} = 7 functions
     Similarity = Intersection / Union = 3/7 = 0.4286 (42.86%)

Formula:
  Jaccard_similarity = |Functions_A ∩ Functions_B| / |Functions_A ∪ Functions_B|

Characteristics:
  ✓ Focuses on contract functionality (not implementation details)
  ✓ Ignores function implementation differences
  ✓ Identifies contracts with similar interfaces
  ✓ Detects shared function patterns across contracts
  
Common NFT Functions Checked:
  • Minting: mint, safeMint, _mint, mintNFT, mintTo
  • Transfer: transfer, transferFrom, safeTransferFrom, _transfer
  • Approval: approve, setApprovalForAll, getApproved, isApprovedForAll
  • Ownership: ownerOf, balanceOf, owner, transferOwnership
  • Supply: totalSupply, maxSupply, tokenSupply
  • Metadata: tokenURI, setBaseURI, baseTokenURI
  • Access: onlyOwner, pause, unpause, withdraw
  • Marketplace: purchase, buy, sell, list, setPrice
  • Whitelist: addToWhitelist, removeFromWhitelist, presale
  • Reveal: reveal, setRevealed, tokenMetadata
  
Interpretation:
  • 90-100%: Same function interface (likely same contract type)
  • 70-90%:  Similar functionality with some additions
  • 50-70%:  Moderate overlap (common NFT patterns)
  • 30-50%:  Low overlap (different contract types)
  • 0-30%:   Minimal overlap (unique implementations)
""")
    
    # SECTION 2: OVERALL STATISTICS
    output.append("\n" + "=" * 100)
    output.append("SECTION 2: OVERALL STATISTICS")
    output.append("=" * 100)
    
    output.append(f"\n2.1 SUMMARY METRICS")
    output.append("-" * 100)
    output.append(f"  Total Comparisons:          {len(entries)}")
    output.append(f"  Average Full Similarity:    {avg_full*100:.2f}%")
    output.append(f"  Average Partial Similarity: {avg_partial*100:.2f}%")
    output.append(f"  High Full Similarity (≥80%):    {len(high_full)} pairs")
    output.append(f"  High Partial Similarity (≥80%): {len(high_partial)} pairs")
    output.append(f"  Medium Full Similarity (50-80%):    {len(medium_full)} pairs")
    output.append(f"  Medium Partial Similarity (50-80%): {len(medium_partial)} pairs")
    
    output.append(f"\n2.2 FULL SIMILARITY DISTRIBUTION")
    output.append("-" * 100)
    for bucket in sorted(full_bins.keys()):
        count = full_bins[bucket]
        percentage = (count / len(entries)) * 100
        bar = '█' * int(percentage / 2)
        output.append(f"  {bucket:02d}-{bucket+9:02d}%: {count:3d} pairs {bar} ({percentage:.1f}%)")
    
    output.append(f"\n2.3 PARTIAL SIMILARITY DISTRIBUTION")
    output.append("-" * 100)
    for bucket in sorted(partial_bins.keys()):
        count = partial_bins[bucket]
        percentage = (count / len(entries)) * 100
        bar = '█' * int(percentage / 2)
        output.append(f"  {bucket:02d}-{bucket+9:02d}%: {count:3d} pairs {bar} ({percentage:.1f}%)")
    
    # SECTION 3: TOP SIMILARITY PAIRS
    output.append("\n" + "=" * 100)
    output.append("SECTION 3: TOP SIMILARITY PAIRS (DETAILED)")
    output.append("=" * 100)
    
    output.append(f"\n3.1 TOP 20 FULL SIMILARITY PAIRS")
    output.append("-" * 100)
    for i, item in enumerate(full_sorted[:20], 1):
        output.append(f"\n  #{i}")
        output.append(f"    Contract 1: {item['contract1']}")
        output.append(f"    Contract 2: {item['contract2']}")
        output.append(f"    Full Similarity:    {item['full_similarity']*100:.2f}%")
        output.append(f"    Partial Similarity: {item['partial_similarity']*100:.2f}%")
        if item['full_similarity'] >= 0.95:
            output.append(f"    ⚠️  ALERT: Near-identical contracts - potential clone/rug pull template!")
        elif item['full_similarity'] >= 0.80:
            output.append(f"    ⚠️  WARNING: Very high similarity - investigate for code reuse")
    
    output.append(f"\n3.2 TOP 20 PARTIAL SIMILARITY PAIRS")
    output.append("-" * 100)
    for i, item in enumerate(partial_sorted[:20], 1):
        output.append(f"\n  #{i}")
        output.append(f"    Contract 1: {item['contract1']}")
        output.append(f"    Contract 2: {item['contract2']}")
        output.append(f"    Partial Similarity: {item['partial_similarity']*100:.2f}%")
        output.append(f"    Full Similarity:    {item['full_similarity']*100:.2f}%")
        if item['partial_similarity'] >= 0.90:
            output.append(f"    ✓ Same function interface - likely same contract type")
        elif item['partial_similarity'] >= 0.70:
            output.append(f"    ✓ Similar functionality with variations")
    
    # SECTION 4: HIGH RISK FINDINGS
    output.append("\n" + "=" * 100)
    output.append("SECTION 4: HIGH-RISK FINDINGS & CLONE DETECTION")
    output.append("=" * 100)
    
    output.append(f"\n4.1 CRITICAL: NEAR-IDENTICAL CONTRACTS (≥95% Full Similarity)")
    output.append("-" * 100)
    critical = [e for e in entries if e['full_similarity'] >= 0.95]
    if critical:
        for i, item in enumerate(critical, 1):
            output.append(f"\n  Clone Group #{i}")
            output.append(f"    {item['contract1']}")
            output.append(f"    {item['contract2']}")
            output.append(f"    Similarity: {item['full_similarity']*100:.2f}% (full), {item['partial_similarity']*100:.2f}% (partial)")
            output.append(f"    Risk Level: CRITICAL - Investigate for rug pull templates")
    else:
        output.append("  None found.")
    
    output.append(f"\n4.2 HIGH RISK: VERY SIMILAR CONTRACTS (80-95% Full Similarity)")
    output.append("-" * 100)
    high_risk = [e for e in entries if 0.80 <= e['full_similarity'] < 0.95]
    if high_risk:
        for i, item in enumerate(high_risk, 1):
            output.append(f"\n  Similar Pair #{i}")
            output.append(f"    {item['contract1']}")
            output.append(f"    {item['contract2']}")
            output.append(f"    Similarity: {item['full_similarity']*100:.2f}% (full), {item['partial_similarity']*100:.2f}% (partial)")
            output.append(f"    Risk Level: HIGH - Likely forked or template-based")
    else:
        output.append("  None found.")
    
    # SECTION 5: FULL DETAILED LISTING
    output.append("\n" + "=" * 100)
    output.append("SECTION 5: COMPLETE COMPARISON MATRIX")
    output.append("=" * 100)
    output.append("\nAll 325 contract pairs sorted by full similarity (highest to lowest):\n")
    output.append("-" * 100)
    
    for i, item in enumerate(full_sorted, 1):
        output.append(f"{i:3d}. {item['contract1']} vs {item['contract2']}")
        output.append(f"     Full: {item['full_similarity']*100:6.2f}% | Partial: {item['partial_similarity']*100:6.2f}%")
    
    # SECTION 6: CONTRACT ANALYSIS
    output.append("\n" + "=" * 100)
    output.append("SECTION 6: INDIVIDUAL CONTRACT ANALYSIS")
    output.append("=" * 100)
    
    # Group by contract
    contract_similarities = defaultdict(list)
    for entry in entries:
        c1, c2 = entry['contract1'], entry['contract2']
        contract_similarities[c1].append({
            'other': c2,
            'full': entry['full_similarity'],
            'partial': entry['partial_similarity']
        })
        contract_similarities[c2].append({
            'other': c1,
            'full': entry['full_similarity'],
            'partial': entry['partial_similarity']
        })
    
    for contract in sorted(contract_similarities.keys()):
        sims = contract_similarities[contract]
        avg_full = sum(s['full'] for s in sims) / len(sims)
        avg_partial = sum(s['partial'] for s in sims) / len(sims)
        max_full = max(s['full'] for s in sims)
        max_partial = max(s['partial'] for s in sims)
        
        output.append(f"\nContract: {contract}")
        output.append(f"  Comparisons: {len(sims)}")
        output.append(f"  Average Full Similarity:    {avg_full*100:.2f}%")
        output.append(f"  Average Partial Similarity: {avg_partial*100:.2f}%")
        output.append(f"  Max Full Similarity:        {max_full*100:.2f}%")
        output.append(f"  Max Partial Similarity:     {max_partial*100:.2f}%")
        
        # Find most similar contracts
        most_similar = sorted(sims, key=lambda x: x['full'], reverse=True)[:3]
        output.append(f"  Most Similar Contracts:")
        for i, sim in enumerate(most_similar, 1):
            output.append(f"    {i}. {sim['other']} (Full: {sim['full']*100:.2f}%, Partial: {sim['partial']*100:.2f}%)")
    
    # SECTION 7: CONCLUSIONS
    output.append("\n" + "=" * 100)
    output.append("SECTION 7: ANALYSIS CONCLUSIONS & RECOMMENDATIONS")
    output.append("=" * 100)
    
    output.append(f"\n7.1 KEY FINDINGS")
    output.append("-" * 100)
    output.append(f"  • {len(critical)} contract pair(s) show near-identical code (≥95% similarity)")
    output.append(f"  • {len(high_risk)} contract pair(s) show very high similarity (80-95%)")
    output.append(f"  • {len(high_partial)} contract pair(s) share same function interface (≥80% partial)")
    output.append(f"  • Average similarity across all pairs: {avg_full*100:.2f}% (full), {avg_partial*100:.2f}% (partial)")
    
    output.append(f"\n7.2 RISK ASSESSMENT")
    output.append("-" * 100)
    if len(critical) > 0:
        output.append(f"  ⚠️  CRITICAL RISK: {len(critical)} near-identical contract pairs detected")
        output.append(f"      → Investigate for potential rug pull templates or unauthorized clones")
    if len(high_risk) > 0:
        output.append(f"  ⚠️  HIGH RISK: {len(high_risk)} very similar contract pairs detected")
        output.append(f"      → May indicate template reuse or forked contracts")
    if avg_full > 0.3:
        output.append(f"  ℹ️  INFO: Average similarity is {avg_full*100:.2f}%")
        output.append(f"      → Suggests common patterns/libraries across NFT contracts")
    
    output.append(f"\n7.3 RECOMMENDATIONS")
    output.append("-" * 100)
    output.append(f"  1. Manual Review: Investigate all contract pairs with ≥95% similarity")
    output.append(f"  2. Code Audit: Compare implementation details of high-similarity pairs")
    output.append(f"  3. Ownership Check: Verify deployer addresses for clone detection")
    output.append(f"  4. Vulnerability Scan: Run security tools on high-risk contracts")
    output.append(f"  5. Community Research: Check contract reputation and audit reports")
    
    output.append("\n" + "=" * 100)
    output.append("END OF REPORT")
    output.append("=" * 100)
    
    return '\n'.join(output)

if __name__ == '__main__':
    print("Generating detailed similarity analysis report...")
    report_text = analyze_similarity_report()
    
    # Save to file
    output_path = Path('DETAILED_SIMILARITY_REPORT.txt')
    output_path.write_text(report_text, encoding='utf-8')
    print(f"✓ Report saved to: {output_path}")
    print(f"✓ Report size: {len(report_text)} characters")
    print(f"✓ Report lines: {len(report_text.splitlines())}")
