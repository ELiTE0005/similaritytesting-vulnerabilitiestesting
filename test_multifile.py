"""Test multi-file extraction from Etherscan responses"""
import json
import os
from etherscan_client import EtherscanClient
from slither_analyzer import SlitherAnalyzer

# Load API key
with open("config.json") as f:
    config = json.load(f)

client = EtherscanClient(config["etherscan_api_key"])

# Test with contracts that have JSON format
test_addresses = [
    ("0x8f496D935A356077fAA40417881826939bCD5632", "Tendies (Multi-file JSON)"),
    ("0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D", "BAYC (Flattened)"),
]

for test_address, name in test_addresses:
    print(f"\n{'='*70}")
    print(f"Testing: {name}")
    print(f"Address: {test_address}")
    print('='*70)

    code = client.get_contract_source(test_address)
    if code:
        print(f"\nOriginal response length: {len(code)} chars")
        print(f"Starts with: {code[:60]}...")
        
        # Extract all contracts
        main_file, is_multi, temp_dir = SlitherAnalyzer._extract_all_contracts(code)
        
        if is_multi:
            print(f"\n✓ Multi-file contract detected!")
            print(f"  Temp directory: {temp_dir}")
            print(f"  Main contract: {main_file}")
            
            # List all extracted files
            if temp_dir and os.path.exists(temp_dir):
                print(f"\n  Extracted files:")
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, temp_dir)
                        size = os.path.getsize(file_path)
                        print(f"    - {rel_path} ({size} bytes)")
                
                # Read main file
                with open(main_file, 'r', encoding='utf-8') as f:
                    main_content = f.read()
                print(f"\n  Main contract starts with:")
                print(f"  {main_content[:200]}...")
                
                # Cleanup
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
        else:
            print(f"\n✓ Single file contract")
            print(f"  Content starts with: {main_file[:200]}...")
    else:
        print("Failed to fetch contract")

print(f"\n{'='*70}")
print("Test complete!")
print('='*70)
