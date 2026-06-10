import sys
import os
from pymongo import MongoClient

if len(sys.argv) < 3:
    print("❌ ERROR: You must provide a username and password.")
    print("Usage: python3 force_fix_db.py <username> <password>")
    sys.exit(1)

user = sys.argv[1]
password = sys.argv[2]
cluster = "bot.8k9t40t.mongodb.net"
db_name = "haze_bot"

# Build URI
uri = f"mongodb+srv://{user}:{password}@{cluster}/{db_name}?retryWrites=true&w=majority"

print(f"📡 Attempting Force-Link to {cluster}...")

try:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    # Test Auth
    client.admin.command('ping')
    print("✅ AUTHENTICATION SUCCESSFUL!")
    
    # If successful, fix the .env file
    print("📝 Rewriting .env file with verified neural link...")
    
    with open(".env", "r") as f:
        lines = f.readlines()
    
    with open(".env", "w") as f:
        for line in lines:
            if line.startswith("MONGO_URI="):
                f.write(f"MONGO_URI={uri}\n")
            else:
                f.write(line)
                
    print("✨ .env file updated successfully.")
    print("🚀 RESTART THE BOT NOW.")

except Exception as e:
    print(f"❌ LINK FAILED: {e}")
    print("\nPOSSIBLE CAUSES:")
    print("1. Password is still wrong in Atlas.")
    print("2. You haven't clicked 'Update User' after changing the password in Atlas.")
    print("3. Special characters in password (try using only letters and numbers).")
