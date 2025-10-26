import json

with open('vulnerability_report.json', 'r') as f:
    data = json.load(f)

total = len(data)
no_traceback = sum(1 for v in data.values() if "Traceback" not in v)
compilation_succeeded = sum(1 for v in data.values() if "Compilation" in v and "Traceback" not in v)
detectors_found = sum(1 for v in data.values() if "[" in v and "detector" in v.lower())
multifile_unknown = sum(1 for v in data.values() if '@openzeppelin' in v and 'Unknown file' in v)
single_unknown = sum(1 for v in data.values() if 'tmp' in v and 'Unknown file' in v)

print(f"Total contracts: {total}")
print(f"No Traceback: {no_traceback}")
print(f"Compilation succeeded: {compilation_succeeded}")
print(f"Detectors found issues: {detectors_found}")
print(f"Multi-file unknown errors: {multifile_unknown}")
print(f"Single-file unknown errors: {single_unknown}")

# Get sample of each error type
if multifile_unknown > 0:
    multifile_sample = [v for v in data.values() if '@openzeppelin' in v and 'Unknown file' in v][0]
    lines = multifile_sample.split('\n')
    err_idx = [i for i, l in enumerate(lines) if 'Unknown file' in l][0]
    print(f"\nSample multi-file error:")
    print('\n'.join(lines[max(0,err_idx-2):err_idx+2]))

if single_unknown > 0:
    single_sample = [v for v in data.values() if 'tmp' in v and 'Unknown file' in v][0]
    lines = single_sample.split('\n')
    err_idx = [i for i, l in enumerate(lines) if 'Unknown file' in l][0]
    print(f"\nSample single-file error:")
    print('\n'.join(lines[max(0,err_idx-2):err_idx+2]))
