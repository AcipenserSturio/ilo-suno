from discord.ext import commands
# from discord import Intents

import os
from dotenv import load_dotenv
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

from cogs.schedule import CogSchedule

bot = commands.Bot(command_prefix="/",
                   # intents=Intents.all(),
                   )

@bot.event
async def on_ready():
    for index, guild in enumerate(bot.guilds):
        print("{}) {}".format(index+1, guild.name))

if __name__ == "__main__":
    bot.add_cog(CogSchedule(bot))
    bot.run(DISCORD_TOKEN, reconnect=True)
