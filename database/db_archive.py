from datetime import datetime, timedelta
from .db_globals import *
from pytz import timezone


def get_next_archive_date() -> datetime:
    collection = db.next_archive_date
    data = collection.find_one({"_id": DATE_ID}, {"_id": 0})
    if data is None:
        raise Exception("Couldn't find document")
    eastern = timezone("US/Eastern")
    next_archive_date = eastern.localize(
        datetime(data["year"], data["month"], data["day"],
                 data["hour"], data["minute"], data["second"])
    )
    return next_archive_date


def get_archived_name(channel_name: str) -> str:
    date = get_next_archive_date()
    month = str(date.month)
    day = str(date.day)
    year = str(date.year)
    return f"{channel_name}-{month}-{day}-{year[len(year) - 2:]}"


def update_next_archive_date(archive_freq: timedelta) -> None:
    old_date = get_next_archive_date()
    new_date: datetime = old_date + archive_freq
    new_date_fields = {
        "year": new_date.year,
        "month": new_date.month,
        "day": new_date.day,
        "hour": new_date.hour,
        "minute": new_date.minute,
        "second": new_date.second
    }
    collection = db.next_archive_date
    collection.update_one(
        {"_id": DATE_ID}, {"$set": new_date_fields}, upsert=True)
