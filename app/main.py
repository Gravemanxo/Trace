from __future__ import annotations

import base64
import calendar
import csv
import hmac
import io
import json
import secrets
from contextlib import asynccontextmanager
from datetime import date, datetime, time, timedelta
from pathlib import Path
from urllib.parse import urlencode

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from .config import settings
from .database import Base, engine, get_db
from .models import Project, ProjectDocument, TimeEntry, WorkDay
from .services import (
    ValidationError,
    add_entry,
    day_duration,
    duration,
    format_duration,
    get_day,
    get_or_create_day,
    validate_interval,
    week_start,
)

BASE_DIR = Path(__file__).parent
MONTH_NAMES = (
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.validate()
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Trace", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")
templates.env.filters["duration"] = format_duration
templates.env.filters["entry_duration"] = duration
templates.env.globals.update(day_duration=day_duration, csrf_token=lambda request: request.state.csrf_token)


@app.middleware("http")
async def app_guard(request: Request, call_next):
    if settings.auth_enabled:
        header = request.headers.get("Authorization", "")
        expected = base64.b64encode(
            f"{settings.auth_username}:{settings.auth_password}".encode()
        ).decode()
        if not hmac.compare_digest(header, f"Basic {expected}"):
            return HTMLResponse(
                "Anmeldung erforderlich",
                401,
                {"WWW-Authenticate": 'Basic realm="Arbeitsraum"'},
            )

    token = request.cookies.get(settings.csrf_cookie_name) or secrets.token_urlsafe(32)
    request.state.csrf_token = token
    response = await call_next(request)
    if settings.csrf_cookie_name not in request.cookies:
        response.set_cookie(settings.csrf_cookie_name, token, samesite="strict")
    response.headers.update(
        {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "same-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            "Content-Security-Policy": (
                "default-src 'self'; img-src 'self' data:; style-src 'self'; "
                "script-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
            ),
        }
    )
    return response


def verify_csrf(request: Request, csrf_token: str = Form("")) -> None:
    expected = request.cookies.get(settings.csrf_cookie_name, "")
    if not expected or not hmac.compare_digest(expected, csrf_token):
        raise HTTPException(403, "Ungültiges oder fehlendes Formular-Token.")


def now() -> datetime:
    return datetime.now(settings.timezone)


def parse_date(value: str | None, fallback: date | None = None) -> date:
    try:
        return date.fromisoformat(value) if value else (fallback or now().date())
    except ValueError as exc:
        raise HTTPException(400, "Ungültiges Datum") from exc


def parse_time(value: str) -> time:
    try:
        return time.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError("Ungültige Uhrzeit.") from exc


def redirect_day(day_date: date, error: str | None = None) -> RedirectResponse:
    query = urlencode({"error": error}) if error else ""
    return RedirectResponse(
        f"/days/{day_date.isoformat()}" + (f"?{query}" if query else ""), 303
    )


def month_period(month: str | None) -> tuple[str, date, date]:
    selected = month or now().strftime("%Y-%m")
    try:
        year, month_number = map(int, selected.split("-"))
        first = date(year, month_number, 1)
    except (ValueError, TypeError):
        current = now()
        selected = current.strftime("%Y-%m")
        first = date(current.year, current.month, 1)
    following = date(
        first.year + (first.month == 12), 1 if first.month == 12 else first.month + 1, 1
    )
    return selected, first, following


def active_elapsed(day: WorkDay | None, current: datetime) -> timedelta:
    if not day or day.date != current.date():
        return timedelta()
    running = next((entry for entry in day.entries if entry.end_time is None), None)
    if not running:
        return timedelta()
    return max(
        current.replace(tzinfo=None) - datetime.combine(day.date, running.start_time),
        timedelta(),
    )


