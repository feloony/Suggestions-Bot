import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from database.db import Database
from utils.helpers import check_rate_limit, get_rate_limit_remaining, sanitize_input
from config import Config

class Suggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @app_commands.command(name="suggest", description="Add a suggestion")
    async def suggest(self, interaction: discord.Interaction, suggestion: str, category: str = "General", anonymous: bool = False):
        try:
            # Defer the response immediately
            await interaction.response.defer(ephemeral=True)
            
            # Input validation
            if len(suggestion) > Config.MAX_SUGGESTION_LENGTH:
                await interaction.followup.send(
                    f"Suggestion too long! Maximum length is {Config.MAX_SUGGESTION_LENGTH} characters.", 
                    ephemeral=True
                )
                return

            # Rate limit check
            is_allowed, time_remaining = check_rate_limit(interaction.user.id)
            if not is_allowed:
                time_str = format_time_remaining(time_remaining)
                await interaction.followup.send(
                    f"You're suggesting too quickly! Please wait {time_str} before making another suggestion.\n"
                    f"Maximum suggestions per {Config.RATE_LIMIT_DURATION} seconds: {Config.MAX_SUGGESTIONS_PER_USER}", 
                    ephemeral=True
                )
                return

            # Get suggestion channel from database
            channel_id = self.db.get_suggestion_channel(interaction.guild_id)
            if not channel_id:
                await interaction.followup.send("No suggestions channel has been set!", ephemeral=True)
                return
            
            suggest_channel = self.bot.get_channel(channel_id)
            if not suggest_channel:
                await interaction.followup.send("Suggestion channel not found.", ephemeral=True)
                return

            # Create embed
            embed = discord.Embed(
                title="New Suggestion",
                description=suggestion,
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            author_name = "Anonymous" if anonymous else interaction.user.display_name
            author_avatar = None if anonymous else interaction.user.avatar.url
            embed.set_author(name=author_name, icon_url=author_avatar)
            embed.add_field(name="Category", value=category, inline=True)
            embed.add_field(name="Status", value="Pending", inline=True)
            embed.set_footer(text=f"Suggestion from {interaction.user.id}")

            # Send embed and create thread
            message = await suggest_channel.send(embed=embed)
            await message.add_reaction('👍')
            await message.add_reaction('👎')
            thread = await message.create_thread(name=f"Suggestion Discussion")
            await thread.send("Discussion thread for this suggestion")

            # Store in database
            self.db.add_suggestion(message.id, interaction.user.id, suggestion, category, anonymous)
            
            await interaction.followup.send(
                f"Thank you for your suggestion! Suggestion ID: {message.id}", 
                ephemeral=True
            )

        except Exception as e:
            print(f"Error in suggest command: {e}")
            try:
                await interaction.followup.send(
                    "An error occurred while processing your suggestion.", 
                    ephemeral=True
                )
            except:
                pass

    @app_commands.command(name="stats", description="View suggestion statistics")
    async def stats(self, interaction: discord.Interaction):
        stats = self.db.get_suggestion_stats()
        await interaction.response.send_message(
            f"📊 **Suggestion Statistics**\n"
            f"Total Suggestions: {stats['total']}\n"
            f"Accepted: {stats['accepted']}\n"
            f"Pending: {stats['pending']}\n"
            f"Rejected: {stats['rejected']}", 
            ephemeral=True
        )

    @app_commands.command(name="search", description="Search suggestions")
    async def search(self, interaction: discord.Interaction, query: str):
        results = self.db.search_suggestions(query)
        if not results:
            await interaction.response.send_message("No suggestions found matching your query.", ephemeral=True)
            return
        
        response = "**Search Results:**\n"
        for result in results[:5]:
            response += f"ID: {result[0]} | {result[1][:50]}... | Status: {result[2]} | Category: {result[3]}\n"
        
        await interaction.response.send_message(response, ephemeral=True)

    @app_commands.command(name="mysuggestions", description="View your suggestion history")
    async def mysuggestions(self, interaction: discord.Interaction):
        suggestions = self.db.get_user_suggestions(interaction.user.id)
        if not suggestions:
            await interaction.response.send_message("You haven't made any suggestions yet!", ephemeral=True)
            return
        
        response = "**Your Recent Suggestions:**\n"
        for sugg in suggestions:
            response += f"ID: {sugg[0]} | {sugg[1][:50]}... | Status: {sugg[2]} | Category: {sugg[3]}\n"
        
        await interaction.response.send_message(response, ephemeral=True)

    @app_commands.command(name="edit", description="Edit your suggestion")
    async def edit(self, interaction: discord.Interaction, message_id: str, new_text: str):
        try:
            msg_id = int(message_id)
            suggestion = self.db.get_suggestion(msg_id)
            
            if not suggestion or suggestion['user_id'] != interaction.user.id:
                await interaction.response.send_message("You can't edit this suggestion", ephemeral=True)
                return

            if len(new_text) > Config.MAX_SUGGESTION_LENGTH:
                await interaction.response.send_message(
                    f"Suggestion too long! Maximum length is {Config.MAX_SUGGESTION_LENGTH} characters.",
                    ephemeral=True
                )
                return

            channel_id = self.db.get_suggestion_channel(interaction.guild_id)
            channel = self.bot.get_channel(channel_id)
            if not channel:
                await interaction.response.send_message("Suggestion channel not found", ephemeral=True)
                return

            try:
                message = await channel.fetch_message(msg_id)
                embed = message.embeds[0]
                embed.description = new_text
                
                await message.edit(embed=embed)
                self.db.update_suggestion_text(msg_id, new_text)
                await interaction.response.send_message("Suggestion updated successfully", ephemeral=True)

            except discord.NotFound:
                await interaction.response.send_message("Could not find the suggestion message", ephemeral=True)

        except ValueError:
            await interaction.response.send_message("Invalid message ID", ephemeral=True)

    @app_commands.command(name="categories", description="List available suggestion categories")
    async def categories(self, interaction: discord.Interaction):
        categories = self.db.get_categories()
        if categories:
            await interaction.response.send_message(
                f"Available categories:\n{', '.join(categories)}", 
                ephemeral=True
            )
        else:
            await interaction.response.send_message("No categories found", ephemeral=True)

    @app_commands.command(name="top", description="View top suggestions")
    async def top(self, interaction: discord.Interaction, timeframe: str = "all"):
        suggestions = self.db.get_top_suggestions(timeframe)
        if not suggestions:
            await interaction.response.send_message("No suggestions found", ephemeral=True)
            return

        embed = discord.Embed(title=f"Top Suggestions ({timeframe})", color=discord.Color.blue())
        for i, sugg in enumerate(suggestions[:10], 1):
            embed.add_field(
                name=f"{i}. ID: {sugg['message_id']} (👍 {sugg['upvotes']} | 👎 {sugg['downvotes']})",
                value=f"{sugg['suggestion'][:100]}...",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    # Reaction handling
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        try:
            if payload.user_id == self.bot.user.id:
                return

            if str(payload.emoji) in ['👍', '👎']:
                self.db.add_vote(payload.message_id, payload.user_id, str(payload.emoji))
        except Exception as e:
            print(f"Error handling reaction: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        try:
            if str(payload.emoji) in ['👍', '👎']:
                self.db.remove_vote(payload.message_id, payload.user_id)
        except Exception as e:
            print(f"Error handling reaction removal: {e}")

async def setup(bot):
    await bot.add_cog(Suggestions(bot))
