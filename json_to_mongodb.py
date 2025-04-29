import json
import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

# Connect to MongoDB
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["merinid_db"]
collection = db["products"]

# Load items.json
with open("items.json", "r", encoding="utf-8") as f:
    products = json.load(f)

# Insert data
if products:
    collection.delete_many({})  # Optional: clear old data first
    collection.insert_many(products)
    print(f"✅ Imported {len(products)} products into MongoDB.")
else:
    print("❌ No products found in items.json")