def report_text(days: list[WorkDay], heading: str) -> str:
    lines = [f"Tätigkeitsbericht – {heading}", ""]
    for work_day in sorted(days, key=lambda item: item.date):
        if work_day.notes.strip():
            lines.extend(
                [
                    f"{work_day.date.strftime('%d.%m.%Y')} · {format_duration(day_duration(work_day))}",
                    work_day.notes.strip(),
                    "",
                ]
            )
    return "\n".join(lines).strip() or (
        f"Tätigkeitsbericht – {heading}\n\n"
        "Für diesen Monat sind noch keine Tätigkeiten dokumentiert."
    )


def load_days(db: Session) -> list[WorkDay]:
    return list(
        db.scalars(
            select(WorkDay).options(selectinload(WorkDay.entries)).order_by(WorkDay.date)
        ).all()
    )


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, error: str | None = None, db: Session = Depends(get_db)):
    current = now()
    today = get_day(db, current.date())
    running = next((entry for entry in (today.entries if today else []) if entry.end_time is None), None)
    elapsed = active_elapsed(today, current)
    today_total = day_duration(today) + elapsed
    days = load_days(db)
    week_total = sum(
        (day_duration(day) for day in days if week_start(day.date) == week_start(current.date())),
        timedelta(),
    ) + elapsed
    month_total = sum(
        (
            day_duration(day)
            for day in days
            if day.date.year == current.year and day.date.month == current.month
        ),
        timedelta(),
    ) + elapsed
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "today": today,
            "current": current,
            "running": running,
            "today_total": today_total,
            "running_started": (
                datetime.combine(current.date(), running.start_time, tzinfo=settings.timezone).isoformat()
                if running else None
            ),
            "completed_seconds": int(day_duration(today).total_seconds()),
            "week_total": week_total,
            "month_total": month_total,
            "day_count": len(days),
            "error": error,
        },
    )


@app.post("/check-in", dependencies=[Depends(verify_csrf)])
def check_in(db: Session = Depends(get_db)):
    current = now()
    day = get_or_create_day(db, current.date())
    try:
        add_entry(db, day, current.time().replace(microsecond=0), None)
        db.commit()
    except ValidationError as exc:
        db.rollback()
        return RedirectResponse(f"/?{urlencode({'error': str(exc)})}", 303)
    return RedirectResponse("/", 303)


@app.post("/check-out", dependencies=[Depends(verify_csrf)])
def check_out(db: Session = Depends(get_db)):
    current = now()
    day = get_day(db, current.date())
    running = next((entry for entry in (day.entries if day else []) if entry.end_time is None), None)
    if not running:
        return RedirectResponse("/?error=Keine+laufende+Arbeitsphase+gefunden.", 303)
    if current.time().replace(microsecond=0) <= running.start_time:
        return RedirectResponse("/?error=Die+Endzeit+muss+nach+der+Startzeit+liegen.", 303)
    running.end_time = current.time().replace(microsecond=0)
    db.commit()
    return RedirectResponse("/", 303)


@app.get("/days/{day_value}", response_class=HTMLResponse)
def edit_day(day_value: str, request: Request, error: str | None = None, db: Session = Depends(get_db)):
    day_date = parse_date(day_value)
    return templates.TemplateResponse(
        request,
        "day.html",
        {
            "day": get_day(db, day_date),
            "day_date": day_date,
            "error": error,
            "projects": db.scalars(select(Project).order_by(Project.name)).all(),
        },
    )


@app.post("/days/{day_value}/notes", dependencies=[Depends(verify_csrf)])
def save_notes(day_value: str, notes: str = Form(""), db: Session = Depends(get_db)):
    day = get_or_create_day(db, parse_date(day_value))
    day.notes = notes.strip()
    db.commit()
    return redirect_day(day.date)


@app.post("/days/{day_value}/projects", dependencies=[Depends(verify_csrf)])
def save_day_projects(day_value: str, project_ids: list[int] = Form([]), db: Session = Depends(get_db)):
    day = get_or_create_day(db, parse_date(day_value))
    day.projects = (
        list(db.scalars(select(Project).where(Project.id.in_(project_ids))).all())
        if project_ids else []
    )
    db.commit()
    return redirect_day(day.date)


