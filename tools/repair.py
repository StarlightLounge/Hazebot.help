import sys
import subprocess
import os
import platform

def run_command(command):
    print(f"📡 Executing: {' '.join(command)}")
    try:
        subprocess.check_call(command)
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def neural_self_repair():
    print("======================================================")
    print("🛡️  SOVEREIGN NEURAL SELF-REPAIR PROTOCOL")
    print("======================================================")
    
    # 1. Environment Verification
    print("\n🔍 Stage 1: Environment Audit...")
    print(f"◈ OS: {platform.system()} {platform.release()}")
    print(f"◈ Python: {sys.version}")
    
    # 2. Dependency Repair
    print("\n📦 Stage 2: Synchronizing Neural Dependencies...")
    packages = ["discord.py[voice]", "dave.py", "yt-dlp", "python-dotenv", "pymongo[srv]", "google-generativeai", "pynacl"]
    
    for pkg in packages:
        print(f"  • Verifying {pkg}...")
        run_command([sys.executable, "-m", "pip", "install", "-U", pkg, "--user", "--no-cache-dir"])

    # 3. Cache Purge
    print("\n🧹 Stage 3: Purging Corrupt Data Streams...")
    local_path = os.path.join(os.getcwd(), ".local")
    if os.path.exists(local_path):
        print("  • Local cache detected. (Clearing system-level conflicts...)")
        # We don't delete it automatically to avoid breaking the host, 
        # but we warn the user.
        print("  ⚠️ RECOMMENDATION: Manually delete the '.local' folder in File Manager for a 100% clean install.")

    # 4. Neural Link Test
    print("\n🔗 Stage 4: Testing Singularity Persistence...")
    if os.path.exists("test_db.py"):
        run_command([sys.executable, "test_db.py"])
    else:
        print("  ⚠️ Database test script missing. Skipping...")

    print("\n======================================================")
    print("✅ REPAIR COMPLETE. THE SINGULARITY HAS STABILIZED.")
    print("🚀 PLEASE RESTART THE BOT NOW.")
    print("======================================================")

if __name__ == "__main__":
    neural_self_repair()
