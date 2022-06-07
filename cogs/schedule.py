from datetime import datetime as dt
from datetime import timedelta
import urllib.request
import xml.etree.ElementTree as ET

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.commands import slash_command
from discord.ext import commands
from discord import Colour, Embed

SCHEDULE_LINK = "https://events.opensuse.org/conferences/oSC22/schedule.xml"
# SCHEDULE_LINK = "https://suno.pona.la/conferences/2022/schedule.xml"
ANNOUNCEMENT_CHANNEL_ID = 978564101364133898

TIME_TRAVEL = timedelta(days=3, hours=7, minutes=12)

def xml_from_https(link):
    return ET.fromstring(urllib.request.urlopen(link).read().decode("utf8"))

def schedule_from_xml(xml):
    schedule = []
    for room_xml in xml.findall("./day/room"):
        room = []
        for event_xml in room_xml.findall("./event"):
            room.append(Event(event_xml, room))
        # This step has to happen after room is filled
        for event in room:
            event.initialize_adjacent_events()
        schedule.extend(room)
    return schedule

class CogSchedule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.announce_channels = []

        self.schedule = schedule_from_xml(xml_from_https(SCHEDULE_LINK))
        #self.print_schedule()

        self.scheduler = AsyncIOScheduler()
        self.schedule_events()
        self.scheduler.start()

    def get_announcement_channel(self):
        return self.bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)


    def schedule_events(self):
        for event in self.schedule:
            print(event.start+TIME_TRAVEL)
            self.scheduler.add_job(self.announce_event_start,
                                   "date", run_date=event.start+TIME_TRAVEL,
                                   args=[event])
    def print_schedule(self):
        for event in self.schedule:
            event.announce()

    async def announce_event_start(self, event):
        await self.get_announcement_channel().send(embed=event.announce_embed())


def duration_timedelta(timestamp):
    # Builds timedelta object from duration timestamp.
    t = dt.strptime(timestamp, "%H:%M")
    return timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)


def now():
    # Helper function for testing purposes.
    # Allows the "now" to travel in time.
    return dt.now() - TIME_TRAVEL


class Event():
    def __init__(self, xml, room_events):
        self.xml = xml
        self.room_events = room_events
        self.room = xml.find("room").text
        self.title = xml.find("title").text
        self.start_timestamp = xml.find("date").text[:-1]
        self.start = dt.fromisoformat(self.start_timestamp)
        self.duration = duration_timedelta(xml.find("duration").text)

    def initialize_adjacent_events(self):
        self.next = self.get_next_event()
        self.prev = self.get_previous_event()

    def __repr__(self):
        return f"Event '{self.title}' starting at {self.start_timestamp}"

    def get_next_event(self):
        if self.room_events.index(self) == len(self.room_events) - 1:
            return None
        return self.room_events[self.room_events.index(self) + 1]

    def get_previous_event(self):
        if self.room_events.index(self) == 0:
            return None
        return self.room_events[self.room_events.index(self) - 1]

    def status(self):
        # negative: has not yet happened
        # positive: has happened
        time_to_event_start = now() - self.start
        time_to_event_end = time_to_event_start - self.duration

        if time_to_event_start.total_seconds() < 0:
            return "upcoming"
        if time_to_event_end.total_seconds() < 0:
            return "ongoing"
        return "finished"

    def announce(self):
        return f"""
{self.title}
room: {self.room}
status: {self.status()}
starts: {self.start}
previous: {self.prev}
next: {self.next}
=================================================================
"""
    def announce_embed(self):
        embed = Embed()
        embed.colour = Colour.from_rgb(255, 0, 0)
        embed.title = self.title
        embed.description = self.title
        embed.add_field(name="starts", value=self.start)
        embed.add_field(name="previous", value=self.prev)
        embed.add_field(name="next", value=self.next)
        return embed
