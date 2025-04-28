import json
import numpy as np
from sentence_transformers import SentenceTransformer
import re

# Load the Sentence-BERT model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Read the input JSON file
with open('output.json', 'r', encoding="utf-8") as file:
    data = json.load(file)

# List to store questions with metadata and embeddings
embedded_data = []

# Function to clean text by removing unwanted characters and whitespace
def clean_text(text):
    # Remove unwanted characters (like zero-width spaces, etc.)
    return re.sub(r'[^\x00-\x7F]+', '', text).strip()  # This removes non-ASCII characters

# Function to process questions and generate embeddings
def process_questions(questions, tag, subtag=None):
    for question in questions:
        # Clean the question (remove extra whitespace, special characters, and unwanted characters like \u200b)
        cleaned_question = clean_text(question)
        
        # Generate embedding for the question
        embedding = model.encode(cleaned_question, convert_to_numpy=True)
        
        # Store metadata and embedding
        embedded_data.append({
            "tag": tag,
            "subtag": subtag if subtag else None,  # Only include subtag if it's not None
            "question": cleaned_question,
            "embedding": embedding.tolist()  # Convert numpy array to list for JSON compatibility
        })

# Iterate through each tag in the document
for tag_entry in data['tags']:
    tag_name = tag_entry['tag']
    
    # Process top-level questions under the tag (if any)
    if 'questions' in tag_entry and tag_entry['questions']:
        process_questions(tag_entry['questions'], tag_name)
    
    # Process questions under subtags (if any)
    if 'subtags' in tag_entry and tag_entry['subtags']:
        for subtag_entry in tag_entry['subtags']:
            subtag_name = subtag_entry['subtag']
            
            # Only process if the subtag has questions
            if 'questions' in subtag_entry and subtag_entry['questions']:
                process_questions(subtag_entry['questions'], tag_name, subtag_name)

# Save the embedded data to a JSON file for reference (optional)
with open('embedded_questions.json', 'w') as file:
    json.dump(embedded_data, file, indent=4)

# Create a binary index file (index.bin)
embedding_dim = len(embedded_data[0]['embedding'])  # 384 for all-MiniLM-L6-v2
num_entries = len(embedded_data)

with open('index.bin', 'wb') as f:
    # Write number of entries and embedding dimension
    f.write(np.int32(num_entries).tobytes())
    f.write(np.int32(embedding_dim).tobytes())
    
    # Write each entry
    for entry in embedded_data:
        # Prepare metadata as JSON string
        metadata = json.dumps({
            "tag": entry["tag"],
            "subtag": entry["subtag"] if entry["subtag"] is not None else "",  # Don't store 'None', store empty string
            "question": entry["question"]
        }).encode('utf-8')
        
        # Write metadata length and metadata
        f.write(np.int32(len(metadata)).tobytes())
        f.write(metadata)
        
        # Write embedding as float32 array
        embedding = np.array(entry["embedding"], dtype=np.float32)
        f.write(embedding.tobytes())

print(f"Processed {num_entries} questions.")
print(f"Embeddings saved to 'index.bin' with dimension {embedding_dim}.")
print("Metadata and embeddings also saved to 'embedded_questions.json' for reference.")
