import sys
from pymongo import MongoClient
import os

# --- MASTER CONNECTION FIXER ---
# Use this script to verify your EXACT Atlas connection string.

if len(sys.argv) < 2:
    print("❌ ERROR: Missing Connection String.")
    print("\nHow to use:")
    print("1. Go to MongoDB Atlas -> Clusters -> Connect -> Drivers.")
    print("2. Copy the LONG link (mongodb+srv://...)")
    print("3. Type: python3 master_fix.py \"PASTE_YOUR_LINK_HERE\"")
    print("\n⚠️ IMPORTANT: Make sure you replace <password> with your actual password in the link!")
    sys.exit(1)

full_uri = sys.argv[1]

# Force the database name if not present
if "/haze_bot" not in full_uri:
    if "?" in full_uri:
        full_uri = full_uri.replace("?", "/haze_bot?")
    else:
        full_uri += "/haze_bot"

print(f"📡 Testing Neural Link: {full_uri.split('@')[-1]}")

try:
    # We add tlsAllowInvalidCertificates just in case Bisect has old SSL certificates
    client = MongoClient(full_uri, serverSelectionTimeoutMS=5000, tlsAllowInvalidCertificates=True)
    
    # Test 1: Network Ping
    client.admin.command('ping')
    print("✅ Stage 1: Network Connection Established.")
    
    # Test 2: Authentication (This is where it usually fails)
    db = client.get_database()
    print(f"🔍 Stage 2: Attempting to access '{db.name}'...")
    db.list_collection_names()
    print("🎉 STAGE 2: AUTHENTICATION SUCCESSFUL!")
    
    # If we got here, the link is 100% correct.
    print("\n📝 REWRITING .ENV FILE...")
    
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            lines = f.readlines()
        with open(".env", "w") as f:
            found = False
            for line in lines:
                if line.startswith("MONGO_URI="):
                    f.write(f"MONGO_URI={full_uri}\n")
                    found = True
                else:
                    f.write(line)
            if not found:
                f.write(f"\nMONGO_URI={full_uri}\n")
    else:
        with open(".env", "w") as f:
            f.write(f"MONGO_URI={full_uri}\n")

    print("✨ Verified neural link saved to .env.")
    print("🚀 RESTART THE BOT NOW.")

except Exception as e:
    print(f"❌ LINK FAILED: {e}")
    print("\nTROUBLESHOOTING:")
    print("1. Did you remove the < and > around your password?")
    print("2. Is your username 'hazeadmin' or 'v2lunartv_db_user'?")
    print("3. Does your password have symbols? (If so, reset it in Atlas to just letters and numbers).")