@app.post("/days/{day_value}/entries", dependencies=[Depends(verify_csrf)])
def create_entry(day_value: str, start_time: str = Form(...), end_time: str = Form(""), db: Session = Depends(get_db)):
    day = get_or_create_day(db, parse_date(day_value))
    try:
        add_entry(db, day, parse_time(start_time), parse_time(end_time) if end_time else None)
        db.commit()
    except ValidationError as exc:
        db.rollback()
        return redirect_day(day.date, str(exc))
    return redirect_day(day.date)


@app.post("/entries/{entry_id}", dependencies=[Depends(verify_csrf)])
def update_entry(entry_id: int, start_time: str = Form(...), end_time: str = Form(""), db: Session = Depends(get_db)):
    entry = db.scalar(
        select(TimeEntry)
        .where(TimeEntry.id == entry_id)
        .options(selectinload(TimeEntry.work_day).selectinload(WorkDay.entries))
    )
    if not entry:
        raise HTTPException(404)
    try:
        start = parse_time(start_time)
        end = parse_time(end_time) if end_time else None
        validate_interval(entry.work_day, start, end, entry.id)
        entry.start_time, entry.end_time = start, end
        db.commit()
    except ValidationError as exc:
        db.rollback()
        return redirect_day(entry.work_day.date, str(exc))
    return redirect_day(entry.work_day.date)


@app.post("/entries/{entry_id}/delete", dependencies=[Depends(verify_csrf)])
def delete_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.get(TimeEntry, entry_id)
    if not entry:
        raise HTTPException(404)
    day_date = entry.work_day.date
    db.delete(entry)
    db.commit()
    return redirect_day(day_date)


@app.get("/history", response_class=HTMLResponse)
def history(request: Request, month: str | None = None, db: Session = Depends(get_db)):
    selected, first, next_month = month_period(month)
    days = list(
        db.scalars(
            select(WorkDay)
            .where(WorkDay.date >= first, WorkDay.date < next_month)
            .options(selectinload(WorkDay.entries), selectinload(WorkDay.projects))
            .order_by(WorkDay.date.desc())
        ).all()
    )
    by_date = {day.date: day for day in days}
    current_date = now().date()
    calendar_days = []
    for number in range(1, calendar.monthrange(first.year, first.month)[1] + 1):
        item_date = date(first.year, first.month, number)
        item = by_date.get(item_date)
        seconds = day_duration(item).total_seconds()
        intensity = 0 if not seconds else 1 if seconds < 4 * 3600 else 2 if seconds < 7 * 3600 else 3
        calendar_days.append(
            {
                "date": item_date,
                "day": item,
                "intensity": intensity,
                "is_weekend": item_date.weekday() >= 5,
                "is_today": item_date == current_date,
            }
        )
    previous_first = (first - timedelta(days=1)).replace(day=1)
    return templates.TemplateResponse(
        request,
        "history.html",
        {
            "days": days,
            "month": selected,
            "calendar_days": calendar_days,
            "first_weekday": first.weekday(),
            "previous_month": previous_first.strftime("%Y-%m"),
            "next_month": next_month.strftime("%Y-%m"),
            "month_label": f"{MONTH_NAMES[first.month - 1]} {first.year}",
            "today_iso": current_date.isoformat(),
        },
    )


@app.get("/projects", response_class=HTMLResponse)
def projects(request: Request, error: str | None = None, db: Session = Depends(get_db)):
    items = db.scalars(
        select(Project)
        .options(selectinload(Project.documents), selectinload(Project.work_days))
        .order_by(Project.name)
    ).all()
    return templates.TemplateResponse(request, "projects.html", {"projects": items, "error": error})


