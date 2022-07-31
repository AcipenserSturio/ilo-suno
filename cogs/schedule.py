from datetime import datetime as dt
from datetime import timedelta
import urllib.request
import xml.etree.ElementTree as ET
import json

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.commands import slash_command
from discord.ext import commands
from discord import Colour, Embed

# SCHEDULE_LINK = "https://events.opensuse.org/conferences/oSC22/schedule.xml"
SCHEDULE_LINK = "https://suno.pona.la/conferences/2022/schedule.xml"
ANNOUNCEMENT_CHANNEL_ID = 873077312306966548
GRACE = 1800

# TIME_TRAVEL = timedelta(days=3, hours=7, minutes=30)
TIME_TRAVEL = 0
ROOM_IDS = {"wordcloud room": 1003319404009889942,
            "🔊 supa suli": 976133236533112862,
            "o toki e sitelen, o pali e sitelen": 1003322452207743068,
            "chill space": 1003318557804875856}

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
        with open("events.json", "w") as f:
            f.write(json.dumps([x.to_json() for x in self.schedule]))
        self.scheduler = AsyncIOScheduler()
        self.schedule_events()

    def get_announcement_channel(self):
        return self.bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)


    def schedule_events(self):
        for event in self.schedule:
            print(event.start+TIME_TRAVEL)
            self.scheduler.add_job(self.announce,
                                   "date", run_date=event.start+TIME_TRAVEL,
                                   args=[event, "start"],
                                   misfire_grace_time=GRACE)
            print(len(self.scheduler.get_jobs()))
            self.scheduler.add_job(self.announce,
                                   "date", run_date=event.end+TIME_TRAVEL,
                                   args=[event, "end"],
                                   misfire_grace_time=GRACE)
            print(len(self.scheduler.get_jobs()))

    async def announce(self, event, mode):
        embed = self.embed(event, mode)
        await self.get_announcement_channel().send(embed=embed)

    def embed(self, event, mode):
        embed = Embed()
        embed.colour = Colour.from_rgb(255, 0, 0) if mode == "start" else Colour.from_rgb(0, 0, 255)
        embed.title = event.title
        embed.description = event.description
        embed.set_author(name=", ".join(event.authors))
        embed.add_field(name="starts", value=discord_timestamp(event.start))
        embed.add_field(name="ends", value=discord_timestamp(event.end))
        embed.add_field(name="previous", value=event.prev, inline=False)
        embed.add_field(name="next", value=event.next, inline=False)
        embed.add_field(name="room", value=f"<#{event.room_id}>", inline=False)
        return embed


def duration_timedelta(timestamp):
    # Builds timedelta object from duration timestamp.
    t = dt.strptime(timestamp, "%H:%M")
    return timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)


def now():
    # Helper function for testing purposes.
    # Allows the "now" to travel in time.
    return dt.now() - TIME_TRAVEL


def discord_timestamp(datetime):
    return f"<t:{int(datetime.timestamp())}:t>"

class Event():
    def __init__(self, xml, room_events):
        self.xml = xml
        self.room_events = room_events

        self.title = xml.find("title").text
        self.description = xml.find("description").text
        self.room = xml.find("room").text
        self.authors = [person.text for person in xml.find("persons").findall("person")]

        self.room_id = ROOM_IDS[self.room]

        self._start_timestamp = xml.find("date").text[:-1]
        self.start = dt.fromisoformat(self._start_timestamp)
        self.duration = duration_timedelta(xml.find("duration").text)
        self.end = self.start + self.duration

    def initialize_adjacent_events(self):
        self.next = self.get_next_event()
        self.prev = self.get_previous_event()

    def __repr__(self):
        return f"Event '{self.title}' starting at {self._start_timestamp}"

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

    def to_json(self):
        return { "title": self.title, "description": self.description, "authors": self.authors, "start": self._start_timestamp }
