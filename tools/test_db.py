import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("MONGO_URI")
print(f"📡 Testing connection to: {uri.split('@')[-1]}") # Hide password in print

try:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    # The 'ping' command is cheap and does not require auth, 
    # but accessing a collection DOES require auth.
    client.admin.command('ping')
    print("✅ Network connection to Atlas is OK.")
    
    # Try to access the database (This is where Bad Auth happens)
    db = client.get_database()
    print(f"🔍 Attempting to list collections in '{db.name}'...")
    db.list_collection_names()
    print("🎉 AUTHENTICATION SUCCESSFUL! Your credentials are correct.")

except Exception as e:
    print(f"❌ CONNECTION FAILED: {e}")
    print("\nHELPFUL TIPS:")
    print("1. If it says 'bad auth', your password or username in .env is WRONG.")
    print("2. Ensure you removed the < and > brackets from your password.")
    print("3. Ensure your password doesn't have @, #, or ! symbols (or use a simple password).")
