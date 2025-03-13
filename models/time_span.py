class TimeSpan():
    def __init__(self, seconds: int):
        self._days: int = seconds // 86400
        self._days_unit = self.days_unit()
        seconds -= self._days * 86400
        self._hours: int = seconds // 3600
        self._hours_unit = self.hours_unit()
        seconds -= self._hours * 3600
        self._minutes: int = seconds // 60
        self._minutes_unit = self.minutes_unit()
        seconds -= self._minutes * 60
        self._seconds: int = seconds
        self._seconds_unit = self.seconds_unit()

    # region Getters

    def days(self) -> int:
        return self._days

    def hours(self) -> int:
        return self._hours

    def minutes(self) -> int:
        return self._minutes

    def seconds(self) -> int:
        return self._seconds

    def days_unit(self) -> str:
        return "day" if self._days == 1 else "days"

    def hours_unit(self) -> str:
        return "hour" if self._hours == 1 else "hours"

    def minutes_unit(self) -> str:
        return "minute" if self._minutes == 1 else "minutes"

    def seconds_unit(self) -> str:
        return "second" if self._seconds == 1 else "seconds"

    # endregion

    # region Setters

    def set_days(self, days: int) -> None:
        self._days = days

    def set_hours(self, hours: int) -> None:
        self._hours = hours

    def set_minutes(self, minutes: int) -> None:
        self._minutes = minutes

    def set_seconds(self, seconds: int) -> None:
        self._seconds = seconds

    # endregion
