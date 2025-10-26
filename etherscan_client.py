import requests
import json

class EtherscanClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.etherscan.io/v2/api"

    def get_contract_source(self, address):
        params = {
            "chainid": "1",  # Ethereum mainnet
            "module": "contract",
            "action": "getsourcecode",
            "address": address,
            "apikey": self.api_key
        }
        try:
            resp = requests.get(self.base_url, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return None
        if data.get("status") == "1" and data.get("result"):
            src = data["result"][0].get("SourceCode")
            if src:
                return src
        return None
