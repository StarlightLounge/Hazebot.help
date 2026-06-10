import discord
from discord import app_commands
from utils.mongo import db

PRESTIGE_ROLES = {
    100: "〔 Ω 〕ETERNAL O.G.",
    75: "〔 Ψ 〕MYSTIC HERB",
    50: "〔 Φ 〕SYNDICATE KUSH",
    40: "〔 Σ 〕TITAN BUD",
    30: "〔 Δ 〕ELITE SMOKER",
    20: "〔 Λ 〕NOBLE BLAZER",
    10: "〔 Ζ 〕CITIZEN STONER",
    1: "〔 ⟡ 〕NEW BUD"
}

async def sync_member_roles(member: discord.Member, level: int):
    """
    Surgically aligns a member's roles based on their Tier.
    Removes outdated prestige roles and adds the correct one.
    """
    if not member.guild.me.guild_permissions.manage_roles:
        return

    # Determine target role based on level
    target_role_name = None
    for lv, name in sorted(PRESTIGE_ROLES.items(), reverse=True):
        if level >= lv:
            target_role_name = name
            break
    
    # If they are below level 10, they don't get a prestige role
    if not target_role_name:
        # Check if they have any old ones to remove
        old_roles = [r for r in member.roles if r.name in PRESTIGE_ROLES.values()]
        if old_roles:
            try: await member.remove_roles(*old_roles)
            except: pass
        return

    target_role = discord.utils.get(member.guild.roles, name=target_role_name)
    if not target_role:
        return

    # Roles to remove (all other prestige roles)
    to_remove = [r for r in member.roles if r.name in PRESTIGE_ROLES.values() and r.id != target_role.id]
    
    try:
        if to_remove:
            await member.remove_roles(*to_remove)
        if target_role not in member.roles:
            await member.add_roles(target_role)
    except discord.Forbidden:
        pass # Bot role is likely too low
    except Exception as e:
        print(f"Error syncing roles for {member.name}: {e}")

def get_xp_needed(level: int):
    """Calculation for XP needed to reach next level."""
    return level * 100

def get_xp_multiplier(member: discord.Member, user_data: dict):
    """Calculates total XP multiplier based on prestige and assets."""
    multiplier = 1.0
    
    # Prestige Multiplier ( +20% per Prestige level )
    prestige = user_data.get("prestige", 0)
    multiplier += (prestige * 0.2)
    
    # Staff Bonus
    roles = [r.name for r in member.roles]
    staff_roles = ["HIGH ARCHITECT", "CHRONIC ARBITER", "SYSTEM HASH"]
    if any(s in name.upper() for s in staff_roles for name in roles):
        multiplier += 0.5 # +50% XP for staff
        
    return multiplier

def get_progress_bar(current, total, length=10):
    """Generates a stylized text-based progress bar."""
    percent = current / total if total > 0 else 0
    filled = int(length * percent)
    bar = "▰" * filled + "▱" * (length - filled)
    return f"{bar} {int(percent * 100)}%"

def get_luck_bonus(member: discord.Member):
    """
    Returns a success percentage bonus based on roles and inventory assets.
    """
    roles = [r.name for r in member.roles]
    user_data = db.get_user(member.id, member.guild.id)
    inv = user_data.get("inventory", [])
    
    # 1. Staff Luck
    staff_roles = ["HIGH ARCHITECT", "CHRONIC ARBITER", "SYSTEM HASH"]
    base_bonus = 25 if any(s in name.upper() for s in staff_roles for name in roles) else 0
    
    # 2. Tier Luck
    tier_bonuses = {
        "ETERNAL O.G.": 20, "MYSTIC HERB": 15, "SYNDICATE KUSH": 12,
        "TITAN BUD": 10, "ELITE SMOKER": 7, "NOBLE BLAZER": 5, "CITIZEN STONER": 2
    }
    
    tier_bonus = 0
    for tier, bonus in tier_bonuses.items():
        if any(tier in name.upper() for name in roles):
            tier_bonus = max(tier_bonus, bonus)
                
    total_flat = base_bonus + tier_bonus
    
    # 3. Item Multipliers
    multiplier = 1.0
    if "🌋 The Volcano" in inv: multiplier += 0.2
    if "🔥 The Eternal Ember" in inv: multiplier += 1.0 # 2x Total Luck
    
    return int(total_flat * multiplier)

import os

def staff_or_owner(permission: str = None):
    """
    Check decorator that allows either the required permission OR the bot owner.
    """
    async def predicate(interaction: discord.Interaction) -> bool:
        raw_ids = os.getenv("OWNER_IDS", os.getenv("OWNER_ID", ""))
        owner_ids = [int(i.strip()) for i in raw_ids.split(",") if i.strip().isdigit()]
        
        # 1. Check if user is a Bot Owner
        if interaction.user.id in owner_ids:
            return True
            
        # 2. Check for specific permission if provided
        if permission:
            perms = interaction.user.guild_permissions
            if getattr(perms, permission, False):
                return True
        
        # 3. Default: Deny if neither match
        return False
    return app_commands.check(predicate)

def premium_only():
    """
    Check decorator that restricts commands to premium guilds.
    """
    async def predicate(interaction: discord.Interaction) -> bool:
        if db.is_premium(interaction.guild_id):
            return True
            
        # If not premium, send a clean upsell message
        embed = discord.Embed(
            title="💎 ELITE PREMIUM REQUIRED",
            description=(
                "This protocol is exclusive to **Elite Premium** servers.\n\n"
                "**Premium Features:**\n"
                "◈ 2x Daily Rewards & Half Cooldowns\n"
                "◈ High-Fidelity Audio & Saveable Playlists\n"
                "◈ Advanced `/nuke` Moderation tools\n"
                "◈ Priority AI Neural Processing\n\n"
                "Contact the **High Architect** to upgrade your node."
            ),
            color=0xFDB931
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return False
    return app_commands.check(predicate)

def elite_only():
    """Check decorator to restrict commands to Elite-enabled servers."""
    async def predicate(interaction: discord.Interaction):
        if not db.is_elite_enabled(interaction.guild_id):
            await interaction.response.send_message("❌ **Access Denied.** Elite Elysium protocols are offline in this sector.", ephemeral=True)
            return False
        return True
    return app_commands.check(predicate)
