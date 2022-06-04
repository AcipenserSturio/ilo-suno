from discord.ext import tasks, commands
import xml.etree.ElementTree as ET
import urllib.request
from datetime import datetime as dt

SCHEDULE_LINK = "https://events.opensuse.org/conferences/oSC22/schedule.xml"
# SCHEDULE_LINK = "https://suno.pona.la/conferences/2022/schedule.xml"

def schedule_tree(link):
    return ET.fromstring(urllib.request.urlopen(link).read().decode('utf8'))

class CogSchedule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.printer.start()
        self.tree = schedule_tree(SCHEDULE_LINK)
        self.events = {event.find('date').text: event for event in self.tree.findall('.//event')}

    def cog_unload(self):
        self.printer.cancel()

    @tasks.loop(seconds=5.0)
    async def printer(self):
        self.get_current_event(self)

    def get_current_event(self):
        for timestamp, event in self.events.items():
            print(k, v)
