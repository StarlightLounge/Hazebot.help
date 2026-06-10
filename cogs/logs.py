import discord
from discord.ext import commands
from utils.mongo import db

class NeuralLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_log_channel(self, guild):
        try:
            if not db.connected: return discord.utils.get(guild.channels, name="terminal-logs")
            
            guild_data = db.guilds.find_one({"guild_id": str(guild.id)})
            if guild_data and "stats_channels" in guild_data:
                ch_id = guild_data["stats_channels"].get("logs")
                if ch_id:
                    return guild.get_channel(int(ch_id))
        except: pass
        
        return discord.utils.get(guild.channels, name="terminal-logs")

    @commands.Cog.listener()
    async def on_app_command_completion(self, interaction, command):
        try:
            # We only log administrative or sensitive commands
            admin_commands = ["set_level", "add_xp", "set_balance", "reset_account", "setup_elysium", "purge"]
            if command.name not in admin_commands:
                return

            log_ch = await self.get_log_channel(interaction.guild)
            if not log_ch: return

            embed = discord.Embed(
                title="💾 LOG: ADMINISTRATIVE OVERRIDE",
                description=f"**Command:** `/{command.name}`\n**Operator:** {interaction.user.mention}\n**Channel:** {interaction.channel.mention}",
                color=0x3498db,
                timestamp=interaction.created_at
            )
            
            # Capture options if possible
            options = interaction.data.get("options", [])
            if options:
                opt_str = "\n".join([f"• {o['name']}: `{o['value']}`" for o in options])
                embed.add_field(name="Parameters", value=opt_str)

            await log_ch.send(embed=embed)
        except: pass

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        try:
            # Log prestige role changes
            prestige_roles = ["〔 Ω 〕ETERNAL", "〔 Ψ 〕MYSTIC", "〔 Φ 〕SYNDICATE", "〔 Σ 〕TITAN", "〔 Δ 〕ELITE", "〔 Λ 〕NOBLE", "〔 Ζ 〕CITIZEN", "〔 ⟡ 〕GUEST"]
            
            b_roles = set(r.name for r in before.roles)
            a_roles = set(r.name for r in after.roles)
            
            added = a_roles - b_roles
            for role_name in added:
                if role_name in prestige_roles:
                    log_ch = await self.get_log_channel(after.guild)
                    if not log_ch: return
                    
                    embed = discord.Embed(
                        title="✨ LOG: NEURAL ASCENSION",
                        description=f"**Subject:** {after.mention}\n**New Tier:** `{role_name}`",
                        color=0xf1c40f
                    )
                    await log_ch.send(embed=embed)
        except: pass

async def setup(bot):
    await bot.add_cog(NeuralLogs(bot))
