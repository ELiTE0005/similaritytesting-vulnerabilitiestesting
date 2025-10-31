"""
Convert Etherscan Standard JSON Input contracts to flattened Solidity files.
This script processes all .sol files in retrieved_contracts that are actually JSON format
and converts them to flat Solidity files that Slither can analyze.
"""

import json
import os
from pathlib import Path


def is_json_format(file_path):
    """Check if a file is in JSON format."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            first_char = f.read(1)
            return first_char == '{'
    except:
        return False


def extract_flatten_from_json(json_file_path):
    """
    Extract and flatten Solidity code from Etherscan Standard JSON Input format.
    Returns the flattened source code as a string.
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Handle double curly braces at the start (Etherscan wrapping)
        if content.startswith('{{'):
            content = content[1:-1]  # Remove outer braces
        
        data = json.loads(content)
        
        if 'sources' not in data:
            return None
        
        # Collect all source codes
        all_sources = []
        seen_licenses = set()
        main_pragma = None
        
        for filename, file_data in data['sources'].items():
            source_code = file_data.get('content', '')
            if not source_code:
                continue
            
            # Process line by line to remove duplicate SPDX, pragmas, and imports
            lines = source_code.split('\n')
            processed_lines = []
            
            for line in lines:
                stripped = line.strip()
                
                # Skip SPDX license identifiers (we'll add one at the top)
                if 'SPDX-License-Identifier' in stripped:
                    if stripped not in seen_licenses:
                        seen_licenses.add(stripped)
                    continue
                
                # Capture first pragma solidity statement
                if stripped.startswith('pragma solidity') and main_pragma is None:
                    main_pragma = line
                    continue
                
                # Skip other pragma solidity statements to avoid duplicates
                if stripped.startswith('pragma solidity'):
                    continue
                
                # Skip import statements since we're flattening everything
                if stripped.startswith('import '):
                    continue
                
                processed_lines.append(line)
            
            if processed_lines:
                all_sources.append({
                    'filename': filename,
                    'content': '\n'.join(processed_lines)
                })
        
        if not all_sources:
            return None
        
        # Build flattened output
        flattened_code = []
        
        # Add single SPDX license (use MIT as default if multiple or none found)
        if seen_licenses:
            # Use the first license found, or MIT if multiple
            first_license = list(seen_licenses)[0] if len(seen_licenses) == 1 else "// SPDX-License-Identifier: MIT"
            flattened_code.append(first_license)
        else:
            flattened_code.append("// SPDX-License-Identifier: MIT")
        
        flattened_code.append("")
        
        # Add single pragma
        if main_pragma:
            flattened_code.append(main_pragma)
        else:
            flattened_code.append("pragma solidity ^0.8.0;")
        
        flattened_code.append("")
        flattened_code.append("// File flattened from Etherscan Standard JSON Input")
        flattened_code.append("// Multiple source files have been concatenated")
        flattened_code.append("")
        
        # Add all source files
        for source in all_sources:
            flattened_code.append(f"// File: {source['filename']}")
            flattened_code.append(source['content'])
            flattened_code.append("")
        
        return '\n'.join(flattened_code)
    
    except Exception as e:
        print(f"Error processing {json_file_path}: {str(e)}")
        return None


def main():
    """Convert all JSON-format contracts to flattened Solidity."""
    contracts_dir = "retrieved_contracts"
    
    if not os.path.exists(contracts_dir):
        print(f"Error: Directory '{contracts_dir}' not found")
        return
    
    sol_files = list(Path(contracts_dir).glob("*.sol"))
    total_files = len(sol_files)
    json_format_count = 0
    converted_count = 0
    failed_count = 0
    
    print("="*80)
    print("CONVERTING JSON-FORMAT CONTRACTS TO FLATTENED SOLIDITY")
    print("="*80)
    print()
    print(f"Found {total_files} .sol files in {contracts_dir}/")
    print()
    
    for sol_file in sol_files:
        if is_json_format(sol_file):
            json_format_count += 1
            print(f"[{json_format_count}] Converting: {sol_file.name}")
            
            # Extract flattened code
            flattened_code = extract_flatten_from_json(sol_file)
            
            if flattened_code:
                # Write flattened code back to the same file
                try:
                    with open(sol_file, 'w', encoding='utf-8') as f:
                        f.write(flattened_code)
                    converted_count += 1
                    print(f"    ✓ Successfully converted")
                except Exception as e:
                    failed_count += 1
                    print(f"    ✗ Failed to write: {str(e)}")
            else:
                failed_count += 1
                print(f"    ✗ Failed to extract code")
    
    print()
    print("="*80)
    print("CONVERSION COMPLETE")
    print("="*80)
    print()
    print(f"📊 Total files scanned: {total_files}")
    print(f"📋 JSON-format files found: {json_format_count}")
    print(f"✅ Successfully converted: {converted_count}")
    print(f"❌ Failed to convert: {failed_count}")
    print(f"📁 Plain Solidity files (no conversion needed): {total_files - json_format_count}")
    print()
    
    if converted_count > 0:
        print("✓ Contracts have been converted and can now be analyzed with Slither")
    print("="*80)


if __name__ == "__main__":
    main()
