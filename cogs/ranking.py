import discord
from discord.ext import commands
from discord import app_commands
from utils.mongo import db
from utils.logic import sync_member_roles, elite_only

class Ranking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    rank_group = app_commands.Group(name="rank", description="Hierarchy: View server and global neural standings")

    @rank_group.command(name="leaderboard", description="Show the top subjects in the server hierarchy")
    @app_commands.describe(sort_by="Metric to sort by (level, tokes, coins)")
    @elite_only()
    async def leaderboard(self, interaction: discord.Interaction, sort_by: str = "level"):
        mapping = {"level": "level", "tokes": "puff_count", "coins": "hash_coins"}
        sort_key = mapping.get(sort_by.lower())
        if not sort_key: return await interaction.response.send_message("❌ Invalid metric.", ephemeral=True)
        await interaction.response.defer()
        users = db.get_leaderboard(interaction.guild_id, sort_by=sort_key, limit=10)
        embed = discord.Embed(title=f"🏆 SOVEREIGN LEADERBOARD", description=f"Rankings: **{sort_by.upper()}**", color=0xF1C40F)
        leader_str = ""
        for i, user in enumerate(users, 1):
            try:
                member = await self.bot.fetch_user(int(user["user_id"]))
                name = member.name
            except:
                name = f"Node {user['user_id']}"
            leader_str += f"`{i}.` **{name}** — `{user.get(sort_key, 0):,}`\n"
        embed.description += f"\n\n{leader_str}"
        await interaction.followup.send(embed=embed)

    @rank_group.command(name="global", description="Sovereign Ranking: Compare your frequency globally")
    async def global_top(self, interaction: discord.Interaction):
        await interaction.response.defer()
        pipeline = [{"$group": {"_id": "$user_id", "max_level": {"$max": "$level"}, "total_prestige": {"$max": "$prestige"}}}, {"$sort": {"total_prestige": -1, "max_level": -1}}, {"$limit": 10}]
        global_users = list(db.users.aggregate(pipeline))
        embed = discord.Embed(title="🌌 GLOBAL STANDINGS", color=0xFDB931)
        leaderboard_str = ""
        for i, data in enumerate(global_users, 1):
            try:
                member = await self.bot.fetch_user(int(data["_id"]))
                name = member.name
            except:
                name = f"Node {data['_id']}"
            leaderboard_str += f"`{i}.` **{name}** ◈ Prestige `{data['total_prestige']}` ◈ Tier `{data['max_level']}`\n"
        embed.add_field(name="◈ TOP SUBJECTS", value=leaderboard_str)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="prestige", description="Ascend to the next level of existence (Resets Level to 1)")
    @elite_only()
    async def prestige(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id, interaction.guild_id)
        if user.get("level", 1) < 100: return await interaction.response.send_message("❌ Tier 100 Required.", ephemeral=True)
        new_prestige = user.get("prestige", 0) + 1
        db.update_user(interaction.user.id, interaction.guild_id, {"level": 1, "xp": 0, "prestige": new_prestige})
        await sync_member_roles(interaction.user, 1)
        await interaction.response.send_message(f"✨ **Ascension Complete.** Prestige `{new_prestige}` achieved!")

    @rank_group.command(name="set_level", description="STAFF: Manually set a user's Tier")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_level(self, interaction: discord.Interaction, member: discord.Member, level: int):
        db.update_user(member.id, interaction.guild_id, {"level": level, "xp": 0})
        await sync_member_roles(member, level)
        await interaction.response.send_message(f"✅ Tier set to `{level}`.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Ranking(bot))
