import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio
from config import Config

# Load environment variables
load_dotenv()

class SuggestionBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=Config.COMMAND_PREFIX, intents=intents)
        self.config = Config

    async def setup_hook(self):
        # Load cogs
        await self.load_extension("cogs.suggestions")
        await self.load_extension("cogs.admin")

    async def on_ready(self):
        await self.tree.sync()
        print(f'Logged in as {self.user}')

def main():
    bot = SuggestionBot()
    bot.run(Config.DISCORD_TOKEN)

if __name__ == "__main__":
    main()
