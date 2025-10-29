import json
import time
from etherscan_client import EtherscanClient
from code_similarity import CodeSimilarity
from mythril_analyzer import MythrilAnalyzer

class NFTContractAnalyzer:
    def __init__(self, api_key):
        self.etherscan = EtherscanClient(api_key)
        self.unavailable = []
        self.contracts = {}
        self.addresses = []  # Store addresses for direct bytecode analysis

    def fetch_and_analyze(self, addresses):
        total = len(addresses)
        self.addresses = addresses  # Store for Mythril bytecode analysis
        for idx, addr in enumerate(addresses, 1):
            print(f"[{idx}/{total}] Fetching {addr}...", end=" ", flush=True)
            code = self.etherscan.get_contract_source(addr)
            if not code:
                print("UNAVAILABLE")
                self.unavailable.append(addr)
            else:
                print(f"OK ({len(code)} chars)")
                self.contracts[addr] = code
            # Rate limiting: 5 requests/second max for free tier
            time.sleep(0.25)

    def similarity_report(self):
        report = {}
        addresses = list(self.contracts.keys())
        total_pairs = (len(addresses) * (len(addresses) - 1)) // 2
        pair_num = 0
        print(f"\nCalculating similarity for {total_pairs} contract pairs...")
        for i in range(len(addresses)):
            for j in range(i+1, len(addresses)):
                pair_num += 1
                a1, a2 = addresses[i], addresses[j]
                print(f"[{pair_num}/{total_pairs}] Comparing {a1[:10]}... vs {a2[:10]}...", flush=True)
                code1, code2 = self.contracts[a1], self.contracts[a2]
                full = CodeSimilarity.full_similarity(code1, code2)
                partial = CodeSimilarity.partial_similarity(code1, code2)
                # Use string key for JSON compatibility
                key = f"{a1}_{a2}"
                report[key] = {"contract1": a1, "contract2": a2, "full_similarity": full, "partial_similarity": partial}
        return report

    def vulnerability_report(self, timeout_per_contract=300):
        """
        Run Mythril vulnerability analysis on all contracts.
        Uses bytecode analysis for reliability (works even without source code).
        
        Args:
            timeout_per_contract: Maximum seconds per contract analysis (default: 5 minutes)
        """
        vulns = {}
        # Use all addresses (even those without source code)
        all_addresses = self.addresses if self.addresses else list(self.contracts.keys())
        total = len(all_addresses)
        
        print(f"\n{'='*70}")
        print(f"Running Mythril vulnerability analysis on {total} contracts...")
        print(f"Using bytecode analysis (works without source code)")
        print(f"Timeout per contract: {timeout_per_contract}s (~{timeout_per_contract//60} minutes)")
        print(f"{'='*70}\n")
        
        for idx, addr in enumerate(all_addresses, 1):
            print(f"[{idx}/{total}] Analyzing {addr}...")
            
            # Use bytecode analysis (more reliable than source code)
            result = MythrilAnalyzer.analyze_address(addr, timeout=timeout_per_contract)
            vulns[addr] = result
            
            # Show quick summary
            if result.get("success"):
                issues = result.get("issue_count", 0)
                severity = result.get("severity_breakdown", {})
                high = severity.get("High", 0)
                medium = severity.get("Medium", 0)
                low = severity.get("Low", 0)
                print(f"  ✓ Complete: {issues} issues (🔴{high} 🟡{medium} 🟢{low})")
            else:
                error = result.get("error", "Unknown error")[:50]
                print(f"  ✗ Failed: {error}...")
            
            # Add small delay to avoid overwhelming the system
            time.sleep(1)
        
        print(f"\n{'='*70}")
        print(f"Vulnerability analysis complete!")
        print(f"{'='*70}\n")
        
        return vulns

    def log_unavailable(self, path="unavailable_contracts.txt"):
        with open(path, "w") as f:
            for addr in self.unavailable:
                f.write(addr + "\n")
