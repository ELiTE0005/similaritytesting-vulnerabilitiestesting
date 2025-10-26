import json

with open('similarity_report.json', 'r') as f:
    similarity = json.load(f)

total = len(similarity)
high_full = [(k, v['full_similarity']) for k, v in similarity.items() if v['full_similarity'] > 0.8]
high_partial = [(k, v['partial_similarity']) for k, v in similarity.items() if v['partial_similarity'] > 0.8]

print(f"✓ Similarity Analysis Results:")
print(f"  Total comparisons: {total}")
print(f"  High full similarity (>80%): {len(high_full)}")
print(f"  High partial similarity (>80%): {len(high_partial)}")

if high_full:
    print(f"\nTop 5 by full similarity:")
    high_full.sort(key=lambda x: x[1], reverse=True)
    for pair, sim in high_full[:5]:
        c1, c2 = pair.split('_')
        print(f"  {c1[:10]}... vs {c2[:10]}...: {sim*100:.1f}%")

if high_partial:
    print(f"\nTop 5 by partial similarity:")
    high_partial.sort(key=lambda x: x[1], reverse=True)
    for pair, sim in high_partial[:5]:
        c1, c2 = pair.split('_')
        print(f"  {c1[:10]}... vs {c2[:10]}...: {sim*100:.1f}%")
