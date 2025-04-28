import tkinter as tk
from tkinter import filedialog
import json
from pymongo import MongoClient

# --- Setup MongoDB ---
client = MongoClient('mongodb://localhost:27017/')
db = client['due_dilligence_crypto_fund_rag_database']
questions_collection = db['questions']

# --- Function to Load JSON from Dialog Box ---
def load_json_file():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if not file_path:
        raise ValueError("No file selected.")
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

# --- Store JSON in MongoDB ---
def store_json_in_db(data):
    questions_collection.drop()  # Clear existing data
    questions_collection.insert_many(data)
    print(f"Stored {len(data)} questions in MongoDB.")
    print("Database 'crypto_rag_database' and collection 'questions' are ready for RAG use.")

# --- Main Workflow ---
def main():
    try:
        # Load JSON from dialog box
        print("Please select the JSON file containing embedded questions.")
        json_data = load_json_file()
        
        # Store in MongoDB
        store_json_in_db(json_data)
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()