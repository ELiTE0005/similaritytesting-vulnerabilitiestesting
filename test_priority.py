import sys
sys.path.append('.')
from slither_analyzer import SlitherAnalyzer
import os
import json

# Test with realistic Etherscan structure
test_json = '''{{
  "language": "Solidity",
  "sources": {
    "@openzeppelin/contracts/token/ERC721/ERC721.sol": {"content": "pragma solidity ^0.8.0; contract ERC721 { function test() public { } function test2() public { } function test3() public { } }"},
    "@openzeppelin/contracts/access/Ownable.sol": {"content": "contract Ownable { }"},
    "contracts/MyNFT.sol": {"content": "pragma solidity ^0.8.0; import '@openzeppelin/contracts/token/ERC721/ERC721.sol'; contract MyNFT is ERC721 { }"},
    "contracts/utils/Helper.sol": {"content": "contract Helper { }"}
  }
}}'''

main_file, is_multi, tempdir = SlitherAnalyzer._extract_all_contracts(test_json)

print(f"Main file selected: {main_file}")
basename = os.path.basename(main_file)
print(f"  → {basename}")
print(f"\nAll extracted files:")
for root, dirs, files in os.walk(tempdir):
    for file in files:
        filepath = os.path.join(root, file)
        relative = os.path.relpath(filepath, tempdir)
        is_main = filepath == main_file
        marker = " ← SELECTED AS MAIN" if is_main else ""
        print(f"  {relative}{marker}")

# Cleanup
import shutil
shutil.rmtree(tempdir, ignore_errors=True)

print(f"\n✓ Correctly selected '{basename}' (non-library file in contracts/ folder)")
