# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""ISO 8601 Duration representation.

Implements a duration class that supports the full ISO 8601 duration format:
``PnYnMnDTnHnMnS``

Unlike ``datetime.timedelta``, this class preserves calendar components (years, months)
which cannot be converted to a fixed number of days without a reference date.
"""

import datetime
import re
from typing import Optional, Union

_ISO_DURATION_RE = re.compile(
    r"^P"
    r"(?:(\d+)Y)?"
    r"(?:(\d+)M)?"
    r"(?:(\d+)W)?"
    r"(?:(\d+)D)?"
    r"(?:T"
    r"(?:(\d+)H)?"
    r"(?:(\d+)M)?"
    r"(?:(\d+(?:\.\d+)?)S)?"
    r")?$"
)


class Duration:
    """An ISO 8601 duration.

    Represents a duration as a combination of date components (years, months, weeks, days)
    and time components (hours, minutes, seconds). This preserves the semantics of
    calendar-based durations that cannot be represented as a fixed number of seconds.

    Parameters
    ----------
    years : int
        Number of years.
    months : int
        Number of months.
    weeks : int
        Number of weeks.
    days : int
        Number of days.
    hours : int
        Number of hours.
    minutes : int
        Number of minutes.
    seconds : float
        Number of seconds.
    """

    __slots__ = ("years", "months", "weeks", "days", "hours", "minutes", "seconds")

    def __init__(
        self,
        years: int = 0,
        months: int = 0,
        weeks: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: float = 0,
    ) -> None:
        self.years = years
        self.months = months
        self.weeks = weeks
        self.days = days
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds

    @classmethod
    def from_str(cls, s: str) -> "Duration":
        """Parse an ISO 8601 duration string.

        Parameters
        ----------
        s : str
            An ISO 8601 duration string, e.g. ``"P1Y2M3DT4H5M6S"``, ``"PT72H"``, ``"P1W"``.

        Returns
        -------
        Duration
            The parsed duration.

        Raises
        ------
        ValueError
            If the string is not a valid ISO 8601 duration.
        """
        m = _ISO_DURATION_RE.match(s)
        if not m:
            raise ValueError(f"Invalid ISO 8601 duration string: {s!r}")

        years, months, weeks, days, hours, minutes, seconds = m.groups()
        return cls(
            years=int(years) if years else 0,
            months=int(months) if months else 0,
            weeks=int(weeks) if weeks else 0,
            days=int(days) if days else 0,
            hours=int(hours) if hours else 0,
            minutes=int(minutes) if minutes else 0,
            seconds=float(seconds) if seconds else 0,
        )

    @classmethod
    def from_timedelta(cls, td: datetime.timedelta) -> "Duration":
        """Create a Duration from a datetime.timedelta.

        Parameters
        ----------
        td : datetime.timedelta
            The timedelta to convert.

        Returns
        -------
        Duration
            A Duration with only days and seconds components.
        """
        total_seconds = int(td.total_seconds())
        days = total_seconds // 86400
        remainder = total_seconds % 86400
        hours = remainder // 3600
        remainder = remainder % 3600
        minutes = remainder // 60
        seconds = remainder % 60
        return cls(days=days, hours=hours, minutes=minutes, seconds=seconds)

    def to_timedelta(self) -> datetime.timedelta:
        """Convert to a datetime.timedelta.

        This conversion is only exact when ``years`` and ``months`` are both zero,
        since calendar months/years have variable lengths.

        Returns
        -------
        datetime.timedelta
            The equivalent timedelta.

        Raises
        ------
        ValueError
            If the duration contains years or months, which cannot be
            unambiguously converted to a fixed timedelta.
        """
        if self.years != 0 or self.months != 0:
            raise ValueError("Cannot convert a Duration with years or months to timedelta without a reference date.")
        return datetime.timedelta(
            weeks=self.weeks,
            days=self.days,
            hours=self.hours,
            minutes=self.minutes,
            seconds=self.seconds,
        )

    def __repr__(self) -> str:
        parts = []
        for attr in ("years", "months", "weeks", "days", "hours", "minutes", "seconds"):
            val = getattr(self, attr)
            if val:
                parts.append(f"{attr}={val!r}")
        return f"Duration({', '.join(parts)})" if parts else "Duration()"

    def __str__(self) -> str:
        """Return the ISO 8601 string representation."""
        return self.to_iso_string()

    def to_iso_string(self) -> str:
        """Return the ISO 8601 duration string.

        Returns
        -------
        str
            E.g. ``"P1Y2M3DT4H5M6S"``.
        """
        date_parts = []
        if self.years:
            date_parts.append(f"{self.years}Y")
        if self.months:
            date_parts.append(f"{self.months}M")
        if self.weeks:
            date_parts.append(f"{self.weeks}W")
        if self.days:
            date_parts.append(f"{self.days}D")

        time_parts = []
        if self.hours:
            time_parts.append(f"{self.hours}H")
        if self.minutes:
            time_parts.append(f"{self.minutes}M")
        if self.seconds:
            s = int(self.seconds) if self.seconds == int(self.seconds) else self.seconds
            time_parts.append(f"{s}S")

        result = "P" + "".join(date_parts)
        if time_parts:
            result += "T" + "".join(time_parts)

        # Edge case: zero duration
        if result == "P":
            result = "PT0S"

        return result

    def __eq__(self, other) -> bool:
        if isinstance(other, Duration):
            return (
                self.years == other.years
                and self.months == other.months
                and self.weeks == other.weeks
                and self.days == other.days
                and self.hours == other.hours
                and self.minutes == other.minutes
                and self.seconds == other.seconds
            )
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self.years, self.months, self.weeks, self.days, self.hours, self.minutes, self.seconds))


def to_duration(value: Optional[Union["Duration", datetime.timedelta, str]]) -> Optional["Duration"]:
    """Convert a value to a Duration.

    Parameters
    ----------
    value : Duration, datetime.timedelta, str, or None
        The value to convert.

    Returns
    -------
    Duration or None
        The converted Duration, or None if input is None.

    Raises
    ------
    TypeError
        If the value type is not supported.
    """
    if value is None:
        return None
    if isinstance(value, Duration):
        return value
    if isinstance(value, datetime.timedelta):
        return Duration.from_timedelta(value)
    if isinstance(value, str):
        return Duration.from_str(value)
    raise TypeError(f"Cannot convert {type(value).__name__} to Duration")
