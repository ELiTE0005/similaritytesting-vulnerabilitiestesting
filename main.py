import json
import os
import argparse
from nft_contract_analyzer import NFTContractAnalyzer

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NFT Smart Contract Analyzer")
    parser.add_argument("--input", required=True, help="Path to file with contract addresses (one per line)")
    args = parser.parse_args()

    with open("config.json") as f:
        config = json.load(f)
    api_key = config.get("etherscan_api_key") or os.environ.get("ETHERSCAN_API_KEY")
    analyzer = NFTContractAnalyzer(api_key or "")

    with open(args.input) as f:
        # Read addresses, ignore blank lines and comments
        addresses = [
            line.strip()
            for line in f
            if line.strip() and not line.strip().startswith("#")
        ]

    analyzer.fetch_and_analyze(addresses)
    analyzer.log_unavailable()

    sim_report = analyzer.similarity_report()
    vuln_report = analyzer.vulnerability_report()

    with open("similarity_report.json", "w") as f:
        json.dump(sim_report, f, indent=2)
    with open("vulnerability_report.json", "w") as f:
        json.dump(vuln_report, f, indent=2)

    print("Analysis complete. See output files for details.")
