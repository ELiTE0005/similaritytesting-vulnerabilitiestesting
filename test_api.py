import requests
import json


# Load the API key from config
with open("config.json") as f:
    config = json.load(f)

api_key = config["etherscan_api_key"]

# Test 1: Get a verified contract (CryptoKitties - one of the first NFTs)
test_address = "0x06012c8cf97BEaD5deAe237070F9587f8E7A266d"

print("Testing Etherscan API key...")
print(f"API Key: {api_key[:10]}...{api_key[-4:]}")
print(f"Test Address: {test_address}")
print("-" * 60)

params = {
    "chainid": "1",  # Ethereum mainnet
    "module": "contract",
    "action": "getsourcecode",
    "address": test_address,
    "apikey": api_key
}

try:
    response = requests.get("https://api.etherscan.io/v2/api", params=params, timeout=20)
    response.raise_for_status()
    data = response.json()
    
    print(f"Status: {data.get('status')}")
    print(f"Message: {data.get('message')}")
    
    if data.get("status") == "1" and data.get("result"):
        result = data["result"][0]
        contract_name = result.get("ContractName")
        source_code = result.get("SourceCode", "")
        
        print(f"\n✅ API Key Works!")
        print(f"Contract Name: {contract_name}")
        print(f"Source Code Length: {len(source_code)} characters")
        print(f"First 200 chars of source:\n{source_code[:200]}...")
    else:
        print(f"\n❌ API Key Issue or Contract Not Verified")
        print(f"Full Response: {json.dumps(data, indent=2)}")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
