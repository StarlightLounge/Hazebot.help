import discord
from discord.ext import commands
from discord import app_commands
from utils.logic import staff_or_owner
from utils.mongo import db

class Streamer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    stream_group = app_commands.Group(name="streamer", description="Multimedia: Manage live streaming announcements")

    @stream_group.command(name="setup", description="STAFF: Establish a thematic streaming district")
    @app_commands.describe(template="The current architecture template to match")
    @app_commands.choices(template=[
        app_commands.Choice(name="Elite Elysium", value="elysium"),
        app_commands.Choice(name="The Chronic Crypt", value="crypt"),
        app_commands.Choice(name="The Vibe Lounge", value="vibe"),
        app_commands.Choice(name="Elite Afterdark", value="afterdark")
    ])
    @staff_or_owner("administrator")
    async def setup_stream(self, interaction: discord.Interaction, template: str):
        await interaction.response.defer()
        guild = interaction.guild

        if template == "elysium":
            cat_name = "◌ [ NEURAL BROADCASTS ]"
            ch_name = "󠇲 ┇ ◌ live-transmissions"
        elif template == "crypt":
            cat_name = "◌ [ THE OSSUARY BROADCASTS ]"
            ch_name = "󠇲 ┇ ◌ spectral-streams"
        elif template == "vibe":
            cat_name = "◌ [ THE LOUNGE LIVE ]"
            ch_name = "󠇲 ┇ ◌ vibe-streams"
        elif template == "afterdark":
            cat_name = "◌ [ THE MIDNIGHT BROADCASTS ]"
            ch_name = "󠇲 ┇ ◌ unrestricted-live"
        else:
            cat_name = "◌ [ NEURAL BROADCASTS ]"
            ch_name = "󠇲 ┇ ◌ live-streams"

        # Create Category
        category = discord.utils.get(guild.categories, name=cat_name)
        if not category:
            category = await guild.create_category(cat_name)

        # Create Channel
        channel = await guild.create_text_channel(ch_name, category=category)
        
        # Save to DB
        db.set_stream_hub(guild.id, channel.id)

        embed = discord.Embed(
            title="🎥 STREAMING HUB ESTABLISHED",
            description=f"Nodes can now link their platforms and broadcast to {channel.mention} using `/streamer go_live`.",
            color=0x00FFCC
        )
        await interaction.followup.send(embed=embed)

    @stream_group.command(name="profile", description="Link your preferred streaming platform")
    @app_commands.describe(platform="Twitch, YouTube, Kick, etc.", link="Your direct channel URL")
    async def set_profile(self, interaction: discord.Interaction, platform: str, link: str):
        if not link.startswith("http"):
            return await interaction.response.send_message("❌ Invalid link format. Must start with http/https.", ephemeral=True)
            
        db.update_stream_profile(interaction.user.id, interaction.guild_id, platform, link)
        await interaction.response.send_message(f"✅ **Neural Link Established.** Platform set to **{platform}**.\nYou can now use `/streamer go_live` to announce your broadcasts.", ephemeral=True)

    @stream_group.command(name="go_live", description="Broadcast your stream to the entire server")
    @app_commands.describe(title="The title or topic of your current stream")
    async def go_live(self, interaction: discord.Interaction, title: str):
        guild_id = interaction.guild_id
        hub_id = db.get_stream_hub(guild_id)
        
        if not hub_id:
            return await interaction.response.send_message("❌ The High Architect has not established a Streaming Hub yet. (Tell staff to run `/streamer setup`)", ephemeral=True)
            
        hub = interaction.guild.get_channel(int(hub_id))
        if not hub:
            return await interaction.response.send_message("❌ Streaming Hub channel no longer exists.", ephemeral=True)

        user_data = db.get_user(interaction.user.id, guild_id)
        profile = user_data.get("stream_profile")
        
        if not profile:
            return await interaction.response.send_message("❌ You have not linked a streaming platform. Use `/streamer profile` first.", ephemeral=True)

        platform = profile.get("platform", "Unknown")
        link = profile.get("link", "#")

        # Thematic Styling
        is_crypt = "CRYPT" in interaction.guild.name.upper()
        color = 0x000000 if is_crypt else 0x9146FF # Twitch Purple / Obsidian

        embed = discord.Embed(
            title=f"🔴 {interaction.user.name.upper()} IS LIVE ON {platform.upper()}",
            description=f"**Topic:** {title}\n\n[**>> CLICK TO SYNCHRONIZE <<**]({link})",
            color=color
        )
        embed.set_author(name=f"TRANSMISSION: {platform}", icon_url=interaction.user.display_avatar.url)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="Neural Broadcast Protocol")

        await hub.send(content=f"@everyone {interaction.user.mention} is broadcasting!", embed=embed)
        await interaction.response.send_message("📡 **Broadcast Dispatched.** Your stream is now live on the server network.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Streamer(bot))
