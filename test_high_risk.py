"""Test if we can find high-risk contracts from similarity report."""
import json

# Load similarity report
with open('similarity_report.json') as f:
    sim_report = json.load(f)

# Find high similarity pairs (>= 95%)
high_sim_pairs = []
contract_risk = {}

for pair_key, pair_data in sim_report.items():
    if isinstance(pair_data, dict):
        full_sim = pair_data.get('full_similarity', 0)
        partial_sim = pair_data.get('partial_similarity', 0)
        
        if full_sim >= 0.95 or partial_sim >= 0.95:
            addr1 = pair_data.get('contract1', '')
            addr2 = pair_data.get('contract2', '')
            risk_score = max(full_sim, partial_sim)
            
            high_sim_pairs.append((addr1, addr2, full_sim * 100, partial_sim * 100))
            
            if addr1:
                contract_risk[addr1] = max(contract_risk.get(addr1, 0), risk_score)
            if addr2:
                contract_risk[addr2] = max(contract_risk.get(addr2, 0), risk_score)

print(f"Total pairs in report: {len(sim_report)}")
print(f"High-risk pairs (>= 95%): {len(high_sim_pairs)}")
print(f"Unique high-risk contracts: {len(contract_risk)}")

if high_sim_pairs:
    print(f"\nFirst 10 high-risk pairs:")
    for addr1, addr2, full, partial in high_sim_pairs[:10]:
        print(f"  {addr1[:10]}... ↔ {addr2[:10]}...")
        print(f"    Full: {full:.1f}%, Partial: {partial:.1f}%")
