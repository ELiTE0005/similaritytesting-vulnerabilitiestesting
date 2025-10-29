"""
Mythril-based vulnerability analyzer for smart contracts.
Analyzes contracts using symbolic execution for deep vulnerability detection.
Works with both source code and deployed bytecode.
"""

import json
from typing import Dict, Any, List
from mythril.mythril import Mythril
from mythril.analysis.issue_annotation import IssueAnnotation


class MythrilAnalyzer:
    """Wrapper for Mythril symbolic execution engine."""
    
    @staticmethod
    def analyze_address(address: str, timeout: int = 300) -> Dict[str, Any]:
        """
        Analyze a deployed contract by address using bytecode analysis.
        
        Args:
            address: Ethereum contract address (0x...)
            timeout: Analysis timeout in seconds (default: 5 minutes)
            
        Returns:
            Dictionary with analysis results:
            {
                "success": bool,
                "address": str,
                "issues": List[dict],
                "issue_count": int,
                "severity_breakdown": dict,
                "error": str (if failed)
            }
        """
        try:
            print(f"  [Mythril] Analyzing bytecode for {address[:10]}...")
            
            # Initialize Mythril
            myth = Mythril(solv=None, solc_args=None)
            
            # Load contract from blockchain
            myth.load_from_address(address)
            
            # Run symbolic execution
            report = myth.fire_lasers(
                modules=None,  # Use all detection modules
                transaction_count=2,  # Number of transactions to simulate
                max_depth=50,  # Maximum recursion depth
                execution_timeout=timeout
            )
            
            # Parse issues
            issues = []
            severity_counts = {"High": 0, "Medium": 0, "Low": 0}
            
            for issue in report.issues:
                severity = issue.severity
                if severity in severity_counts:
                    severity_counts[severity] += 1
                
                issues.append({
                    "title": issue.title,
                    "description": issue.description,
                    "severity": severity,
                    "contract": issue.contract,
                    "function": issue.function,
                    "swc_id": issue.swc_id,
                    "bytecode_offsets": issue.bytecode_offsets,
                })
            
            return {
                "success": True,
                "address": address,
                "issues": issues,
                "issue_count": len(issues),
                "severity_breakdown": severity_counts,
                "analysis_type": "bytecode"
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"  [Mythril] Error: {error_msg[:100]}...")
            
            return {
                "success": False,
                "address": address,
                "error": error_msg,
                "issues": [],
                "issue_count": 0
            }
    
    @staticmethod
    def analyze_source(code: str, contract_name: str = "Contract", timeout: int = 300) -> Dict[str, Any]:
        """
        Analyze contract from source code.
        
        Args:
            code: Solidity source code
            contract_name: Name for the contract
            timeout: Analysis timeout in seconds
            
        Returns:
            Dictionary with analysis results
        """
        try:
            print(f"  [Mythril] Analyzing source code for {contract_name}...")
            
            # Initialize Mythril
            myth = Mythril(solv=None, solc_args=None)
            
            # Load from source code
            myth.load_from_solidity([code])
            
            # Run symbolic execution
            report = myth.fire_lasers(
                modules=None,
                transaction_count=2,
                max_depth=50,
                execution_timeout=timeout
            )
            
            # Parse issues
            issues = []
            severity_counts = {"High": 0, "Medium": 0, "Low": 0}
            
            for issue in report.issues:
                severity = issue.severity
                if severity in severity_counts:
                    severity_counts[severity] += 1
                
                issues.append({
                    "title": issue.title,
                    "description": issue.description,
                    "severity": severity,
                    "contract": issue.contract,
                    "function": issue.function,
                    "swc_id": issue.swc_id,
                    "line_numbers": getattr(issue, 'line_numbers', []),
                })
            
            return {
                "success": True,
                "contract_name": contract_name,
                "issues": issues,
                "issue_count": len(issues),
                "severity_breakdown": severity_counts,
                "analysis_type": "source"
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"  [Mythril] Error: {error_msg[:100]}...")
            
            return {
                "success": False,
                "contract_name": contract_name,
                "error": error_msg,
                "issues": [],
                "issue_count": 0
            }
    
    @staticmethod
    def format_report(result: Dict[str, Any]) -> str:
        """
        Format analysis result as human-readable text.
        
        Args:
            result: Analysis result dictionary
            
        Returns:
            Formatted string report
        """
        if not result.get("success"):
            return f"Analysis failed: {result.get('error', 'Unknown error')}"
        
        lines = []
        lines.append("=" * 70)
        lines.append("MYTHRIL SECURITY ANALYSIS")
        lines.append("=" * 70)
        
        if "address" in result:
            lines.append(f"Contract: {result['address']}")
        else:
            lines.append(f"Contract: {result.get('contract_name', 'Unknown')}")
        
        lines.append(f"Analysis Type: {result.get('analysis_type', 'unknown')}")
        lines.append(f"Total Issues: {result['issue_count']}")
        
        severity = result.get('severity_breakdown', {})
        lines.append(f"\nSeverity Breakdown:")
        lines.append(f"  🔴 High:   {severity.get('High', 0)}")
        lines.append(f"  🟡 Medium: {severity.get('Medium', 0)}")
        lines.append(f"  🟢 Low:    {severity.get('Low', 0)}")
        
        if result['issues']:
            lines.append("\n" + "=" * 70)
            lines.append("DETAILED FINDINGS")
            lines.append("=" * 70)
            
            for i, issue in enumerate(result['issues'], 1):
                lines.append(f"\n[{i}] {issue['title']} (SWC-{issue.get('swc_id', 'N/A')})")
                lines.append(f"    Severity: {issue['severity']}")
                lines.append(f"    Function: {issue.get('function', 'N/A')}")
                lines.append(f"    Description: {issue['description'][:200]}...")
        else:
            lines.append("\n✅ No vulnerabilities detected!")
        
        lines.append("\n" + "=" * 70)
        
        return "\n".join(lines)


# Quick test function
def test_mythril():
    """Test Mythril on a known contract."""
    # BAYC contract address
    test_address = "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D"
    
    print(f"Testing Mythril on BAYC contract...")
    result = MythrilAnalyzer.analyze_address(test_address, timeout=60)
    
    print("\n" + MythrilAnalyzer.format_report(result))
    
    return result


if __name__ == "__main__":
    test_mythril()
