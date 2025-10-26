import json

with open('vulnerability_report.json', 'r') as f:
    data = json.load(f)

total = len(data)
success = sum(1 for v in data.values() if "Traceback" not in v)
compilation_errors = sum(1 for v in data.values() if "Compilation warnings/errors" in v)
version_mismatches = sum(1 for v in data.values() if "requires different compiler version" in v)
unknown_file_errors = sum(1 for v in data.values() if "Unknown file:" in v)
import_errors = sum(1 for v in data.values() if "not found: File not found" in v)

print(f"Total contracts: {total}")
print(f"Successful analyses (no Traceback): {success}/{total}")
print(f"Compilation errors: {compilation_errors}")
print(f"Version mismatches: {version_mismatches}")
print(f"Unknown file errors: {unknown_file_errors}")
print(f"Import errors: {import_errors}")
