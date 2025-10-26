import difflib
import re
import hashlib


class CodeSimilarity:
    @staticmethod
    def full_similarity(code1, code2):
        """Fast similarity using hash comparison and sampling for large files."""
        # If identical, return 1.0 immediately
        if code1 == code2:
            return 1.0
        
        # For very large files, use hash-based comparison + sampling
        if len(code1) > 50000 or len(code2) > 50000:
            # Check if hashes match (perfect similarity)
            if hashlib.md5(code1.encode()).hexdigest() == hashlib.md5(code2.encode()).hexdigest():
                return 1.0
            # Sample-based similarity for large files (first 10K chars)
            sample1 = code1[:10000]
            sample2 = code2[:10000]
            return difflib.SequenceMatcher(None, sample1, sample2).ratio() * 0.95  # Cap at 0.95 for samples
        
        # Standard comparison for smaller files
        return difflib.SequenceMatcher(None, code1, code2).ratio()

    @staticmethod
    def _solidity_function_names(code: str):
        """Extract Solidity function names via regex. Handles standard function definitions."""
        try:
            pattern = r"\bfunction\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("
            return set(m.group(1) for m in re.finditer(pattern, code))
        except Exception:
            return set()

    @staticmethod
    def partial_similarity(code1, code2):
        """Jaccard similarity of function name sets as a proxy for partial similarity."""
        funcs1 = CodeSimilarity._solidity_function_names(code1)
        funcs2 = CodeSimilarity._solidity_function_names(code2)
        union = funcs1 | funcs2
        if not union:
            return 0.0
        return len(funcs1 & funcs2) / len(union)
