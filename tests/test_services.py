from datetime import date, time
import pytest
from app.database import Base
from app.models import WorkDay
from app.services import ValidationError, add_entry, day_duration, format_duration, validate_interval
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


def test_entries_sum_and_overlap_validation():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        day = WorkDay(date=date(2026, 9, 10))
        db.add(day); db.flush()
        add_entry(db, day, time(8), time(12))
        add_entry(db, day, time(12, 45), time(17))
        assert format_duration(day_duration(day)) == "08:15 h"
        with pytest.raises(ValidationError):
            add_entry(db, day, time(11), time(13))


def test_end_must_follow_start():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        day = WorkDay(date=date.today())
        db.add(day); db.flush()
        with pytest.raises(ValidationError):
            add_entry(db, day, time(12), time(12))


def test_open_phase_blocks_another_interval():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        day = WorkDay(date=date(2026, 9, 10))
        db.add(day); db.flush()
        add_entry(db, day, time(8), None)
        with pytest.raises(ValidationError, match="laufende Arbeitsphase"):
            add_entry(db, day, time(9), None)
        assert format_duration(day_duration(day)) == "00:00 h"


def test_adjacent_intervals_are_valid_and_edit_can_ignore_itself():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        day = WorkDay(date=date(2026, 9, 10))
        db.add(day); db.flush()
        first = add_entry(db, day, time(8), time(10))
        add_entry(db, day, time(10), time(12, 30))
        validate_interval(day, time(8, 15), time(9, 45), ignore_id=first.id)
        assert format_duration(day_duration(day)) == "04:30 h"
