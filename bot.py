import discord
from discord.ext import commands
from bot_setup import BOT_TOKEN
import logging
import asyncio
from database import init_database
from setup_exp_tables import setup_exp_tables
from setup_statpoint_table import setup_statpoint_table
from setup_combat_tables import setup_combat_tables
from monster import add_monsters, add_monster_skills
from asyncio import Lock


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=["@", "/"], intents=intents)

db_lock = Lock()  # Global lock for DB access

# Update get_db_connection if not in database.py
def get_db_connection():
    return sqlite3.connect("ragnarok.db", timeout=10)

async def load_extensions():
    extensions = ["battle", "players", "admin", "trade", "hunt"]
    for ext in extensions:
        try:
            await bot.load_extension(ext)
            logger.info(f"Loaded extension: {ext}")
        except Exception as e:
            logger.error(f"Failed to load extension {ext}: {e}")
            if ext in ["hunt", "battle"]:  # Critical extensions
                raise

restricted_during_trade = {"items", "battle", "equip", "storage", "bank", "mob"}
restricted_during_battle = {"items", "battle", "equip", "storage", "bank", "mob", "trade"}

@bot.before_invoke
async def check_trade_status(ctx):
    trade_cog = bot.get_cog("TradeCog")
    if not trade_cog:
        logger.warning("TradeCog not loaded; trade restrictions bypassed.")
    if trade_cog and ctx.command.name in restricted_during_trade:
        for trade in trade_cog.active_trades.values():
            if trade["initiator"]["user_id"] == str(ctx.author.id) or trade["target"]["user_id"] == str(ctx.author.id):
                await ctx.send("**You’re currently in a trade!** Commands like `@items`, `@battle`, etc., are disabled until the trade is completed or cancelled.")
                raise commands.CommandError("User is in a trade")

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user}")

async def setup_hook():
    await load_extensions()

bot.setup_hook = setup_hook

if __name__ == "__main__":
    async def main():
        logger.info("Initializing database...")
        init_database()
        setup_exp_tables()
        setup_statpoint_table()
        setup_combat_tables()
        add_monsters()
        add_monster_skills()
        logger.info("Database initialization complete.")
        await bot.start(BOT_TOKEN)
    
    asyncio.run(main())