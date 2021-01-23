import asyncio
import time
import discord
from discord.ext import commands
from services import file_manager
from services import rcon_manager
from services import permission_manager
import main

config = file_manager.load_config()
client = commands.Bot(command_prefix = config["discord_bot"]["prefix"])


@client.event
async def on_ready():
    print("ready")


@client.command()
async def triberank(ctx):

    steam_id = main.get_steam_id(ctx.message.author.id)
    if steam_id is None:
        await ctx.send("You need to be verified to use this command")
        return

    result = main.get_max_tribe_size(steam_id)
    if result is None:
        await ctx.send("Could not find your tribe")

    embed = discord.Embed(
        title="📈 │**TRIBE RANKS**",
        description=f"Your current tribe size is {result} across all maps.",
        color=discord.Color.dark_red()
    )

    await ctx.send(embed=embed)


client.run(config["discord_bot"]["token"])


