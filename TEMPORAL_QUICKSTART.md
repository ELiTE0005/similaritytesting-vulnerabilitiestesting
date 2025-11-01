# Temporal Feature Extraction - Quick Reference

## 🚀 Quick Start (3 Steps)

### 1. Set API Key
```powershell
$env:ETHERSCAN_API_KEY = "YourKeyHere"
```

### 2. Extract Features
```powershell
python extract_temporal_features.py
```
⏱️ Time: ~5-10 minutes for 85 contracts

### 3. Generate Reports
```powershell
python analyze_temporal_features.py
```
⏱️ Time: < 1 minute

---

## 📊 Output Files

| File | What's Inside |
|------|---------------|
| `temporal_features.json` | Complete raw data |
| `temporal_features_summary.json` | Statistics |
| `TEMPORAL_FEATURES_REPORT.md` | Human-readable report |

---

## 🔍 Key Features Extracted

### Creator (20+ metrics)
- Transaction counts
- ETH sent/received
- Transfer/approve patterns
- Activity timing
- Frequency metrics

### Contract (30+ metrics)
- Mint/burn/withdraw counts
- NFT transfer stats
- Contract age
- Activity patterns
- Burst detection
- Unique participants

---

## 📈 What You Can Analyze

✅ Creator behavior before/after deployment  
✅ Contract lifecycle and activity  
✅ Minting patterns and velocity  
✅ Withdrawal patterns (rug pull detection)  
✅ Temporal correlation with vulnerabilities  
✅ Abandoned contract identification  
✅ Activity bursts (pump & dump detection)  

---

## 🛠️ Troubleshooting

**API Key Error?**
→ Set: `$env:ETHERSCAN_API_KEY = "YourKey"`

**Rate Limit?**
→ Increase `RATE_LIMIT_DELAY` in script

**Timeout?**
→ Retry or skip problematic contracts

---

## 📚 Full Documentation

See `TEMPORAL_FEATURES_USAGE.md` for:
- Complete feature list
- Data structure details
- Advanced usage
- Integration examples

---

**Get Etherscan API Key:** https://etherscan.io/apis (FREE)
