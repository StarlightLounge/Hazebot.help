import discord
from discord.ext import commands
from discord import app_commands
import datetime
import asyncio
from utils.mongo import db
from utils.logic import premium_only, staff_or_owner

class VerificationReview(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def get_gender_role(self, guild, gender):
        # Neural mapping for gender roles across all templates
        role_map = {
            "MALE": ["〔 👑 〕SOVEREIGN KING", "〔 💀 〕CRYPT KING", "〔 👑 〕LOUNGE KING"],
            "FEMALE": ["〔 👸 〕SOVEREIGN QUEEN", "〔 🕯️ 〕CRYPT QUEEN", "〔 👸 〕LOUNGE QUEEN"]
        }
        for name in role_map[gender]:
            role = discord.utils.get(guild.roles, name=name)
            if role: return role
        return None

    @discord.ui.button(label="18+ KING", style=discord.ButtonStyle.success, custom_id="verify_18_king", emoji="👑")
    async def approve_18_king(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_royal_approval(interaction, "〔 🔞 〕VERIFIED 18+", "MALE")

    @discord.ui.button(label="18+ QUEEN", style=discord.ButtonStyle.success, custom_id="verify_18_queen", emoji="👸")
    async def approve_18_queen(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_royal_approval(interaction, "〔 🔞 〕VERIFIED 18+", "FEMALE")

    @discord.ui.button(label="21+ KING", style=discord.ButtonStyle.primary, custom_id="verify_21_king", emoji="👑")
    async def approve_21_king(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_royal_approval(interaction, "〔 🍺 〕VERIFIED 21+", "MALE")

    @discord.ui.button(label="21+ QUEEN", style=discord.ButtonStyle.primary, custom_id="verify_21_queen", emoji="👸")
    async def approve_21_queen(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_royal_approval(interaction, "〔 🍺 〕VERIFIED 21+", "FEMALE")

    @discord.ui.button(label="DENY", style=discord.ButtonStyle.danger, custom_id="verify_deny")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            user_id = int(interaction.message.embeds[0].footer.text.split("ID: ")[1])
            member = interaction.guild.get_member(user_id)
            await interaction.response.send_message(f"🚫 **Verification Denied.** Removing sensitive data...", ephemeral=True)
            if member:
                try: await member.send("❌ **Haze Bot: Verification Denied.** Your submission did not meet our neural standards.")
                except: pass
            await interaction.message.delete()
        except:
            await interaction.response.send_message("❌ Failed to process denial.", ephemeral=True)

    async def process_royal_approval(self, interaction, age_role_name, gender):
        try:
            user_id = int(interaction.message.embeds[0].footer.text.split("ID: ")[1])
            member = interaction.guild.get_member(user_id)
            if not member: 
                await interaction.response.send_message("❌ Subject left the sector.", ephemeral=True)
                return await interaction.message.delete()

            # 1. Age Role
            age_role = discord.utils.get(interaction.guild.roles, name=age_role_name)
            
            # 2. Gender Role
            gender_role = await self.get_gender_role(interaction.guild, gender)

            # 3. Base Verified Role
            base_verified = discord.utils.get(interaction.guild.roles, name="〔 👤 〕VERIFIED MEMBER")
            if not base_verified: base_verified = discord.utils.get(interaction.guild.roles, name="VERIFIED MEMBER")

            roles_to_add = []
            if age_role: roles_to_add.append(age_role)
            if gender_role: roles_to_add.append(gender_role)
            if base_verified: roles_to_add.append(base_verified)

            if roles_to_add:
                await member.add_roles(*roles_to_add)
                db.update_user(member.id, interaction.guild_id, {"is_age_verified": True, "verified_tier": age_role_name, "gender_alignment": gender})
                
                await interaction.response.send_message(f"✅ **Royal Alignment Complete.** {member.name} verified as **{age_role_name} {gender}**.", ephemeral=True)
                try: await member.send(f"✅ **Haze Bot: Verification Successful.** You have been aligned with the **{age_role_name}**, **{gender}**, and **Verified Member** frequencies!")
                except: pass
                
                # Privacy Protocol
                await interaction.message.delete()
            else:
                await interaction.response.send_message("❌ Error: Verification roles not found in hierarchy.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    verification_group = app_commands.Group(name="verification", description="Manage sector verification protocols")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Privacy Shield: Deletes standard messages in verification channels."""
        if message.author.bot: return
        if any(x in message.channel.name for x in ["verify-here", "age-verification", "verification-hub", "shadow-gate"]):
            try: await message.delete()
            except: pass

    @app_commands.command(name="verify", description="Submit your ID for age-verification (18+ or 21+)")
    @app_commands.describe(id_image="Upload a clear image of your ID", type="Target verification tier")
    @app_commands.choices(type=[
        app_commands.Choice(name="🔞 18+ Verification", value="18"),
        app_commands.Choice(name="🍺 21+ Verification", value="21")
    ])
    async def verify(self, interaction: discord.Interaction, id_image: discord.Attachment, type: str):
        if not id_image.content_type or "image" not in id_image.content_type:
            return await interaction.response.send_message("❌ Please upload a valid image file.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        # 1. Locate Staff Hub (Flexible Detection)
        hub_names = ["󠇲 ┇ ◌ verification-hub", "󠇲 ┇ ◌ grave-logs", "󠇲 ┇ ◌ void-logs", "󠇲 ┇ ◌ terminal-logs", "󠇲 ┇ ◌ staff-chat", "󠇲 ┇ ◌ bot-alerts"]
        hub = None
        for name in hub_names:
            hub = discord.utils.get(interaction.guild.text_channels, name=name)
            if hub: break
              
        if not hub:
            return await interaction.followup.send("❌ **Neural Error.** Staff Hub not found in this sector. (Ask staff to ensure logs are online).", ephemeral=True)

        # 2. Dispatch to Staff
        embed = discord.Embed(
            title="🛰️ NEW VERIFICATION SUBMISSION",
            description=f"Subject {interaction.user.mention} is requesting **{type}+** access.\n\n**◈ DISCORD ID:** `{interaction.user.id}`",
            color=0x00FFCC,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.set_image(url=id_image.url)
        embed.set_footer(text=f"Subject ID: {interaction.user.id}")
        
        await hub.send(embed=embed, view=VerificationReview())
        await interaction.followup.send("✅ **Neural Transmission Sent.** Your ID has been delivered to the High Architects for review.", ephemeral=True)

    @verification_group.command(name="setup", description="STAFF: Establish a specialized Verification Gate for this sector")
    @app_commands.describe(template="The visual aesthetic for the portal")
    @app_commands.choices(template=[
        app_commands.Choice(name="The High Society (Clean/Modern)", value="highsociety"),
        app_commands.Choice(name="The Chronic Crypt (Dark/Gothic)", value="crypt"),
        app_commands.Choice(name="Elite Afterdark (Shadow/Neon)", value="afterdark"),
        app_commands.Choice(name="Standard Protocol", value="standard")
    ])
    @staff_or_owner("administrator")
    async def verification_setup(self, interaction: discord.Interaction, template: str):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild

        # 1. Ensure Roles Exist
        role_configs = [
            ("〔 🔞 〕VERIFIED 18+", 0xe74c3c),
            ("〔 🍺 〕VERIFIED 21+", 0xf1c40f),
            ("〔 👤 〕VERIFIED MEMBER", 0x2ecc71)
        ]
        for name, color in role_configs:
            if not discord.utils.get(guild.roles, name=name):
                try: await guild.create_role(name=name, color=discord.Color(color))
                except: pass

        # 2. Configure Aesthetic
        configs = {
            "highsociety": {
                "title": "🛡️ NEURAL VERIFICATION GATE",
                "desc": "Welcome to the inner sanctum. To unlock the full potential of this sector, you must verify your identity.\n\n**◈ PROTOCOL:** Use the `/verify` command.\n**◈ REQUIREMENT:** Clear photo of ID with DOB visible.\n\n**🛡️ PRIVACY SHIELD:** Submissions are ephemeral.",
                "color": 0x00FFCC,
                "name": "󠇲 ┇ ◌ verify-here"
            },
            "crypt": {
                "title": "💀 THE HIGH ALTAR: AGE VERIFICATION",
                "desc": "New nodes must be vetted before entering the deeper catacombs.\n\n**◈ PROTOCOL:** Use the `/verify` command.\n**◈ REQUIREMENT:** Clear photo of ID with DOB visible.\n\n**🛡️ NEURAL PRIVACY:** Sensitive data is purged after review.",
                "color": 0x000000,
                "name": "󠇲 ┇ ◌ age-verification"
            },
            "afterdark": {
                "title": "🌑 THE SHADOW GATE: AGE VERIFICATION",
                "desc": "Access to the unrestricted Midnight districts requires verified neural maturity.\n\n**◈ PROTOCOL:** Use the `/verify` command.\n**◈ REQUIREMENT:** Clear photo of ID with DOB visible.\n\n**🛡️ PRIVACY SHIELD:** Submissions are handled by Afterdark Overseers.",
                "color": 0x3c3c3c,
                "name": "󠇲 ┇ ◌ shadow-gate-verification"
            },
            "standard": {
                "title": "✅ SECTOR VERIFICATION",
                "desc": "Please verify your age to gain access to the rest of the server.\n\n**◈ PROTOCOL:** Use the `/verify` command.\n**◈ REQUIREMENT:** ID image with visible DOB.",
                "color": 0x2ecc71,
                "name": "󠇲 ┇ ◌ verification"
            }
        }
        
        cfg = configs.get(template)
        
        # 3. Setup Channel
        category = discord.utils.get(guild.categories, name="◌ [ THE ENTRANCE ]")
        if not category: category = discord.utils.get(guild.categories, name="◌ [ INITIALIZATION ]")
        
        channel = await guild.create_text_channel(cfg["name"], category=category)
        
        # 4. Overwrites: Unlocked for everyone to see
        await channel.set_permissions(guild.default_role, view_channel=True, send_messages=False, read_message_history=True)
        
        embed = discord.Embed(title=cfg["title"], description=cfg["desc"], color=cfg["color"])
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        
        await channel.send(embed=embed)
        await interaction.followup.send(f"✅ **Verification Portal Online.** Portal synchronized in {channel.mention}.", ephemeral=True)

    @app_commands.command(name="setup_verification_afterdark", description="STAFF: Establish the Shadow Gate Verification for Elite Afterdark 18+")
    @staff_or_owner("administrator")
    async def setup_verification_afterdark(self, interaction: discord.Interaction):
        await self.verification_setup.callback(self, interaction, "afterdark")

    @app_commands.command(name="setup_verification_crypt", description="STAFF: Establish the High Altar Verification Gate for the Chronic Crypt")
    @staff_or_owner("administrator")
    async def setup_verification_crypt(self, interaction: discord.Interaction):
        await self.verification_setup.callback(self, interaction, "crypt")

async def setup(bot):
    await bot.add_cog(Verification(bot))

async def setup(bot):
    await bot.add_cog(Verification(bot))
