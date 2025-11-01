"""
Temporal Feature Extraction for NFT Contracts
Extracts temporal features from:
1. Creator's transaction activity (transfer, approve, etc.)
2. Smart contract transaction activity (withdraw, mint, burn, etc.)
"""

import json
import time
import requests
from datetime import datetime
from collections import defaultdict
import os
from typing import Dict, List, Tuple

# Load configuration
def load_config():
    """Load API key from config.json"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            return config.get('etherscan_api_key', '')
    except FileNotFoundError:
        print("Warning: config.json not found, trying environment variable...")
        return os.getenv('ETHERSCAN_API_KEY', 'YourApiKeyToken')
    except json.JSONDecodeError:
        print("Error: Invalid JSON in config.json")
        return ''

# Configuration
ETHERSCAN_API_KEY = load_config()
ETHERSCAN_API_URL = 'https://api.etherscan.io/api'
RATE_LIMIT_DELAY = 0.2  # 5 requests per second

class TemporalFeatureExtractor:
    """Extract temporal features from blockchain transactions"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        
    def get_contract_creator(self, contract_address: str) -> Tuple[str, int]:
        """
        Get contract creator address and creation timestamp
        Returns: (creator_address, creation_timestamp)
        """
        params = {
            'module': 'contract',
            'action': 'getcontractcreation',
            'contractaddresses': contract_address,
            'apikey': self.api_key
        }
        
        try:
            response = self.session.get(ETHERSCAN_API_URL, params=params, timeout=10)
            data = response.json()
            
            if data['status'] == '1' and data['result']:
                creator_info = data['result'][0]
                creator_address = creator_info['contractCreator']
                creation_tx = creator_info['txHash']
                
                # Get creation transaction details for timestamp
                tx_details = self.get_transaction_details(creation_tx)
                creation_timestamp = int(tx_details.get('timeStamp', 0))
                
                return creator_address, creation_timestamp
            
            return None, 0
            
        except Exception as e:
            print(f"  ✗ Error getting creator for {contract_address}: {e}")
            return None, 0
    
    def get_transaction_details(self, tx_hash: str) -> dict:
        """Get transaction details by hash"""
        params = {
            'module': 'proxy',
            'action': 'eth_getTransactionByHash',
            'txhash': tx_hash,
            'apikey': self.api_key
        }
        
        try:
            response = self.session.get(ETHERSCAN_API_URL, params=params, timeout=10)
            data = response.json()
            
            if 'result' in data:
                # Get block details for timestamp
                block_number = int(data['result']['blockNumber'], 16)
                block_info = self.get_block_by_number(block_number)
                return {'timeStamp': int(block_info.get('timestamp', '0'), 16)}
            
            return {}
            
        except Exception as e:
            return {}
    
    def get_block_by_number(self, block_number: int) -> dict:
        """Get block information by block number"""
        params = {
            'module': 'proxy',
            'action': 'eth_getBlockByNumber',
            'tag': hex(block_number),
            'boolean': 'false',
            'apikey': self.api_key
        }
        
        try:
            response = self.session.get(ETHERSCAN_API_URL, params=params, timeout=10)
            data = response.json()
            return data.get('result', {})
        except:
            return {}
    
    def get_normal_transactions(self, address: str, start_block: int = 0) -> List[dict]:
        """Get normal ETH transactions for an address"""
        params = {
            'module': 'account',
            'action': 'txlist',
            'address': address,
            'startblock': start_block,
            'endblock': 99999999,
            'page': 1,
            'offset': 10000,  # Max allowed
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
    
    def get_internal_transactions(self, address: str, start_block: int = 0) -> List[dict]:
        """Get internal transactions for an address"""
        params = {
            'module': 'account',
            'action': 'txlistinternal',
            'address': address,
            'startblock': start_block,
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
    
    def extract_creator_temporal_features(self, creator_address: str, creation_time: int) -> dict:
        """
        Extract temporal features for contract creator
        Features include: transfer patterns, approve patterns, transaction frequency, etc.
        """
        print(f"  Extracting creator features for {creator_address}...")
        
        # Get creator's transactions
        normal_txs = self.get_normal_transactions(creator_address)
        internal_txs = self.get_internal_transactions(creator_address)
        
        all_txs = normal_txs + internal_txs
        
        # Filter transactions after contract creation
        post_creation_txs = [tx for tx in all_txs if int(tx.get('timeStamp', 0)) >= creation_time]
        
        features = {
            'creator_address': creator_address,
            'total_transactions': len(all_txs),
            'post_creation_transactions': len(post_creation_txs),
            'transaction_activity': self._analyze_transaction_activity(all_txs, creation_time),
            'transfer_patterns': self._analyze_transfer_patterns(all_txs),
            'temporal_patterns': self._analyze_temporal_patterns(all_txs),
        }
        
        return features
    
    def extract_contract_temporal_features(self, contract_address: str, creation_time: int) -> dict:
        """
        Extract temporal features for smart contract
        Features include: mint/burn/withdraw patterns, transaction frequency, etc.
        """
        print(f"  Extracting contract features for {contract_address}...")
        
        # Get contract's transactions
        normal_txs = self.get_normal_transactions(contract_address)
        internal_txs = self.get_internal_transactions(contract_address)
        erc721_transfers = self.get_erc721_transfers(contract_address)
        
        features = {
            'contract_address': contract_address,
            'creation_timestamp': creation_time,
            'creation_date': datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S') if creation_time else 'Unknown',
            'total_normal_transactions': len(normal_txs),
            'total_internal_transactions': len(internal_txs),
            'total_nft_transfers': len(erc721_transfers),
            'transaction_activity': self._analyze_contract_transactions(normal_txs, internal_txs),
            'nft_activity': self._analyze_nft_activity(erc721_transfers),
            'temporal_patterns': self._analyze_contract_temporal_patterns(normal_txs, internal_txs, erc721_transfers, creation_time),
        }
        
        return features
    
    def _analyze_transaction_activity(self, transactions: List[dict], creation_time: int) -> dict:
        """Analyze creator's transaction activity patterns"""
        if not transactions:
            return {
                'sent_count': 0,
                'received_count': 0,
                'total_value_sent': 0,
                'total_value_received': 0,
                'avg_transaction_value': 0,
            }
        
        sent = [tx for tx in transactions if tx.get('from', '').lower() != '']
        received = [tx for tx in transactions if tx.get('to', '').lower() != '']
        
        total_sent = sum(int(tx.get('value', 0)) for tx in sent)
        total_received = sum(int(tx.get('value', 0)) for tx in received)
        
        return {
            'sent_count': len(sent),
            'received_count': len(received),
            'total_value_sent_wei': total_sent,
            'total_value_received_wei': total_received,
            'avg_transaction_value_wei': (total_sent + total_received) // len(transactions) if transactions else 0,
        }
    
    def _analyze_transfer_patterns(self, transactions: List[dict]) -> dict:
        """Analyze transfer patterns (approve, transferFrom, etc.)"""
        method_counts = defaultdict(int)
        
        for tx in transactions:
            method_id = tx.get('input', '')[:10]  # First 10 chars = 0x + 8 hex chars
            method_counts[method_id] += 1
        
        # Common method signatures
        method_names = {
            '0xa9059cbb': 'transfer',
            '0x23b872dd': 'transferFrom',
            '0x095ea7b3': 'approve',
            '0x40c10f19': 'mint',
            '0x42842e0e': 'safeTransferFrom',
            '0xa22cb465': 'setApprovalForAll',
        }
        
        patterns = {}
        for method_id, count in method_counts.items():
            method_name = method_names.get(method_id, method_id)
            patterns[method_name] = count
        
        return patterns
    
    def _analyze_temporal_patterns(self, transactions: List[dict]) -> dict:
        """Analyze temporal patterns of transactions"""
        if not transactions:
            return {
                'first_transaction': 0,
                'last_transaction': 0,
                'time_span_days': 0,
                'avg_daily_transactions': 0,
                'hourly_distribution': {},
                'daily_distribution': {},
            }
        
        timestamps = [int(tx.get('timeStamp', 0)) for tx in transactions if tx.get('timeStamp')]
        
        if not timestamps:
            return {'error': 'No timestamps available'}
        
        first_tx = min(timestamps)
        last_tx = max(timestamps)
        time_span = (last_tx - first_tx) / 86400  # Convert to days
        
        # Hourly distribution
        hourly = defaultdict(int)
        daily = defaultdict(int)
        
        for ts in timestamps:
            dt = datetime.fromtimestamp(ts)
            hourly[dt.hour] += 1
            daily[dt.strftime('%Y-%m-%d')] += 1
        
        return {
            'first_transaction': first_tx,
            'first_transaction_date': datetime.fromtimestamp(first_tx).strftime('%Y-%m-%d %H:%M:%S'),
            'last_transaction': last_tx,
            'last_transaction_date': datetime.fromtimestamp(last_tx).strftime('%Y-%m-%d %H:%M:%S'),
            'time_span_days': round(time_span, 2),
            'avg_daily_transactions': round(len(transactions) / time_span, 2) if time_span > 0 else 0,
            'hourly_distribution': dict(hourly),
            'total_unique_days': len(daily),
        }
    
    def _analyze_contract_transactions(self, normal_txs: List[dict], internal_txs: List[dict]) -> dict:
        """Analyze contract transaction patterns"""
        # Categorize by common contract methods
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
        
        # Count ETH movements
        eth_in = sum(int(tx.get('value', 0)) for tx in normal_txs if tx.get('to', '').lower() == tx.get('contractAddress', '').lower())
        eth_out = sum(int(tx.get('value', 0)) for tx in internal_txs if tx.get('from', '').lower() == tx.get('contractAddress', '').lower())
        
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
            }
        
        unique_tokens = set()
        unique_senders = set()
        unique_receivers = set()
        
        mint_count = 0  # From zero address
        burn_count = 0  # To zero address
        
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
    
    def _analyze_contract_temporal_patterns(self, normal_txs: List[dict], 
                                           internal_txs: List[dict], 
                                           nft_transfers: List[dict],
                                           creation_time: int) -> dict:
        """Analyze temporal patterns for contract activity"""
        all_timestamps = []
        
        # Collect all timestamps
        for tx in normal_txs + internal_txs + nft_transfers:
            ts = int(tx.get('timeStamp', 0))
            if ts > 0:
                all_timestamps.append(ts)
        
        if not all_timestamps:
            return {
                'days_since_creation': 0,
                'total_activity_days': 0,
                'avg_daily_transactions': 0,
            }
        
        all_timestamps.sort()
        
        # Calculate age
        current_time = int(time.time())
        age_days = (current_time - creation_time) / 86400 if creation_time > 0 else 0
        
        # Calculate activity periods
        unique_days = set()
        hourly_dist = defaultdict(int)
        
        for ts in all_timestamps:
            dt = datetime.fromtimestamp(ts)
            unique_days.add(dt.strftime('%Y-%m-%d'))
            hourly_dist[dt.hour] += 1
        
        # Calculate activity bursts (days with unusual activity)
        daily_counts = defaultdict(int)
        for ts in all_timestamps:
            dt = datetime.fromtimestamp(ts)
            daily_counts[dt.strftime('%Y-%m-%d')] += 1
        
        avg_daily = sum(daily_counts.values()) / len(daily_counts) if daily_counts else 0
        burst_days = [day for day, count in daily_counts.items() if count > avg_daily * 2]
        
        return {
            'contract_age_days': round(age_days, 2),
            'days_since_creation': round(age_days, 2),
            'total_activity_days': len(unique_days),
            'avg_daily_transactions': round(len(all_timestamps) / age_days, 2) if age_days > 0 else 0,
            'hourly_distribution': dict(hourly_dist),
            'burst_activity_days': len(burst_days),
            'activity_ratio': round(len(unique_days) / age_days, 4) if age_days > 0 else 0,
        }


def main():
    """Main execution function"""
    
    print("=" * 80)
    print("TEMPORAL FEATURE EXTRACTION FOR NFT CONTRACTS")
    print("=" * 80)
    print()
    
    # Load contract addresses
    with open('contracts.txt', 'r') as f:
        contract_addresses = [line.strip() for line in f if line.strip()]
    
    print(f"Loaded {len(contract_addresses)} contract addresses\n")
    
    # Initialize extractor
    extractor = TemporalFeatureExtractor(ETHERSCAN_API_KEY)
    
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
            # Get creator and creation time
            creator_address, creation_time = extractor.get_contract_creator(contract_address)
            
            if not creator_address:
                print(f"  ✗ Could not get creator information")
                temporal_features['contracts'][contract_address] = {
                    'error': 'Creator information not available'
                }
                continue
            
            print(f"  ✓ Creator: {creator_address}")
            print(f"  ✓ Created: {datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S') if creation_time else 'Unknown'}")
            
            # Extract creator features
            creator_features = extractor.extract_creator_temporal_features(creator_address, creation_time)
            
            # Extract contract features
            contract_features = extractor.extract_contract_temporal_features(contract_address, creation_time)
            
            # Combine features
            temporal_features['contracts'][contract_address] = {
                'creator': creator_features,
                'contract': contract_features,
            }
            
            print(f"  ✓ Features extracted successfully")
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
    
    # Print summary statistics
    successful = sum(1 for v in temporal_features['contracts'].values() if 'error' not in v)
    failed = len(temporal_features['contracts']) - successful
    
    print(f"✓ Successful: {successful}")
    print(f"✗ Failed: {failed}")
    print()


if __name__ == '__main__':
    main()
