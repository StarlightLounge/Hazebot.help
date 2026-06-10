#!/bin/bash
echo "🛡️ Linkage: Stabilizing Neural Voice & Dependencies..."

# 1. Force install discord.py with full extras to satisfy DAVE and Voice requirements
python3 -m pip install -U "discord.py[voice]" --user --no-cache-dir

# 2. Add extra DAVE support if missed
python3 -m pip install dave.py --user

# 3. Final dependency sweep
python3 -m pip install -r requirements.txt --user

echo "🚀 Launching Haze Bot Singularity..."
python3 bot.py
