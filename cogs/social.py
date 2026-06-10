import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import datetime
from utils.logic import staff_or_owner

class GiveawayView(discord.ui.View):
    def __init__(self, prize, end_time):
        super().__init__(timeout=None) # Persistent
        self.prize = prize
        self.end_time = end_time
        self.participants = []

    @discord.ui.button(label="Enter Sync (0)", style=discord.ButtonStyle.success, emoji="🎉", custom_id="giveaway_enter")
    async def enter(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.participants:
            return await interaction.response.send_message("❌ You are already synchronized with this giveaway.", ephemeral=True)
        
        self.participants.append(interaction.user.id)
        button.label = f"Enter Sync ({len(self.participants)})"
        await interaction.response.edit_message(view=self)
        await interaction.followup.send("✅ **Neural Link Established.** You have entered the giveaway.", ephemeral=True)

class Social(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.starboard_threshold = 3 
        self.starboard_channel_name = "󠇲 ┇ ◌ high-vibes"

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if str(payload.emoji) not in ["🌿", "⭐", "🔥"]: return
        channel = self.bot.get_channel(payload.channel_id)
        if not channel or not isinstance(channel, discord.TextChannel): return
        message = await channel.fetch_message(payload.message_id)
        if message.author.bot: return
        reaction = discord.utils.get(message.reactions, emoji=payload.emoji.name)
        if not reaction or reaction.count < self.starboard_threshold: return
        starboard_ch = discord.utils.get(message.guild.text_channels, name=self.starboard_channel_name)
        if not starboard_ch: return
        async for msg in starboard_ch.history(limit=50):
            if f"ID: {message.id}" in msg.content or (msg.embeds and f"ID: {message.id}" in str(msg.embeds[0].footer.text)):
                return
        embed = discord.Embed(description=message.content or "[Attached Asset]", color=0xFDB931, timestamp=message.created_at)
        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
        embed.add_field(name="◈ SOURCE", value=f"[Jump to Message]({message.jump_url})", inline=False)
        if message.attachments: embed.set_image(url=message.attachments[0].url)
        embed.set_footer(text=f"High Vibe Score: {reaction.count} | ID: {message.id}")
        await starboard_ch.send(content=f"🌟 **Neural Highlight in {channel.mention}**", embed=embed)

    @app_commands.command(name="poll", description="Initialize a multi-choice frequency poll")
    @app_commands.describe(question="The topic of the poll", option1="Choice A", option2="Choice B", option3="Choice C (Optional)")
    async def poll(self, interaction: discord.Interaction, question: str, option1: str, option2: str, option3: str = None):
        embed = discord.Embed(title="📊 SOVEREIGN POLL", description=f"**{question}**", color=0x3498db)
        options = f"1️⃣ {option1}\n2️⃣ {option2}"
        if option3: options += f"\n3️⃣ {option3}"
        embed.add_field(name="◈ FREQUENCIES", value=options)
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()
        await msg.add_reaction("1️⃣"); await msg.add_reaction("2️⃣")
        if option3: await msg.add_reaction("3️⃣")

    @app_commands.command(name="giveaway", description="Launch a professional influence giveaway")
    @staff_or_owner(permission="manage_guild")
    async def giveaway(self, interaction: discord.Interaction, prize: str, duration_mins: int):
        end_time = datetime.datetime.now() + datetime.timedelta(minutes=duration_mins)
        embed = discord.Embed(title="🎉 INCOMING GIVEAWAY", description=f"**Prize:** {prize}\n\n**Ends:** <t:{int(end_time.timestamp())}:R>\n**Hosted by:** {interaction.user.mention}", color=0xFDB931)
        view = GiveawayView(prize, end_time)
        await interaction.response.send_message(embed=embed, view=view)
        await asyncio.sleep(duration_mins * 60)
        if not view.participants:
            return await interaction.edit_original_response(embed=discord.Embed(title="🎉 GIVEAWAY ENDED", description=f"**Prize:** {prize}\n\n**Result:** Neural Link Failure.", color=0xff4d4d), view=None)
        winner = await self.bot.fetch_user(random.choice(view.participants))
        await interaction.edit_original_response(embed=discord.Embed(title="🎉 GIVEAWAY CONCLUDED", description=f"**Prize:** {prize}\n\n**Winner:** {winner.mention}", color=0x2ecc71), view=None)
        await interaction.channel.send(f"🎊 **Congratulations {winner.mention}!** Secured the **{prize}**.")

    @app_commands.command(name="transmit", description="Sovereign Communication: Broadcast a high-fidelity transmission")
    @app_commands.describe(content="Your transmission data", asset="Optional visual data (image)", type="Transmission mode")
    @app_commands.choices(type=[
        app_commands.Choice(name="Standard Protocol", value="standard"),
        app_commands.Choice(name="Unfiltered (Afterdark/NSFW)", value="unfiltered")
    ])
    async def transmit(self, interaction: discord.Interaction, content: str, type: str = "standard", asset: discord.Attachment = None):
        """High-end social posting command for mature communities."""
        if type == "unfiltered" and not interaction.channel.nsfw:
            return await interaction.response.send_message("❌ **Neural Conflict.** Unfiltered transmissions must be synchronized in an **Age-Restricted** frequency.", ephemeral=True)

        await interaction.response.defer()
        
        # Vibe Detection
        is_crypt = "CRYPT" in interaction.guild.name.upper()
        
        embed = discord.Embed(
            description=content,
            color=0x00FFCC if type == "standard" else (0x000000 if is_crypt else 0xe74c3c),
            timestamp=datetime.datetime.now()
        )
        embed.set_author(name=f"TRANSMISSION: {interaction.user.name.upper()}", icon_url=interaction.user.display_avatar.url)
        
        if asset:
            if asset.content_type and "image" in asset.content_type:
                embed.set_image(url=asset.url)
            else:
                return await interaction.followup.send("❌ Invalid asset format. Only images are permitted.", ephemeral=True)

        if type == "unfiltered":
            footer_text = "CRYPT SHADOW TRANSMISSION" if is_crypt else "AFTERDARK UNFILTERED ACCESS"
        else:
            footer_text = "Singularity Standard Protocol"
            
        embed.set_footer(text=footer_text)
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="say", description="STAFF: Broadcast a neural message through the bot")
    @app_commands.describe(message="The message to broadcast", embed="Should the message be embedded?", asset="Optional image to attach")
    @staff_or_owner("manage_messages")
    async def say(self, interaction: discord.Interaction, message: str, embed: bool = False, asset: discord.Attachment = None):
        """Allows staff to make the bot speak in the current channel."""
        await interaction.response.defer(ephemeral=True)
        
        if embed:
            msg_embed = discord.Embed(
                description=message,
                color=0x00FFCC
            )
            msg_embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
            
            if asset:
                if asset.content_type and "image" in asset.content_type:
                    msg_embed.set_image(url=asset.url)
                else:
                    return await interaction.followup.send("❌ Invalid asset format. Only images are permitted.", ephemeral=True)
            
            await interaction.channel.send(embed=msg_embed)
        else:
            files = []
            if asset:
                files.append(await asset.to_file())
            await interaction.channel.send(content=message, files=files)
            
        await interaction.followup.send("✅ **Broadcast Dispatched.**", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Social(bot))
