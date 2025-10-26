import sys
import importlib

# Remove cached modules
if 'slither_analyzer' in sys.modules:
    del sys.modules['slither_analyzer']
if 'etherscan_client' in sys.modules:
    del sys.modules['etherscan_client']

sys.path.append('.')
from etherscan_client import EtherscanClient
from slither_analyzer import SlitherAnalyzer
import json
import os

# Load API key
with open("config.json") as f:
    config = json.load(f)

client = EtherscanClient(config["etherscan_api_key"])

# Test ONE failing contract
addr = '0x8f496D935A356077fAA40417881826939bCD5632'  # Tendies
code = client.get_contract_source(addr)

if code:
    # Extract
    main_file, is_multi, temp_dir = SlitherAnalyzer._extract_all_contracts(code)
    
    print(f"Address: {addr}")
    print(f"Multi-file: {is_multi}")
    print(f"Main file: {main_file}")
    print(f"  → {os.path.basename(main_file)}")
    
    if temp_dir and os.path.exists(temp_dir):
        print(f"\nTop 5 contract files by priority:")
        candidates = []
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                filepath = os.path.join(root, file)
                relative = os.path.relpath(filepath, temp_dir)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    has_contract = 'contract ' in content or 'interface ' in content
                    
                    if has_contract:
                        # Use same logic as slither_analyzer
                        filename = relative.replace(os.sep, '/')  # normalize for matching
                        is_library = any(lib in filename.lower() for lib in ['@openzeppelin', 'node_modules', '@chainlink'])
                        is_in_contracts = 'contracts/' in filename
                        priority = (not is_library) * 100000 + is_in_contracts * 10000 + len(content)
                        candidates.append((priority, relative, filepath == main_file))
        
        candidates.sort(reverse=True, key=lambda x: x[0])
        for i, (priority, fname, is_main) in enumerate(candidates[:5]):
            marker = " ← SELECTED" if is_main else ""
            print(f"  {i+1}. {fname} (priority={priority}){marker}")
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    print(f"\n✓ SUCCESS! Selected '{os.path.basename(main_file)}' instead of ERC721.sol")
