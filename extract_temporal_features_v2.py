"""
Simplified Temporal Feature Extraction for NFT Contracts
Focuses on smart contract transaction activity without requiring creator information
"""

import json
import time
import requests
from datetime import datetime
from collections import defaultdict
from typing import Dict, List

# Load configuration
def load_config():
    """Load API key from config.json"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            return config.get('etherscan_api_key', '')
    except:
        return ''

# Configuration
ETHERSCAN_API_KEY = load_config()
ETHERSCAN_API_URL = 'https://api.etherscan.io/v2/api'  # Using API V2
RATE_LIMIT_DELAY = 0.21  # Slightly more than 5 req/sec to be safe

class SimplifiedTemporalExtractor:
    """Extract temporal features focusing on contract activity"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        
    def get_normal_transactions(self, address: str) -> List[dict]:
        """Get normal ETH transactions for an address"""
        params = {
            'chainid': '1',  # Ethereum mainnet
            'module': 'account',
            'action': 'txlist',
            'address': address,
            'startblock': 0,
            'endblock': 99999999,
            'page': 1,
            'offset': 10000,
            'sort': 'asc',
            'apikey': self.api_key
        }
        
        try:
            time.sleep(RATE_LIMIT_DELAY)
            response = self.session.get(ETHERSCAN_API_URL, params=params, timeout=15)
            data = response.json()
            
            if data['status'] == '1':
                return data['result']
            return []
            
        except Exception as e:
            print(f"    Error fetching normal transactions: {e}")
            return []
    
    def get_internal_transactions(self, address: str) -> List[dict]:
        """Get internal transactions for an address"""
        params = {
            'chainid': '1',  # Ethereum mainnet
            'module': 'account',
            'action': 'txlistinternal',
            'address': address,
            'startblock': 0,
            'endblock': 99999999,
            'page': 1,
            'offset': 10000,
            'sort': 'asc',
            'apikey': self.api_key
        }
        
        try:
            time.sleep(RATE_LIMIT_DELAY)
            response = self.session.get(ETHERSCAN_API_URL, params=params, timeout=15)
            data = response.json()
            
            if data['status'] == '1':
                return data['result']
            return []
            
        except Exception as e:
            print(f"    Error fetching internal transactions: {e}")
            return []
    
    def get_erc721_transfers(self, contract_address: str) -> List[dict]:
        """Get ERC721 token transfer events for a contract"""
        params = {
            'chainid': '1',  # Ethereum mainnet
            'module': 'account',
            'action': 'tokennfttx',
            'contractaddress': contract_address,
            'page': 1,
            'offset': 10000,
            'sort': 'asc',
            'apikey': self.api_key
        }
        
        try:
            time.sleep(RATE_LIMIT_DELAY)
            response = self.session.get(ETHERSCAN_API_URL, params=params, timeout=15)
            data = response.json()
            
            if data['status'] == '1':
                return data['result']
            return []
            
        except Exception as e:
            print(f"    Error fetching ERC721 transfers: {e}")
            return []
    
    def extract_contract_features(self, contract_address: str) -> dict:
        """Extract temporal features for smart contract"""
        print(f"  Fetching contract data...")
        
        # Get contract's transactions
        normal_txs = self.get_normal_transactions(contract_address)
        internal_txs = self.get_internal_transactions(contract_address)
        erc721_transfers = self.get_erc721_transfers(contract_address)
        
        # Find creation time from first transaction
        all_timestamps = []
        for tx in normal_txs + internal_txs:
            ts = int(tx.get('timeStamp', 0))
            if ts > 0:
                all_timestamps.append(ts)
        
        creation_time = min(all_timestamps) if all_timestamps else 0
        
        features = {
            'contract_address': contract_address,
            'creation_timestamp': creation_time,
            'creation_date': datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S') if creation_time else 'Unknown',
            'data_collection': {
                'normal_transactions': len(normal_txs),
                'internal_transactions': len(internal_txs),
                'nft_transfers': len(erc721_transfers),
            },
            'transaction_activity': self._analyze_transactions(normal_txs, internal_txs),
            'nft_activity': self._analyze_nft_activity(erc721_transfers),
            'temporal_patterns': self._analyze_temporal_patterns(normal_txs, internal_txs, erc721_transfers, creation_time),
        }
        
        return features
    
    def _analyze_transactions(self, normal_txs: List[dict], internal_txs: List[dict]) -> dict:
        """Analyze contract transaction patterns"""
        # Method signatures
        method_categories = {
            'mint': ['0x40c10f19', '0xa0712d68', '0x1249c58b'],
            'burn': ['0x42966c68', '0x9dc29fac'],
            'withdraw': ['0x3ccfd60b', '0x2e1a7d4d', '0x51cff8d9'],
            'transfer': ['0xa9059cbb', '0x23b872dd', '0x42842e0e'],
            'approve': ['0x095ea7b3', '0xa22cb465'],
        }
        
        activity = defaultdict(int)
        
        for tx in normal_txs:
            method_id = tx.get('input', '')[:10]
            for category, methods in method_categories.items():
                if method_id in methods:
                    activity[category] += 1
        
        # ETH movements
        eth_in = sum(int(tx.get('value', 0)) for tx in normal_txs if tx.get('to', '').lower() == tx.get('contractAddress', '').lower() if tx.get('value'))
        eth_out = sum(int(tx.get('value', 0)) for tx in internal_txs if tx.get('from', '').lower() != '' if tx.get('value'))
        
        return {
            'mint_transactions': activity.get('mint', 0),
            'burn_transactions': activity.get('burn', 0),
            'withdraw_transactions': activity.get('withdraw', 0),
            'transfer_transactions': activity.get('transfer', 0),
            'approve_transactions': activity.get('approve', 0),
            'eth_received_wei': eth_in,
            'eth_sent_wei': eth_out,
            'net_eth_wei': eth_in - eth_out,
        }
    
    def _analyze_nft_activity(self, transfers: List[dict]) -> dict:
        """Analyze NFT transfer activity"""
        if not transfers:
            return {
                'total_transfers': 0,
                'unique_tokens': 0,
                'unique_senders': 0,
                'unique_receivers': 0,
                'mint_events': 0,
                'burn_events': 0,
                'secondary_transfers': 0,
            }
        
        unique_tokens = set()
        unique_senders = set()
        unique_receivers = set()
        
        mint_count = 0
        burn_count = 0
        
        for transfer in transfers:
            token_id = transfer.get('tokenID', '')
            from_addr = transfer.get('from', '').lower()
            to_addr = transfer.get('to', '').lower()
            
            unique_tokens.add(token_id)
            unique_senders.add(from_addr)
            unique_receivers.add(to_addr)
            
            if from_addr == '0x0000000000000000000000000000000000000000':
                mint_count += 1
            if to_addr == '0x0000000000000000000000000000000000000000':
                burn_count += 1
        
        return {
            'total_transfers': len(transfers),
            'unique_tokens_transferred': len(unique_tokens),
            'unique_senders': len(unique_senders),
            'unique_receivers': len(unique_receivers),
            'mint_events': mint_count,
            'burn_events': burn_count,
            'secondary_transfers': len(transfers) - mint_count - burn_count,
        }
    
    def _analyze_temporal_patterns(self, normal_txs: List[dict], 
                                   internal_txs: List[dict], 
                                   nft_transfers: List[dict],
                                   creation_time: int) -> dict:
        """Analyze temporal patterns for contract activity"""
        all_timestamps = []
        
        for tx in normal_txs + internal_txs + nft_transfers:
            ts = int(tx.get('timeStamp', 0))
            if ts > 0:
                all_timestamps.append(ts)
        
        if not all_timestamps:
            return {
                'contract_age_days': 0,
                'total_activity_days': 0,
                'avg_daily_transactions': 0,
            }
        
        all_timestamps.sort()
        
        # Calculate age
        current_time = int(time.time())
        age_days = (current_time - creation_time) / 86400 if creation_time > 0 else 0
        
        # Calculate activity
        unique_days = set()
        hourly_dist = defaultdict(int)
        
        for ts in all_timestamps:
            dt = datetime.fromtimestamp(ts)
            unique_days.add(dt.strftime('%Y-%m-%d'))
            hourly_dist[dt.hour] += 1
        
        # Activity bursts
        daily_counts = defaultdict(int)
        for ts in all_timestamps:
            dt = datetime.fromtimestamp(ts)
            daily_counts[dt.strftime('%Y-%m-%d')] += 1
        
        avg_daily = sum(daily_counts.values()) / len(daily_counts) if daily_counts else 0
        burst_days = sum(1 for count in daily_counts.values() if count > avg_daily * 2)
        
        return {
            'contract_age_days': round(age_days, 2),
            'first_activity': min(all_timestamps),
            'first_activity_date': datetime.fromtimestamp(min(all_timestamps)).strftime('%Y-%m-%d %H:%M:%S'),
            'last_activity': max(all_timestamps),
            'last_activity_date': datetime.fromtimestamp(max(all_timestamps)).strftime('%Y-%m-%d %H:%M:%S'),
            'total_activity_days': len(unique_days),
            'avg_daily_transactions': round(len(all_timestamps) / age_days, 2) if age_days > 0 else 0,
            'hourly_distribution': dict(hourly_dist),
            'burst_activity_days': burst_days,
            'activity_ratio': round(len(unique_days) / age_days, 4) if age_days > 0 else 0,
        }


