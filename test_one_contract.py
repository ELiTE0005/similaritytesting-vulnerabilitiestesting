import sys
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
    
    if temp_dir and os.path.exists(temp_dir):
        print(f"\nAll files:")
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                filepath = os.path.join(root, file)
                relative = os.path.relpath(filepath, temp_dir)
                is_main = filepath == main_file
                marker = " ← MAIN" if is_main else ""
                
                # Get priority info
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    has_contract = 'contract ' in content or 'interface ' in content
                    is_library = any(lib in relative.lower() for lib in ['@openzeppelin', 'node_modules', '@chainlink'])
                    is_in_contracts = 'contracts' + os.sep in relative
                    priority = (not is_library) * 1000 + is_in_contracts * 100 + len(content)
                    
                    if has_contract:
                        print(f"  {relative} (priority={priority}, lib={is_library}, in_contracts={is_in_contracts}, size={len(content)}){marker}")
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
