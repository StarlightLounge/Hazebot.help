import sys
from pymongo import MongoClient

if len(sys.argv) < 5:
    print("Usage: python3 test_raw.py <user> <pass> <cluster_url> <db_name>")
    print("Example: python3 test_raw.py hazeadmin MyPass123 bot.8k9t40t.mongodb.net haze_bot")
    sys.exit(1)

user = sys.argv[1]
password = sys.argv[2]
cluster = sys.argv[3]
db_name = sys.argv[4]

# Manual URI building to prevent typos
uri = f"mongodb+srv://{user}:{password}@{cluster}/{db_name}?retryWrites=true&w=majority"

print(f"📡 Testing connection to {cluster} as user '{user}'...")

try:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    # Ping
    client.admin.command('ping')
    print("✅ Network OK.")
    
    # Auth Test
    db = client[db_name]
    db.list_collection_names()
    print("🎉 SUCCESS! Connection and Authentication are PERFECT.")
    print("\nUSE THIS EXACT URI IN YOUR .ENV:")
    print(uri)

except Exception as e:
    print(f"❌ FAILED: {e}")
    if "bad auth" in str(e).lower() or "authentication failed" in str(e).lower():
        print("\nREASON: The username or password is incorrect.")
        print("ACTION: Go to MongoDB Atlas -> Database Access and reset the password for this user.")
