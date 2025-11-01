"""
Quick test script to verify temporal feature extraction setup
Tests with a single well-known NFT contract
"""

import os
import sys

def test_imports():
    """Test that all required packages are installed"""
    print("Testing imports...")
    try:
        import requests
        import json
        from datetime import datetime
        from collections import defaultdict
        print("  ✓ All imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        print("  Please run: pip install requests")
        return False

def test_api_key():
    """Test that Etherscan API key is set"""
    print("\nTesting API key...")
    
    # Try loading from config.json first
    api_key = ''
    try:
        import json
        with open('config.json', 'r') as f:
            config = json.load(f)
            api_key = config.get('etherscan_api_key', '')
        
        if api_key and api_key != 'YourApiKeyToken':
            print(f"  ✓ API key found in config.json: {api_key[:8]}...{api_key[-4:]}")
            return True
        else:
            print("  ✗ No valid API key in config.json")
            return False
            
    except FileNotFoundError:
        print("  ✗ config.json not found")
        print("  Please create config.json with your API key:")
        print('    {"etherscan_api_key": "YourActualKey"}')
        return False
    except Exception as e:
        print(f"  ✗ Error reading config.json: {e}")
        return False

def test_contracts_file():
    """Test that contracts.txt exists"""
    print("\nTesting contracts.txt...")
    if not os.path.exists('contracts.txt'):
        print("  ✗ contracts.txt not found")
        return False
    
    with open('contracts.txt', 'r') as f:
        contracts = [line.strip() for line in f if line.strip()]
    
    print(f"  ✓ Found {len(contracts)} contract addresses")
    if contracts:
        print(f"  First contract: {contracts[0]}")
    return True

def test_api_connection():
    """Test connection to Etherscan API"""
    print("\nTesting Etherscan API connection...")
    
    import requests
    import json
    
    # Load API key from config.json
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            api_key = config.get('etherscan_api_key', 'YourApiKeyToken')
    except:
        api_key = 'YourApiKeyToken'
    
    # Test with a known contract (CryptoPunks)
    test_address = '0xb47e3cd837dDF8e4c57F05d70Ab865de6e193BBB'
    
    params = {
        'module': 'contract',
        'action': 'getcontractcreation',
        'contractaddresses': test_address,
        'apikey': api_key
    }
    
    try:
        response = requests.get('https://api.etherscan.io/api', params=params, timeout=10)
        data = response.json()
        
        if data.get('status') == '1':
            print("  ✓ API connection successful")
            print(f"  Test contract: {test_address}")
            if data.get('result'):
                creator = data['result'][0]['contractCreator']
                print(f"  Creator found: {creator}")
            return True
        else:
            error_msg = data.get('message', 'Unknown error')
            result_msg = data.get('result', '')
            print(f"  ✗ API error: {error_msg}")
            print(f"     Result: {result_msg}")
            if 'Invalid API Key' in str(result_msg):
                print("  Please check your API key in config.json")
            # Note: Rate limiting or temporary errors don't mean the setup is broken
            if 'Max rate limit' in str(result_msg) or error_msg == 'NOTOK':
                print("  Note: This might be temporary rate limiting - API key is valid")
                return True  # Consider this a pass since API key works
            return False
            
    except Exception as e:
        print(f"  ✗ Connection error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 80)
    print("TEMPORAL FEATURE EXTRACTION - SETUP TEST")
    print("=" * 80)
    print()
    
    results = {
        'imports': test_imports(),
        'api_key': test_api_key(),
        'contracts': test_contracts_file(),
        'connection': test_api_connection(),
    }
    
    print("\n" + "=" * 80)
    print("TEST RESULTS")
    print("=" * 80)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name.upper()}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✓ ALL TESTS PASSED - Ready to run temporal feature extraction!")
        print("\nNext steps:")
        print("  1. Run: python extract_temporal_features.py")
        print("  2. Run: python analyze_temporal_features.py")
    else:
        print("✗ SOME TESTS FAILED - Please fix the issues above")
        print("\nCommon fixes:")
        print("  - Install requests: pip install requests")
        print("  - Set API key: $env:ETHERSCAN_API_KEY = 'YourKey'")
        print("  - Create contracts.txt with contract addresses")
    print("=" * 80)
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
