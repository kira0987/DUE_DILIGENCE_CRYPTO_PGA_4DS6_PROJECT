import json
from collections import defaultdict

def process_questions(input_path, output_path):
    # Load the JSON data
    with open(input_path, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
    
    output = []
    question_map = defaultdict(list)
    index = 1
    total_raw = 0
    total_processed = 0

    # First pass: Process all subtag questions
    for tag in data['tags']:
        tag_name = tag['tag']
        
        # Process subtags first to establish hierarchy
        for subtag in tag.get('subtags', []):
            subtag_name = subtag.get('subtag', 'Uncategorized')
            
            for question in subtag.get('questions', []):
                total_raw += 1
                clean_q = question.strip()
                if clean_q:
                    question_map[clean_q].append({
                        "original": question.strip(),
                        "tag": tag_name,
                        "subtag": subtag_name,
                        "source": "subtag"
                    })

    # Second pass: Process direct questions
    for tag in data['tags']:
        tag_name = tag['tag']
        has_subtags = bool(tag.get('subtags'))
        
        for question in tag.get('questions', []):
            total_raw += 1
            clean_q = question.strip()
            if clean_q:
                # Check if clean_q is already in question_map to handle deduplication
                if clean_q not in question_map:
                    subtag_type = "General" if has_subtags else "Standalone"
                    question_map[clean_q].append({
                        "original": question.strip(),
                        "tag": tag_name,
                        "subtag": subtag_type,
                        "source": "direct"
                    })

    # Generate final output with proper indexing
    for clean_q, entries in question_map.items():
        for entry in entries:
            output.append({
                "index": index,
                "question": entry["original"],
                "tag": entry["tag"],
                "subtag": entry["subtag"],
                "source": entry["source"]
            })
            total_processed += 1
            index += 1

    # Verification and stats
    print(f"Total raw questions: {total_raw}")
    print(f"Total processed questions: {total_processed}")
    print(f"Duplicates removed: {total_raw - total_processed}")
    
    # Save the output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

# Execute the processing
process_questions('output.json', 'final_questions.json')
