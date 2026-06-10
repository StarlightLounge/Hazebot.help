import discord
from discord.ext import commands
from discord import app_commands

class Translation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    babel_group = app_commands.Group(name="babel", description="Linguistics: AI-powered translation protocols")

    @babel_group.command(name="sync", description="Translate any frequency into a different language")
    async def translate(self, interaction: discord.Interaction, text: str, language: str = "English"):
        from utils.ai import ai
        await interaction.response.defer()
        res = await ai.get_response(f"Translate this to {language}: {text}")
        await interaction.followup.send(res)

    @babel_group.command(name="link", description="Establish a real-time voice translation bridge")
    async def babel_link(self, interaction: discord.Interaction, target_lang: str):
        await interaction.response.send_message(f"🎙️ **Babel Link Active.** Synchronizing with `{target_lang}`...", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Translation(bot))