def main():
    """Main execution function"""
    
    print("=" * 80)
    print("SIMPLIFIED TEMPORAL FEATURE EXTRACTION")
    print("=" * 80)
    print()
    
    # Load contract addresses
    with open('contracts.txt', 'r') as f:
        contract_addresses = [line.strip() for line in f if line.strip()]
    
    print(f"Loaded {len(contract_addresses)} contract addresses\n")
    
    # Initialize extractor
    extractor = SimplifiedTemporalExtractor(ETHERSCAN_API_KEY)
    
    # Storage for results
    temporal_features = {
        'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_contracts': len(contract_addresses),
        'contracts': {}
    }
    
    # Process each contract
    for idx, contract_address in enumerate(contract_addresses, 1):
        print(f"[{idx}/{len(contract_addresses)}] Processing {contract_address}...")
        
        try:
            # Extract contract features
            contract_features = extractor.extract_contract_features(contract_address)
            
            temporal_features['contracts'][contract_address] = contract_features
            
            print(f"  ✓ Features extracted")
            print(f"     Transactions: {contract_features['data_collection']['normal_transactions']}")
            print(f"     NFT Transfers: {contract_features['data_collection']['nft_transfers']}")
            print()
            
        except Exception as e:
            print(f"  ✗ Error processing {contract_address}: {e}")
            temporal_features['contracts'][contract_address] = {
                'error': str(e)
            }
            print()
    
    # Save results
    output_file = 'temporal_features.json'
    with open(output_file, 'w') as f:
        json.dump(temporal_features, f, indent=2)
    
    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\n✓ Results saved to: {output_file}")
    print(f"✓ Contracts processed: {len(temporal_features['contracts'])}")
    
    # Count success
    successful = sum(1 for v in temporal_features['contracts'].values() if 'error' not in v)
    failed = len(temporal_features['contracts']) - successful
    
    print(f"✓ Successful: {successful}")
    print(f"✗ Failed: {failed}")
    print()


if __name__ == '__main__':
    main()
