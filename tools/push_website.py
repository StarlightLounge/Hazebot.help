import os
import base64
import json
import aiohttp
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def push_file(session, repo, path, content, token, message):
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}"}
    
    # 1. Get SHA
    async with session.get(url, headers=headers) as resp:
        sha = None
        if resp.status == 200:
            data = await resp.json()
            sha = data['sha']
    
    # 2. Push
    encoded_content = base64.b64encode(content.encode()).decode()
    payload = {
        "message": message,
        "content": encoded_content,
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha
        
    async with session.put(url, headers=headers, json=payload) as resp:
        if resp.status in [200, 201]:
            print(f"✅ Synchronized: {path}")
        else:
            print(f"❌ Failed {path}: {await resp.text()}")

async def main():
    token = os.getenv("GITHUB_TOKEN")
    repo = "StarlightLounge/Hazebot.help"
    if not token:
        print("❌ Error: GITHUB_TOKEN not found in .env")
        return

    files = ["index.html", "help.html", "styles.css", "script.js"]
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for file_path in files:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                tasks.append(push_file(session, repo, file_path, content, token, f"🛰️ Neural Sync: High-fidelity web update"))
            else:
                print(f"⚠️ Skipping {file_path}: File not found locally.")
        
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
