import sys
sys.path.append('.')
from slither_analyzer import SlitherAnalyzer
import requests
import os

# Test Tendies contract
r = requests.get('https://api.etherscan.io/api', params={
    'module': 'contract',
    'action': 'getsourcecode',
    'address': '0x8f496D935A356077fAA40417881826939bCD5632',
    'apikey': 'YOUR_API_KEY'
})

code = r.json()['result'][0]['SourceCode']
main_file, is_multi, tempdir = SlitherAnalyzer._extract_all_contracts(code)

print(f"Main file selected: {main_file}")
print(f"Is multi-file: {is_multi}")

if tempdir and os.path.exists(tempdir):
    print(f"\nFiles in temp directory:")
    for root, dirs, files in os.walk(tempdir):
        level = root.replace(tempdir, '').count(os.sep)
        indent = ' ' * 2 * level
        folder = os.path.basename(root)
        print(f'{indent}{folder}/')
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            if file.endswith('.sol'):
                filepath = os.path.join(root, file)
                size = os.path.getsize(filepath)
                # Check if it contains "contract" keyword
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    has_contract = "contract " in content or "interface " in content
                    is_main = filepath == main_file
                    marker = " ← MAIN" if is_main else ""
                    marker += " (has contract)" if has_contract else ""
                    print(f'{subindent}{file} ({size} bytes){marker}')
