from datetime import date, datetime, time, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from .models import TimeEntry, WorkDay


class ValidationError(ValueError):
    pass


def get_or_create_day(db: Session, day_date: date) -> WorkDay:
    day = db.scalar(
        select(WorkDay)
        .where(WorkDay.date == day_date)
        .options(selectinload(WorkDay.entries), selectinload(WorkDay.projects))
    )
    if not day:
        day = WorkDay(date=day_date)
        db.add(day)
        db.flush()
    return day


def get_day(db: Session, day_date: date) -> WorkDay | None:
    return db.scalar(select(WorkDay).where(WorkDay.date == day_date).options(selectinload(WorkDay.entries), selectinload(WorkDay.projects)))


def duration(entry: TimeEntry) -> timedelta:
    if not entry.end_time:
        return timedelta()
    return datetime.combine(date.min, entry.end_time) - datetime.combine(date.min, entry.start_time)


def day_duration(day: WorkDay | None) -> timedelta:
    if not day:
        return timedelta()
    return sum((duration(entry) for entry in day.entries), timedelta())


def validate_interval(day: WorkDay, start: time, end: time | None, ignore_id: int | None = None) -> None:
    if end and end <= start:
        raise ValidationError("Die Endzeit muss nach der Startzeit liegen.")
    for entry in day.entries:
        if entry.id == ignore_id:
            continue
        # Eine offene Phase blockiert neue Intervalle; zwei offene Phasen sind nicht erlaubt.
        if entry.end_time is None:
            raise ValidationError("Es gibt bereits eine laufende Arbeitsphase.")
        if end and start < entry.end_time and end > entry.start_time:
            raise ValidationError(
                "Überschneidung mit "
                f"{entry.start_time.strftime('%H:%M')}–{entry.end_time.strftime('%H:%M')}."
            )
        if end is None and start < entry.end_time:
            raise ValidationError("Die laufende Arbeitsphase würde sich überschneiden.")


def add_entry(db: Session, day: WorkDay, start: time, end: time | None) -> TimeEntry:
    validate_interval(day, start, end)
    entry = TimeEntry(work_day=day, start_time=start, end_time=end)
    db.add(entry)
    db.flush()
    return entry


def format_duration(value: timedelta) -> str:
    minutes = max(0, int(value.total_seconds() // 60))
    return f"{minutes // 60:02d}:{minutes % 60:02d} h"


def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())
