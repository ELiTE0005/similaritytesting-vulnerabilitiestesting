"""Test JSON extraction from Etherscan responses"""
import json
from etherscan_client import EtherscanClient
from slither_analyzer import SlitherAnalyzer

# Load API key
with open("config.json") as f:
    config = json.load(f)

client = EtherscanClient(config["etherscan_api_key"])

# Test with a contract that has JSON format
test_addresses = [
    "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D",  # BAYC (flattened)
    "0x8f496D935A356077fAA40417881826939bCD5632",  # Another NFT
    "0x23581767a106ae21c074b2276D25e5C3e136a68b",  # Moonbirds
]

for test_address in test_addresses:
    print(f"\n{'='*60}")
    print(f"Testing: {test_address}")
    print('='*60)

for test_address in test_addresses:
    print(f"\n{'='*60}")
    print(f"Testing: {test_address}")
    print('='*60)

    code = client.get_contract_source(test_address)
    if code:
        print(f"\nOriginal response length: {len(code)} chars")
        print(f"Starts with: {code[:100]}")
        
        # Extract main contract
        processed = SlitherAnalyzer._extract_main_contract(code)
        print(f"\nProcessed length: {len(processed)} chars")
        print(f"Starts with: {processed[:200]}")
        
        # Check if it's valid Solidity
        if processed.strip().startswith(('pragma', 'contract', 'interface', 'library', '//', '/*')):
            print("\n✓ Successfully extracted valid Solidity code!")
        else:
            print("\n✗ Still not valid Solidity format")
            print(f"First 500 chars:\n{processed[:500]}")
    else:
        print("Failed to fetch contract")
