from discord.ext import commands
import xml.etree.ElementTree as ET
import urllib.request
from datetime import datetime as dt
from datetime import timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

SCHEDULE_LINK = "https://events.opensuse.org/conferences/oSC22/schedule.xml"
# SCHEDULE_LINK = "https://suno.pona.la/conferences/2022/schedule.xml"

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
        self.schedule = schedule_from_xml(xml_from_https(SCHEDULE_LINK))
        self.scheduler = AsyncIOScheduler()
        self.schedule_events()
        self.print_schedule()

    def schedule_events(self):
        for event in self.schedule:
            self.scheduler.add_job(self.announce_event_start,
                                   "date", run_date=event.start,
                                   args=[event])
    def print_schedule(self):
        for event in self.schedule:
            event.announce()

    def announce_event_start(self, event):
        event.announce()


def duration_timedelta(timestamp):
    # Builds timedelta object from duration timestamp.
    t = dt.strptime(timestamp, "%H:%M")
    return timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)


def now():
    # Helper function for testing purposes.
    # Allows the "now" to travel in time.
    return dt.now() - timedelta(days=2, hours=6)


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
        print(self.title)
        print(f"room: {self.room}")
        print(f"status: {self.status()}")
        print(f"starts: {self.start}")
        print(f"previous: {self.prev}")
        print(f"next: {self.next}")
        print("="*60)