@app.get("/network", response_class=HTMLResponse)
def network(request: Request, db: Session = Depends(get_db)):
    projects = db.scalars(
        select(Project)
        .options(selectinload(Project.work_days), selectinload(Project.documents))
        .order_by(Project.name)
    ).all()
    nodes: list[dict[str, str]] = []
    edges: list[dict[str, str]] = []
    seen_days: set[int] = set()
    for project in projects:
        project_node = f"project-{project.id}"
        nodes.append({"id": project_node, "label": project.name, "type": "project", "url": f"/projects/{project.id}"})
        for work_day in project.work_days:
            day_node = f"day-{work_day.id}"
            if work_day.id not in seen_days:
                nodes.append({"id": day_node, "label": work_day.date.strftime("%d.%m.%Y"), "type": "day", "url": f"/days/{work_day.date.isoformat()}"})
                seen_days.add(work_day.id)
            edges.append({"source": project_node, "target": day_node})
        for document in project.documents:
            document_node = f"document-{document.id}"
            nodes.append({"id": document_node, "label": document.title, "type": "document", "url": f"/documents/{document.id}"})
            edges.append({"source": project_node, "target": document_node})
    graph_data = json.dumps({"nodes": nodes, "edges": edges}).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return templates.TemplateResponse(
        request,
        "network.html",
        {"graph_data": graph_data, "project_count": len(projects), "day_count": len(seen_days)},
    )


@app.post("/projects", dependencies=[Depends(verify_csrf)])
def create_project(name: str = Form(...), description: str = Form(""), db: Session = Depends(get_db)):
    cleaned = name.strip()
    if not cleaned:
        return RedirectResponse("/projects?error=Bitte+einen+Projektnamen+angeben.", 303)
    project = Project(name=cleaned, description=description.strip())
    db.add(project)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return RedirectResponse("/projects?error=Der+Projektname+existiert+bereits.", 303)
    return RedirectResponse(f"/projects/{project.id}", 303)


@app.get("/projects/{project_id}", response_class=HTMLResponse)
def project_detail(project_id: int, request: Request, error: str | None = None, db: Session = Depends(get_db)):
    project = db.scalar(
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.documents), selectinload(Project.work_days))
    )
    if not project:
        raise HTTPException(404)
    return templates.TemplateResponse(request, "project.html", {"project": project, "error": error})


@app.get("/documents/{document_id}", response_class=HTMLResponse)
def document_detail(document_id: int, request: Request, error: str | None = None, db: Session = Depends(get_db)):
    document = db.scalar(
        select(ProjectDocument)
        .where(ProjectDocument.id == document_id)
        .options(selectinload(ProjectDocument.project))
    )
    if not document:
        raise HTTPException(404)
    return templates.TemplateResponse(request, "document.html", {"document": document, "error": error})


@app.post("/documents/{document_id}", dependencies=[Depends(verify_csrf)])
def save_document(document_id: int, title: str = Form(...), content: str = Form(""), db: Session = Depends(get_db)):
    document = db.get(ProjectDocument, document_id)
    if not document:
        raise HTTPException(404)
    if not title.strip():
        return RedirectResponse(f"/documents/{document.id}?error=Bitte+einen+Titel+angeben.", 303)
    document.title, document.content = title.strip(), content.strip()
    db.commit()
    return RedirectResponse(f"/documents/{document.id}", 303)


@app.post("/projects/{project_id}", dependencies=[Depends(verify_csrf)])
def save_project(project_id: int, name: str = Form(...), description: str = Form(""), db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404)
    if not name.strip():
        return RedirectResponse(f"/projects/{project.id}?error=Bitte+einen+Namen+angeben.", 303)
    project.name, project.description = name.strip(), description.strip()
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return RedirectResponse(f"/projects/{project.id}?error=Der+Projektname+existiert+bereits.", 303)
    return RedirectResponse(f"/projects/{project.id}", 303)


