import discord
from discord.ext import commands
from discord import app_commands
import os
from utils.mongo import db

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.owner_id = int(os.getenv("OWNER_ID", 0))

    def is_owner(self, interaction: discord.Interaction):
        return interaction.user.id == self.owner_id

    @app_commands.command(name="admin_add_hash_coins", description="GOD MODE: Add hash coins to user")
    async def add_hash_coins(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if not self.is_owner(interaction):
            return await interaction.response.send_message("❌ OWNER ONLY", ephemeral=True)

        user = db.get_user(member.id, interaction.guild.id)
        db.update_user(member.id, interaction.guild.id, {"hash_coins": user["hash_coins"] + amount})
        await interaction.response.send_message(f"✅ Added {amount} hash coins to {member.mention}.")

    @app_commands.command(name="admin_set_puffs", description="GOD MODE: Set user puff count")
    async def set_puffs(self, interaction: discord.Interaction, member: discord.Member, count: int):
        if not self.is_owner(interaction):
            return await interaction.response.send_message("❌ OWNER ONLY", ephemeral=True)
        db.update_user(member.id, interaction.guild.id, {"puff_count": count})
        await interaction.response.send_message(f"✅ Set {member.mention}'s puff count to {count}.")

    @app_commands.command(name="admin_servers", description="GOD MODE: Server list")
    async def servers(self, interaction: discord.Interaction):
        if not self.is_owner(interaction):
            return await interaction.response.send_message("❌ OWNER ONLY", ephemeral=True)
        list_str = "\n".join([f"• {g.name} ({g.member_count})" for g in self.bot.guilds])
        await interaction.response.send_message(embed=discord.Embed(title="🌍 Server List", description=list_str))

    @app_commands.command(name="announce", description="Broadcast a message to all servers")
    async def announce(self, interaction: discord.Interaction, message: str):
        if not self.is_owner(interaction):
            return await interaction.response.send_message("❌ OWNER ONLY", ephemeral=True)
            
        await interaction.response.send_message(f"🚀 Starting broadcast to {len(self.bot.guilds)} servers...")
        
        success = 0
        failed = 0
        
        embed = discord.Embed(
            title="📢 Haze Bot Global Announcement",
            description=message,
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text="Official Haze Bot Update")
        
        for guild in self.bot.guilds:
            channel = None
            # 1. Look for system channel
            if guild.system_channel:
                channel = guild.system_channel
            # 2. Look for "announcements" or "general"
            if not channel:
                channel = discord.utils.get(guild.text_channels, name="announcements")
            if not channel:
                channel = discord.utils.get(guild.text_channels, name="general")
            # 3. Just pick the first text channel the bot can send to
            if not channel:
                for c in guild.text_channels:
                    if c.permissions_for(guild.me).send_messages:
                        channel = c
                        break
            
            try:
                if channel:
                    await channel.send(embed=embed)
                    success += 1
                else:
                    failed += 1
            except Exception:
                failed += 1
                
        await interaction.followup.send(f"✅ Broadcast complete!\nSuccess: {success}\nFailed: {failed}")

    @commands.command(name="sync")
    async def sync(self, ctx, spec: str = None):
        if ctx.author.id != self.owner_id: return
        
        if spec == "guild":
            # 1. Clear current guild state
            self.bot.tree.clear_commands(guild=ctx.guild)
            # 2. Mirror global commands to this guild
            self.bot.tree.copy_global_to(guild=ctx.guild)
            # 3. Upload to Discord
            synced = await self.bot.tree.sync(guild=ctx.guild)
            
            await ctx.send(
                f"✅ **Neural Link Established.**\n"
                f"◈ Synced: `{len(synced)}` commands to this sector.\n"
                f"◈ Mode: `INSTANT_GUILD_SYNC`"
            )
        else:
            # Global Sync
            synced = await self.bot.tree.sync()
            cogs = [c.replace('cogs.', '') for c in self.bot.extensions.keys()]
            await ctx.send(
                f"🌍 **Global Sync Initiated.**\n"
                f"◈ Commands: `{len(synced)}` registered in Singularity.\n"
                f"◈ Active Cogs: `{', '.join(cogs)}`"
            )

    @app_commands.command(name="admin_force_sync", description="OWNER: Force-rebuild the entire neural tree")
    async def force_sync(self, interaction: discord.Interaction):
        if not self.is_owner(interaction): return await interaction.response.send_message("❌", ephemeral=True)
        
        await interaction.response.defer(ephemeral=True)
        
        # 1. Clear everything
        self.bot.tree.clear_commands(guild=None)
        for guild in self.bot.guilds:
            self.bot.tree.clear_commands(guild=guild)
            
        # 2. Re-register all Cog commands
        for cog in self.bot.cogs.values():
            for cmd in cog.get_app_commands():
                self.bot.tree.add_command(cmd)
        
        # 3. Mirror to current guild
        self.bot.tree.copy_global_to(guild=interaction.guild)
        synced = await self.bot.tree.sync(guild=interaction.guild)
        
        await interaction.followup.send(f"✅ **Neural Tree Reconstructed.** `{len(synced)}` commands synchronized to this sector.")

    @app_commands.command(name="admin_inspect_tree", description="OWNER: Inspect the neural command tree")
    async def inspect_tree(self, interaction: discord.Interaction):
        if not self.is_owner(interaction): return await interaction.response.send_message("❌", ephemeral=True)
        
        global_cmds = [c.name for c in self.bot.tree.get_commands()]
        
        # Check all guilds
        guild_cmds = []
        for guild in self.bot.guilds:
            cmds = [c.name for c in self.bot.tree.get_commands(guild=guild)]
            if cmds:
                guild_cmds.append(f"• {guild.name}: `{', '.join(cmds)}`")
                
        embed = discord.Embed(title="🛰️ Tree Diagnostics", color=0x3498db)
        embed.add_field(name="Global Commands", value=f"`{', '.join(global_cmds)}`" if global_cmds else "None", inline=False)
        
        if guild_cmds:
            embed.add_field(name="Guild-Specific", value="\n".join(guild_cmds), inline=False)
            
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="admin_reload", description="OWNER: Live-reload a system cog")
    @app_commands.describe(cog="The cog filename (e.g. economy)")
    async def reload_cog(self, interaction: discord.Interaction, cog: str):
        if not self.is_owner(interaction): return await interaction.response.send_message("❌", ephemeral=True)
        
        try:
            await self.bot.reload_extension(f"cogs.{cog}")
            await interaction.response.send_message(f"✅ **System Cog `{cog}` re-synchronized.**", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ **Sync Failed:** `{e}`", ephemeral=True)

    @app_commands.command(name="admin_shutdown", description="OWNER: Terminate the singularity")
    async def shutdown(self, interaction: discord.Interaction):
        if not self.is_owner(interaction): return await interaction.response.send_message("❌", ephemeral=True)
        
        await interaction.response.send_message("⚠️ **Singularity Terminating...**", ephemeral=True)
        await self.bot.close()

    @app_commands.command(name="admin_db_stats", description="OWNER: View database neural density")
    async def db_stats(self, interaction: discord.Interaction):
        if not self.is_owner(interaction): return await interaction.response.send_message("❌", ephemeral=True)
        
        user_count = db.users.count_documents({})
        guild_count = db.db.guilds.count_documents({})
        
        embed = discord.Embed(title="🧠 Neural Database Stats", color=0x3498db)
        embed.add_field(name="Subjects", value=f"`{user_count}`", inline=True)
        embed.add_field(name="Sectors", value=f"`{guild_count}`", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="admin_eval", description="OWNER: Execute raw neural logic")
    @app_commands.describe(code="Python logic to execute")
    async def eval_code(self, interaction: discord.Interaction, code: str):
        if not self.is_owner(interaction): return await interaction.response.send_message("❌", ephemeral=True)
        
        await interaction.response.defer(ephemeral=True)
        
        # Security: Basic sanitization (still powerful, hence owner-only)
        try:
            # Setup environment
            env = {
                'bot': self.bot,
                'interaction': interaction,
                'db': db,
                'discord': discord,
                'os': os
            }
            
            # Use eval or exec? exec is better for blocks
            # Redirect stdout to capture print statements
            import sys
            from io import StringIO
            
            old_stdout = sys.stdout
            redirected_output = sys.stdout = StringIO()
            
            try:
                exec(f"async def _ex():\n" + "".join(f"    {l}\n" for l in code.split("\n")), env)
                await env['_ex']()
                result = redirected_output.getvalue()
            finally:
                sys.stdout = old_stdout
            
            if not result: result = "Command executed with no output."
            
            # Chunk result if too long
            if len(result) > 1900: result = result[:1900] + "..."
            await interaction.followup.send(f"```py\n{result}\n```", ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ **Execution Error:**\n```py\n{e}\n```", ephemeral=True)

    @app_commands.command(name="establish_sanctum", description="OWNER: Establish the Architect's Private Sanctum")
    async def establish_sanctum(self, interaction: discord.Interaction):
        if not self.is_owner(interaction):
            return await interaction.response.send_message("❌", ephemeral=True)

        if not interaction.guild.me.guild_permissions.manage_roles:
            return await interaction.response.send_message("❌ **Neural Link Failed.** Missing 'Manage Roles' permission.", ephemeral=True)

        # Stylized Name for the coding space
        vc_name = "󠇲 ┇ ◌ sovereign sanctum"
        guild = interaction.guild

        await interaction.response.defer(ephemeral=True)

        try:
            # Look for existing sanctum or create new
            channel = discord.utils.get(guild.voice_channels, name=vc_name)
            if not channel:
                # Find the Architect/Staff category if it exists
                category = discord.utils.get(guild.categories, name="◈ [ SOVEREIGN CONTROL ]")
                channel = await guild.create_voice_channel(vc_name, category=category)
                await interaction.followup.send(f"✨ **Singularity Expanded.** Sanctum established: `{vc_name}`")
            else:
                await interaction.followup.send(f"🛰️ **Neural Link Stable.** Found existing Sanctum.")

            # Set High-Prestige Overrides
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(connect=False, view_channel=True),
                guild.me: discord.PermissionOverwrite(connect=True, move_members=True, manage_channels=True)
            }
            
            owner = guild.get_member(self.owner_id)
            if owner:
                overwrites[owner] = discord.PermissionOverwrite(
                    connect=True, 
                    move_members=True, 
                    manage_channels=True,
                    priority_speaker=True,
                    mute_members=True,
                    deafen_members=True
                )
            
            await channel.edit(overwrites=overwrites)
            await interaction.followup.send(f"🔒 **Sanctum Protocols Active.** Only the Architect may anchor this frequency.")

        except Exception as e:
            await interaction.followup.send(f"❌ **System Error:** {e}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        vc_name = "󠇲 ┇ ◌ sovereign sanctum"
        
        # 1. Protection: If someone is moved OUT of the private VC (and it wasn't the owner leaving)
        if before.channel and before.channel.name == vc_name:
            # If they were moved to a different channel (not just disconnected)
            if after.channel and after.channel != before.channel:
                # If the person moved isn't the bot owner or server owner
                if member.id != self.owner_id and member.id != member.guild.owner_id:
                    try:
                        await member.move_to(before.channel, reason="Auto-revert: Protective VC lock")
                        print(f"🛡️ [Guard] Reverted move for {member.name} back to coding space.")
                    except: pass

        # 2. Restriction: Only allow dragging into the VC if the Owner is in it
        if after.channel and after.channel.name == vc_name:
            # If they just joined/were moved in
            if before.channel != after.channel:
                owner_in_vc = any(m.id == self.owner_id for m in after.channel.members)
                
                # If owner IS NOT in the VC, only the bot owner or server owner can stay
                if not owner_in_vc:
                    if member.id != self.owner_id and member.id != member.guild.owner_id:
                        try:
                            # Move them back to where they came from or disconnect
                            await member.move_to(before.channel if before.channel else None, reason="Owner not present in private VC")
                            print(f"🚫 [Guard] Booted {member.name} from coding space (Owner not present).")
                        except: pass


async def setup(bot):
    await bot.add_cog(Owner(bot))
