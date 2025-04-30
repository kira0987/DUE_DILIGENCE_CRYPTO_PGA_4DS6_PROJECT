import json
from collections import Counter

# Read the unique_questions.json file
with open('unique_questions.json', 'r') as file:
    data = json.load(file)

# Count occurrences of each tag
tag_counts = Counter(item['tag'] for item in data)

# Print results
print("Tag Count Analysis:")
print(f"Total number of unique tags: {len(tag_counts)}\n")
print("Breakdown of questions per tag:")
for tag, count in sorted(tag_counts.items()):
    print(f"{tag}: {count} questions")

# Summary
total_questions = len(data)
print(f"\nSummary:")
print(f"Total questions: {total_questions}")
print(f"Total unique tags: {len(tag_counts)}")