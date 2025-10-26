import sys
sys.path.append('.')
import json

# Read vulnerability report to get actual source code
with open('vulnerability_report.json', 'r') as f:
    report = json.load(f)

# Get one of the failing addresses
failing_addr = '0x8f496D935A356077fAA40417881826939bCD5632'

# Fetch it from Etherscan
import requests
r = requests.get('https://api.etherscan.io/api', params={
    'module': 'contract',
    'action': 'getsourcecode',
    'address': failing_addr,
    'apikey': 'YOUR_API_KEY'
})

result = r.json()
if result['status'] == '1' and result['result']:
    source_code = result['result'][0]['SourceCode']
    
    # Parse JSON
    if source_code.startswith('{{'):
        source_code = source_code[1:-1]
    
    try:
        data = json.loads(source_code)
        sources = data.get('sources', {})
        
        print(f"Contract {failing_addr} has {len(sources)} files:")
        for filename in sorted(sources.keys()):
            content = sources[filename].get('content', '')
            has_contract = 'contract ' in content or 'interface ' in content
            is_library = any(lib in filename.lower() for lib in ['@openzeppelin', 'node_modules', '@chainlink'])
            is_in_contracts = 'contracts/' in filename or 'contracts\\' in filename
            
            priority = (not is_library) * 1000 + is_in_contracts * 100 + len(content)
            
            marker = ""
            if has_contract:
                marker += f" [contract, priority={priority}, size={len(content)}]"
            
            print(f"  {filename}{marker}")
        
        # Find highest priority
        candidates = []
        for filename, file_data in sources.items():
            content = file_data.get('content', '')
            if 'contract ' in content or 'interface ' in content:
                is_library = any(lib in filename.lower() for lib in ['@openzeppelin', 'node_modules', '@chainlink'])
                is_in_contracts = 'contracts/' in filename or 'contracts\\' in filename
                priority = (not is_library) * 1000 + is_in_contracts * 100 + len(content)
                candidates.append((priority, filename, len(content)))
        
        candidates.sort(reverse=True, key=lambda x: x[0])
        if candidates:
            print(f"\nTop 3 candidates by priority:")
            for i, (priority, fname, size) in enumerate(candidates[:3]):
                print(f"  {i+1}. {fname} (priority={priority}, size={size})")
            print(f"\n→ SELECTED: {candidates[0][1]}")
    except:
        print(f"Failed to parse JSON")
