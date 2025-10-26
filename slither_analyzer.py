import subprocess
import tempfile
import os
import sys
import json
import re
import shutil

class SlitherAnalyzer:
    @staticmethod
    def _extract_all_contracts(code):
        """
        Extract ALL contracts from Etherscan's response.
        Returns: (main_file_path, is_multi_file, temp_dir)
        - For single files: returns the .sol file path
        - For multi-file: returns the main contract file path and temp directory with all files
        """
        stripped = code.strip()
        
        # Check if it's JSON wrapped (starts with { or {{)
        if not stripped.startswith('{'):
            # Plain Solidity code - single file
            return code, False, None
        
        try:
            # Parse JSON
            if stripped.startswith('{{'):
                stripped = stripped[1:-1]
            
            data = json.loads(stripped)
            
            # Check if it has "sources" (multi-file format)
            if "sources" not in data:
                # Try to find single file content
                for key, value in data.items():
                    if isinstance(value, dict) and "content" in value:
                        return value["content"], False, None
                return code, False, None
            
            sources = data["sources"]
            if not sources:
                return code, False, None
            
            # Multi-file contract - create temp directory structure
            temp_dir = tempfile.mkdtemp(prefix="slither_contracts_")
            
            # Find the main contract file
            # Priority: 
            # 1. Files in contracts/ directory
            # 2. Files NOT in @openzeppelin or node_modules
            # 3. Largest file with "contract" keyword
            main_file = None
            max_size = 0
            contract_candidates = []
            
            for filename, file_data in sources.items():
                content = file_data.get("content", "")
                
                # Keep original path separators (forward slashes) for solc compatibility
                # Just remove leading slash
                clean_filename = filename.lstrip('/')
                
                # Create file in temp directory (Python on Windows accepts forward slashes)
                file_path = os.path.join(temp_dir, clean_filename)
                # Normalize the directory path for os.makedirs
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Track contract candidates
                if "contract " in content or "interface " in content:
                    # Prioritize non-library files
                    is_library = any(lib in filename.lower() for lib in ['@openzeppelin', 'node_modules', '@chainlink'])
                    is_in_contracts = 'contracts/' in filename or 'contracts\\' in filename
                    # Priority: non-library gets huge bonus (100000), then contracts/, then size
                    priority = (not is_library) * 100000 + is_in_contracts * 10000 + len(content)
                    contract_candidates.append((priority, file_path, len(content)))
            
            # Select highest priority contract
            if contract_candidates:
                contract_candidates.sort(reverse=True, key=lambda x: x[0])
                main_file = contract_candidates[0][1]
            
            if not main_file:
                # No contract found, use first file
                first_filename = next(iter(sources.keys())).lstrip('/')
                main_file = os.path.join(temp_dir, first_filename)
            
            return main_file, True, temp_dir
            
        except json.JSONDecodeError:
            # Not valid JSON, return as plain code
            return code, False, None
    
    @staticmethod
    def _extract_solc_version(code):
        """Extract required Solidity version from pragma statement."""
        # Match: pragma solidity ^0.8.0; or pragma solidity >=0.6.0 <0.8.0;
        match = re.search(r'pragma\s+solidity\s+([^;]+);', code)
        if match:
            version_spec = match.group(1).strip()
            # Extract base version (e.g., "^0.8.0" -> "0.8", ">=0.7.0" -> "0.7")
            version_match = re.search(r'(\d+\.\d+)', version_spec)
            if version_match:
                return version_match.group(1)
        return None

    @staticmethod
    def analyze(code):
        # Preprocess: Extract contracts from JSON if needed
        processed_input, is_multi_file, temp_dir = SlitherAnalyzer._extract_all_contracts(code)
        
        # Detect required Solidity version
        if is_multi_file:
            # Read main file to get version
            with open(processed_input, 'r', encoding='utf-8') as f:
                main_content = f.read()
            required_version = SlitherAnalyzer._extract_solc_version(main_content)
        else:
            required_version = SlitherAnalyzer._extract_solc_version(processed_input)
        
        version_warning = ""
        if required_version:
            version_warning = f"[INFO] Contract requires Solidity {required_version}\n"
        
        # For single file, create temp file
        temp_file_path = None
        if not is_multi_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".sol", mode="w", encoding="utf-8") as f:
                f.write(processed_input)
                f.flush()
                temp_file_path = f.name
            target_path = temp_file_path
        else:
            # For multi-file, use the main contract path
            target_path = processed_input
        
        try:
            # Convert paths to forward slashes for solc (Windows compatibility)
            target_path_normalized = target_path.replace('\\', '/')
            
            # Build Slither command
            cmd = ["slither", target_path_normalized]
            
            # Add solc args for both multi-file and single-file (Windows path fix)
            if is_multi_file and temp_dir:
                temp_dir_normalized = temp_dir.replace('\\', '/')
                cmd.append("--solc-args")
                cmd.append(f"--base-path {temp_dir_normalized} --allow-paths {temp_dir_normalized}")
            else:
                # For single-file, explicitly set allow-paths to fix Windows path issue
                temp_file_dir = os.path.dirname(target_path).replace('\\', '/')
                cmd.append("--solc-args")
                cmd.append(f"--allow-paths {temp_file_dir}")
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            except FileNotFoundError:
                # Fallback: attempt to use slither from the same venv as Python
                python_exe = sys.executable
                scripts_dir = os.path.join(os.path.dirname(python_exe))
                slither_exe = os.path.join(scripts_dir, "slither.exe" if os.name == "nt" else "slither")
                
                if is_multi_file and temp_dir:
                    temp_dir_normalized = temp_dir.replace('\\', '/')
                    cmd = [slither_exe, target_path_normalized, "--solc-args", f"--base-path {temp_dir_normalized} --allow-paths {temp_dir_normalized}"]
                else:
                    temp_file_dir = os.path.dirname(target_path).replace('\\', '/')
                    cmd = [slither_exe, target_path_normalized, "--solc-args", f"--allow-paths {temp_file_dir}"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            # Return both stdout and stderr if available for better diagnostics
            output = version_warning
            output += result.stdout or ""
            if result.stderr:
                output += ("\n" if output else "") + "[stderr]\n" + result.stderr
            return output
            
        except FileNotFoundError:
            return "Slither not found. Please install slither-analyzer and ensure 'slither' is in PATH."
        except subprocess.TimeoutExpired:
            return "Slither analysis timed out."
        finally:
            # Cleanup
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
