import json
import time
from etherscan_client import EtherscanClient
from code_similarity import CodeSimilarity
from slither_analyzer import SlitherAnalyzer

class NFTContractAnalyzer:
    def __init__(self, api_key):
        self.etherscan = EtherscanClient(api_key)
        self.unavailable = []
        self.contracts = {}

    def fetch_and_analyze(self, addresses):
        total = len(addresses)
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

    def vulnerability_report(self):
        vulns = {}
        total = len(self.contracts)
        print(f"\nRunning Slither analysis on {total} contracts...")
        for idx, (addr, code) in enumerate(self.contracts.items(), 1):
            print(f"[{idx}/{total}] Analyzing {addr[:10]}...")
            vulns[addr] = SlitherAnalyzer.analyze(code)
        return vulns

    def log_unavailable(self, path="unavailable_contracts.txt"):
        with open(path, "w") as f:
            for addr in self.unavailable:
                f.write(addr + "\n")
