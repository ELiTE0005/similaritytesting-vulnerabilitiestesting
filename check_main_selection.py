import sys
sys.path.append('.')
from slither_analyzer import SlitherAnalyzer
import os
import json

# Read from vulnerability report to get the source code
# Or just test directly
test_json = '''{{
  "language": "Solidity",
  "sources": {
    "@openzeppelin/contracts/token/ERC721/ERC721.sol": {"content": "contract ERC721 { }"},
    "contracts/Tendies.sol": {"content": "pragma solidity ^0.8.0; contract Tendies { }"},
    "contracts/utils/Helper.sol": {"content": "contract Helper { }"}
  }
}}'''

main_file, is_multi, tempdir = SlitherAnalyzer._extract_all_contracts(test_json)

print(f"Main file selected: {main_file}")
print(f"Is multi-file: {is_multi}")

if tempdir and os.path.exists(tempdir):
    print(f"\nFiles extracted:")
    for root, dirs, files in os.walk(tempdir):
        for file in files:
            filepath = os.path.join(root, file)
            relative = os.path.relpath(filepath, tempdir)
            is_main = filepath == main_file
            marker = " ← MAIN FILE" if is_main else ""
            print(f"  {relative}{marker}")
    
    # Cleanup
    import shutil
    shutil.rmtree(tempdir, ignore_errors=True)
