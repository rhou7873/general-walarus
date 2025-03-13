from discord import Guild, User
import database as db
from apscheduler.job import Job
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import random


class WSESession:
    """ Class that encapsulates a details about a Walarus Stock Exchange session """

    def __init__(self, guild: Guild, user_id: int, cron_exp: str) -> None:
        self.guild: Guild = guild
        """ Server that the session is running in """
        self.user_id = user_id
        """ User ID of the user we're tracking """
        cron_trigger = CronTrigger.from_crontab(cron_exp)
        scheduler = BackgroundScheduler()
        self.job: Job = scheduler.add_job(
            self.__get_new_wse_price, cron_trigger, args=[True])
        """ APScheduler job used for fetching next price change timestamp """
        scheduler.start()

    def __str__(self) -> str:
        curr_price = db.get_current_wse_price(self.guild)
        return (f"'{self.guild.name}' ({self.user_id}): ${curr_price} (next price change: {self.job.next_run_time})")

    def __get_new_wse_price(self, write: bool = False) -> float:
        old_price = db.get_current_wse_price(self.guild)
        rate = random.randint(-200, 700) / 10000
        delta = old_price * rate

        if abs(delta) < 0.01:
            return old_price

        new_price = old_price + delta
        if write:
            db.set_current_wse_price(self.guild, new_price)
        return new_price
