import discord
from discord import app_commands
from discord.ext import commands
from database.db import Database
from config import Config
import logging
from typing import Optional
from datetime import datetime, timedelta

class ConfirmView(discord.ui.View):
    def __init__(self, timeout=180):
        super().__init__(timeout=timeout)
        self.value = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()
        await interaction.response.defer()

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    def is_admin(interaction: discord.Interaction) -> bool:
        return interaction.user.guild_permissions.administrator

    @app_commands.command(name="setchannel", description="Set the suggestions channel")
    @app_commands.check(is_admin)
    async def setchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if self.db.set_suggestion_channel(interaction.guild_id, channel.id):
            await interaction.response.send_message(f"Suggestion channel set to {channel.mention}", ephemeral=True)
        else:
            await interaction.response.send_message("Failed to set suggestion channel", ephemeral=True)

    @app_commands.command(name="updatestatus", description="Update suggestion status")
    @app_commands.choices(status=[
        app_commands.Choice(name=status, value=status) 
        for status in Config.VALID_STATUSES
    ])
    @app_commands.check(is_admin)
    async def updatestatus(self, interaction: discord.Interaction, message_id: str, status: str, reason: str = None):
        try:
            await interaction.response.defer(ephemeral=True)
            msg_id = int(message_id)
            suggestion = self.db.get_suggestion(msg_id)
            
            if not suggestion:
                await interaction.followup.send("Suggestion not found", ephemeral=True)
                return

            channel = await self.get_suggestion_channel(interaction.guild_id)
            if not channel:
                return

            message = await channel.fetch_message(msg_id)
            embed = message.embeds[0]
            
            # Update embed
            embed.clear_field(1)
            embed.add_field(name="Status", value=status, inline=True)
            if reason:
                embed.add_field(name="Status Reason", value=reason, inline=False)
            
            # Update color based on status
            embed.color = {
                "Accepted": discord.Color.green(),
                "Rejected": discord.Color.red(),
                "Under Review": discord.Color.yellow(),
                "Pending": discord.Color.blue()
            }.get(status, discord.Color.blue())

            await message.edit(embed=embed)
            self.db.update_suggestion_status(msg_id, status, reason)
            
            # Notify the suggestion author
            if not suggestion['is_anonymous']:
                try:
                    user = await self.bot.fetch_user(suggestion['user_id'])
                    await user.send(f"Your suggestion (ID: {msg_id}) has been {status.lower()}.\n" +
                                  (f"Reason: {reason}" if reason else ""))
                except:
                    pass  # Failed to DM user

            await interaction.followup.send(f"Updated suggestion {msg_id} status to {status}", ephemeral=True)

        except ValueError:
            await interaction.followup.send("Invalid message ID", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Error: {str(e)}", ephemeral=True)

    @app_commands.command(name="addcategory", description="Add a new suggestion category")
    @app_commands.check(is_admin)
    async def addcategory(self, interaction: discord.Interaction, category: str):
        if self.db.add_category(category):
            await interaction.response.send_message(f"Added new category: {category}", ephemeral=True)
        else:
            await interaction.response.send_message("Failed to add category", ephemeral=True)

    @app_commands.command(name="removecategory", description="Remove a suggestion category")
    @app_commands.check(is_admin)
    async def removecategory(self, interaction: discord.Interaction, category: str):
        if self.db.remove_category(category):
            await interaction.response.send_message(f"Removed category: {category}", ephemeral=True)
        else:
            await interaction.response.send_message("Failed to remove category", ephemeral=True)

    @app_commands.command(name="massstatus", description="Update status of multiple suggestions")
    @app_commands.check(is_admin)
    async def massstatus(self, interaction: discord.Interaction, status: str, category: str = None, days: int = None):
        view = ConfirmView()
        count = self.db.count_suggestions_for_mass_update(category, days)
        
        await interaction.response.send_message(
            f"Are you sure you want to update {count} suggestions to {status}?" +
            (f"\nCategory: {category}" if category else "") +
            (f"\nLast {days} days" if days else ""),
            view=view,
            ephemeral=True
        )
        
        await view.wait()
        if view.value:
            updated = self.db.mass_update_status(status, category, days)
            await interaction.edit_original_message(
                content=f"Updated {updated} suggestions to {status}",
                view=None
            )
        else:
            await interaction.edit_original_message(
                content="Operation cancelled",
                view=None
            )

    @app_commands.command(name="purge", description="Purge old suggestions")
    @app_commands.check(is_admin)
    async def purge(self, interaction: discord.Interaction, days: int, status: str = None):
        view = ConfirmView()
        await interaction.response.send_message(
            f"Are you sure you want to purge suggestions older than {days} days" +
            (f" with status {status}" if status else ""),
            view=view,
            ephemeral=True
        )
        
        await view.wait()
        if view.value:
            count = self.db.purge_old_suggestions(days, status)
            await interaction.edit_original_message(
                content=f"Purged {count} suggestions",
                view=None
            )
        else:
            await interaction.edit_original_message(
                content="Operation cancelled",
                view=None
            )

    @app_commands.command(name="exportdata", description="Export suggestions data")
    @app_commands.check(is_admin)
    async def exportdata(self, interaction: discord.Interaction, days: int = None):
        await interaction.response.defer(ephemeral=True)
        
        data = self.db.export_suggestions(days)
        if not data:
            await interaction.followup.send("No data to export", ephemeral=True)
            return
            
        # Create CSV file
        import io
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'User ID', 'Suggestion', 'Status', 'Category', 'Created At', 'Upvotes', 'Downvotes'])
        writer.writerows(data)
        
        # Convert to bytes and send as file
        buffer = io.BytesIO(output.getvalue().encode())
        await interaction.followup.send(
            "Here's your exported data:",
            file=discord.File(buffer, f"suggestions_export_{datetime.now().strftime('%Y%m%d')}.csv"),
            ephemeral=True
        )

    async def get_suggestion_channel(self, guild_id: int) -> Optional[discord.TextChannel]:
        channel_id = self.db.get_suggestion_channel(guild_id)
        if not channel_id:
            return None
        return self.bot.get_channel(channel_id)

async def setup(bot):
    await bot.add_cog(Admin(bot))