@app.post("/projects/{project_id}/documents", dependencies=[Depends(verify_csrf)])
def create_document(project_id: int, title: str = Form(...), content: str = Form(""), db: Session = Depends(get_db)):
    if not db.get(Project, project_id):
        raise HTTPException(404)
    if not title.strip():
        return RedirectResponse(f"/projects/{project_id}?error=Bitte+einen+Dokumenttitel+angeben.", 303)
    document = ProjectDocument(project_id=project_id, title=title.strip(), content=content.strip())
    db.add(document)
    db.commit()
    return RedirectResponse(f"/documents/{document.id}", 303)


@app.get("/report", response_class=HTMLResponse)
def report(request: Request, month: str | None = None, db: Session = Depends(get_db)):
    selected, first, next_month = month_period(month)
    days = list(
        db.scalars(
            select(WorkDay)
            .where(WorkDay.date >= first, WorkDay.date < next_month)
            .options(selectinload(WorkDay.entries))
            .order_by(WorkDay.date)
        ).all()
    )
    heading = f"{MONTH_NAMES[first.month - 1]} {first.year}"
    documented = [day for day in days if day.notes.strip()]
    return templates.TemplateResponse(
        request,
        "report.html",
        {
            "month": selected,
            "month_label": heading,
            "days": documented,
            "work_days": len(days),
            "documented_days": len(documented),
            "month_total": sum((day_duration(day) for day in days), timedelta()),
            "report_text": report_text(days, heading),
        },
    )


@app.get("/report.txt")
def export_report_text(month: str | None = None, db: Session = Depends(get_db)):
    selected, first, next_month = month_period(month)
    days = list(db.scalars(select(WorkDay).where(WorkDay.date >= first, WorkDay.date < next_month).options(selectinload(WorkDay.entries))).all())
    heading = f"{MONTH_NAMES[first.month - 1]} {first.year}"
    return StreamingResponse(
        iter([report_text(days, heading)]),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=taetigkeitsbericht-{selected}.txt"},
    )


@app.get("/overview", response_class=HTMLResponse)
def overview(request: Request, db: Session = Depends(get_db)):
    current = now()
    days = load_days(db)
    current_day = next((day for day in days if day.date == current.date()), None)
    elapsed = active_elapsed(current_day, current)
    total = sum((day_duration(day) for day in days), timedelta()) + elapsed
    week = sum((day_duration(day) for day in days if week_start(day.date) == week_start(current.date())), timedelta()) + elapsed
    month = sum((day_duration(day) for day in days if day.date.year == current.year and day.date.month == current.month), timedelta()) + elapsed
    week_days = []
    start = week_start(current.date())
    for offset in range(7):
        item_date = start + timedelta(days=offset)
        item = next((day for day in days if day.date == item_date), None)
        value = day_duration(item) + (elapsed if item_date == current.date() else timedelta())
        height = min(100, round(value.total_seconds() / (8 * 3600) * 100))
        week_days.append({"date": item_date, "label": ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")[offset], "seconds": value.total_seconds(), "height_step": max(1, min(10, round(height / 10)))})
    return templates.TemplateResponse(
        request,
        "overview.html",
        {"today_total": day_duration(current_day) + elapsed, "week_total": week, "month_total": month, "total": total, "day_count": len(days), "week_days": week_days},
    )


@app.get("/export.csv")
def export_csv(db: Session = Depends(get_db)):
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Datum", "Startzeit", "Endzeit", "Arbeitsdauer", "Tätigkeitsbeschreibung"])
    for day in load_days(db):
        for entry in day.entries:
            entry_total = (
                datetime.combine(date.min, entry.end_time) - datetime.combine(date.min, entry.start_time)
                if entry.end_time else timedelta()
            )
            writer.writerow([day.date.isoformat(), entry.start_time.strftime("%H:%M"), entry.end_time.strftime("%H:%M") if entry.end_time else "", format_duration(entry_total), day.notes])
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=zeiterfassung.csv"},
    )
