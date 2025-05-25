
from pymongo import MongoClient
from datetime import datetime
import json  # ✅ REQUIRED for loading the question bank file

# Connect to local MongoDB (Compass)
client = MongoClient("mongodb://localhost:27017/")
db = client["crypto_dd"]
funds_collection = db["funds"]

def insert_fund_metadata(fund_name, file_name):
    # Check if fund already exists
    existing = funds_collection.find_one({"fund_name": fund_name})
    if existing:
        print(f"⚠️ Fund '{fund_name}' already exists. Skipping insert.")
        return existing["_id"]

    # Insert new if not found
    doc = {
        "fund_name": fund_name,
        "uploaded_at": datetime.utcnow(),
        "file_name": file_name,
        "raw_text": None,
        "cleaned_chunks": [],
        "qa_results": [],
        "risk_score": {},
        "pptx_path": None
    }
    result = funds_collection.insert_one(doc)
    return result.inserted_id


def update_fund_field(fund_name, field_name, value):
    result = funds_collection.update_one(
        {"fund_name": fund_name},
        {"$set": {field_name: value}}
    )
    return result.modified_count

def append_qa_result(fund_name, question, answer):
    result = funds_collection.update_one(
        {"fund_name": fund_name},
        {"$push": {"qa_results": {"question": question, "answer": answer}}}
    )
    return result.modified_count

def get_fund_by_name(fund_name):
    return funds_collection.find_one({"fund_name": fund_name})

def save_question_bank(filepath="data/question_bank.json"):
    with open(filepath, "r", encoding="utf-8") as f:
        questions = json.load(f)
    db.question_bank.delete_many({})
    db.question_bank.insert_many(questions)
    print(f"✅ Saved {len(questions)} questions to MongoDB.")

def load_question_bank():
    return list(db.question_bank.find({}, {"_id": 0}))
def get_all_funds_with_raw_text():
    return list(funds_collection.find(
        {"raw_text": {"$exists": True, "$ne": None}},
        {"fund_name": 1, "raw_text": 1}
    ))
def get_all_funds_with_chunks():
    return list(funds_collection.find({"cleaned_chunks": {"$exists": True, "$ne": []}}))

def get_chunks_and_embeddings(fund_name):
    doc = funds_collection.find_one(
        {"fund_name": fund_name},
        {"_id": 0, "cleaned_chunks": 1, "embeddings": 1}
    )
    return doc.get("cleaned_chunks", []), doc.get("embeddings", [])
def get_all_funds_with_embeddings():
    return list(funds_collection.find({
        "cleaned_chunks": {"$exists": True, "$ne": []},
        "embeddings": {"$exists": True, "$ne": []}
    }))
def store_risk_scores(fund_name, risk_scores: dict):
    result = funds_collection.update_one(
        {"fund_name": fund_name},
        {"$set": {"risk_score": risk_scores}}
    )
    return result.modified_count
