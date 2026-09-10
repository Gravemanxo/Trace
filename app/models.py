from datetime import date, time
from sqlalchemy import Column, Date, ForeignKey, Integer, Table, Text, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


work_day_projects = Table(
    "work_day_projects",
    Base.metadata,
    Column("work_day_id", ForeignKey("work_days.id"), primary_key=True),
    Column("project_id", ForeignKey("projects.id"), primary_key=True),
)


class WorkDay(Base):
    __tablename__ = "work_days"
    __table_args__ = (UniqueConstraint("date", name="uq_work_day_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    entries: Mapped[list["TimeEntry"]] = relationship(
        back_populates="work_day", cascade="all, delete-orphan", order_by="TimeEntry.start_time"
    )
    projects: Mapped[list["Project"]] = relationship(
        back_populates="work_days", secondary=work_day_projects, order_by="Project.name"
    )


class TimeEntry(Base):
    __tablename__ = "time_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    work_day_id: Mapped[int] = mapped_column(ForeignKey("work_days.id"), index=True)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    work_day: Mapped[WorkDay] = relationship(back_populates="entries")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    work_days: Mapped[list[WorkDay]] = relationship(back_populates="projects", secondary=work_day_projects)
    documents: Mapped[list["ProjectDocument"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", order_by="ProjectDocument.id.desc()"
    )


class ProjectDocument(Base):
    __tablename__ = "project_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    title: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    project: Mapped[Project] = relationship(back_populates="documents")
