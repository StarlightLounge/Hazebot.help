import discord
from discord.ext import commands
from discord import app_commands
from utils.mongo import db
from utils.logic import staff_or_owner, elite_only
import datetime
import asyncio

class Sentinel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    sentinel_group = app_commands.Group(name="sentinel", description="Security: Manage server protection protocols")

    @sentinel_group.command(name="status", description="Check the status of the server's security grid")
    @staff_or_owner("manage_guild")
    async def status(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🛡️ SENTINEL SECURITY GRID", color=0x00FFCC)
        embed.add_field(name="◈ Status", value="`🟢 ACTIVE`")
        embed.add_field(name="◈ Anti-Spam", value="`ON`")
        embed.add_field(name="◈ Invite Blocker", value="`ON`")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @sentinel_group.command(name="nuke", description="PREMIUM: Advanced surgical purge of messages")
    @app_commands.describe(limit="Number of messages to scan", user="Target a specific user", keyword="Target a specific keyword")
    @staff_or_owner("manage_messages")
    async def nuke(self, interaction: discord.Interaction, limit: int = 100, user: discord.Member = None, keyword: str = None):
        await interaction.response.defer(ephemeral=True)
        def check(m):
            if user and m.author.id != user.id: return False
            if keyword and keyword.lower() not in m.content.lower(): return False
            return True
        deleted = await interaction.channel.purge(limit=limit, check=check)
        embed = discord.Embed(title="☢️ SURGICAL NUKE COMPLETE", description=f"Neural pathways cleansed in {interaction.channel.mention}.", color=0xff4d4d)
        embed.add_field(name="◈ NODES PURGED", value=f"`{len(deleted)}`", inline=True)
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Sentinel(bot))
