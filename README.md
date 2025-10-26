# NFT Smart Contract Analyzer

This project collects smart contract codes of NFT creators, analyzes them for code similarity (to detect rug pulls and reused patterns), checks for smart contract vulnerabilities using Slither, and records contracts unavailable on Etherscan.

## Features
- Fetch contract source code from Etherscan API
- Analyze complete and partial code similarity
- Detect smart contract vulnerabilities using Slither
- Record unavailable contracts
- CLI/script orchestrates the workflow

## Requirements
- Python 3.8+
- Etherscan API key
- Slither (installed and available in PATH)

## Setup
1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Provide your Etherscan API key either:
	- In `config.json` under `etherscan_api_key`, or
	- As an environment variable `ETHERSCAN_API_KEY`
4. Ensure Slither CLI is available. If installed to the project venv, it will be auto-detected.

## Usage
Run the main script to start analysis:
```
python main.py --input contracts.txt
```

PowerShell (Windows) one-liners:
```
$env:ETHERSCAN_API_KEY = "<your_api_key>"
.venv\Scripts\python.exe main.py --input contracts.txt
```

## Output
- **similarity_report.json**: Pairwise full and partial similarity for fetched contracts ✅ **WORKS PERFECTLY**
- **vulnerability_report.json**: Slither output per contract ⚠️ **LIMITED** (see Known Limitations below)
- **unavailable_contracts.txt**: Addresses with no verified source or retrieval failure

## Known Limitations

### Slither Vulnerability Analysis
The Slither integration has known limitations when analyzing real-world contracts:

1. **Multi-File Contracts**: Etherscan often returns contracts as JSON bundles containing multiple files (e.g., `{"ERC721.sol": {...}, "Address.sol": {...}}`). Current implementation passes this to Slither as-is, which expects single `.sol` files.

2. **Compiler Version Mismatch**: Project uses `solc 0.8.19`, but NFT contracts use various versions (`^0.6.0`, `^0.7.6`, `>=0.6.0 <0.8.0`). Slither compilation fails due to pragma mismatches.

3. **Success Rate**: Similarity analysis works on 100% of fetched contracts, but Slither successfully compiles only a small percentage.

### Code Similarity Analysis (Primary Feature)
✅ **Fully functional** - successfully detects:
- Complete code duplication (rug pull detection)
- Partial function pattern reuse (shared templates)
- Works on all contract sizes with automatic sampling optimization

### Recommendations for Production Use
For comprehensive vulnerability scanning:
- Install `solc-select` to manage multiple Solidity compiler versions
- Pre-process Etherscan JSON responses to extract individual files
- Consider bytecode-level analysis tools (Mythril, Manticore) that don't require source compilation
- Use dedicated contract security platforms (OpenZeppelin Defender, CertiK)

## Results
See `ANALYSIS_RESULTS.md` for detailed analysis of the sample run.

## License
MIT
