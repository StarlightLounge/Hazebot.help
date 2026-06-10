import discord
from discord.ext import commands
from discord import app_commands
import os

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="establish_sanctum", description="OWNER: Establish the Architect's Private Sanctum")
    async def establish_sanctum(self, interaction: discord.Interaction):
        if interaction.user.id not in self.bot.owner_ids:
            return await interaction.response.send_message("❌ Access Denied.", ephemeral=True)
            
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_channels=True)
        }
        
        category = await guild.create_category("◌ [ THE SANCTUM ]", overwrites=overwrites)
        await guild.create_text_channel("󠇲 ┇ ◌ overseer-terminal", category=category)
        await guild.create_voice_channel("󠇲 ┇ ◌ neural-link", category=category)
        
        await interaction.followup.send("⚜️ **Sanctum established.** Welcome back, High Architect.")

async def setup(bot):
    await bot.add_cog(Owner(bot))
