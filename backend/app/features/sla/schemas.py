from datetime import time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator, model_validator

from app.features.tickets.schemas import Priority

MAX_MINUTES = 60 * 24 * 60  # 60 days
HORIZON_WEEKS = 150  # stays inside deadlines.MAX_DAYS (about 156 weeks)


class TargetIO(BaseModel):
    first_response_minutes: int = Field(ge=1, le=MAX_MINUTES)
    resolution_minutes: int = Field(ge=1, le=MAX_MINUTES)

    @model_validator(mode="after")
    def _first_response_comes_first(self) -> "TargetIO":
        if self.first_response_minutes > self.resolution_minutes:
            raise ValueError("first response target can't exceed the resolution target")
        return self


class ScheduleIO(BaseModel):
    days: list[int] = Field(min_length=1, max_length=7)  # 0 = Monday
    start: time
    end: time

    @field_validator("days")
    @classmethod
    def _valid_days(cls, days: list[int]) -> list[int]:
        if len(set(days)) != len(days) or any(not 0 <= d <= 6 for d in days):
            raise ValueError("days must be distinct weekday numbers 0 (Mon) to 6 (Sun)")
        return sorted(days)

    @model_validator(mode="after")
    def _opens_before_close(self) -> "ScheduleIO":
        if self.start >= self.end:
            raise ValueError("start must be before end")
        return self


class SlaSettingsIO(BaseModel):
    targets: dict[Priority, TargetIO]
    timezone: str = Field(max_length=64)
    schedule: ScheduleIO

    @field_validator("targets")
    @classmethod
    def _all_priorities(cls, targets: dict[str, TargetIO]) -> dict[str, TargetIO]:
        if set(targets) != {"P1", "P2", "P3", "P4"}:
            raise ValueError("give targets for P1, P2, P3 and P4")
        return targets

    @field_validator("timezone")
    @classmethod
    def _iana_name(cls, tz: str) -> str:
        try:
            ZoneInfo(tz)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError("timezone must be an IANA name, e.g. Europe/London") from None
        return tz

    @model_validator(mode="after")
    def _targets_fit_the_schedule(self) -> "SlaSettingsIO":
        """Reject targets the schedule can't reach within the horizon (code review: a 1-hour
        weekly schedule with a 60-day target made every new ticket a 500)."""
        s = self.schedule
        weekly = len(s.days) * ((s.end.hour * 60 + s.end.minute) - (s.start.hour * 60 + s.start.minute))
        for priority, target in self.targets.items():
            if priority != "P1" and target.resolution_minutes > weekly * HORIZON_WEEKS:
                raise ValueError(f"{priority} resolution target is too long for this schedule")
        return self
