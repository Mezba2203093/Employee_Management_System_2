import os
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo
from flask import Blueprint, jsonify
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models import Attendance, LeaveRequest

attendance_bp = Blueprint("attendance", __name__, url_prefix="/api/attendance")


def local_now():
    return datetime.now(ZoneInfo(os.getenv("OFFICE_TIMEZONE", "Asia/Dhaka")))


def attendance_json(a):
    return dict(id=a.id, date=a.work_date.isoformat(),
                check_in=a.check_in.isoformat(),
                check_out=a.check_out.isoformat() if a.check_out else None,
                work_minutes=a.work_minutes, status=a.status)


def employee_or_error():
    if current_user.role != "employee" or not current_user.employee_id:
        return None
    return current_user.employee_id


@attendance_bp.get("/today")
@login_required
def today():
    employee_id = employee_or_error()
    if not employee_id:
        return jsonify(error="Employee account required"), 403
    row = db.session.execute(db.select(Attendance).filter_by(
        employee_id=employee_id, work_date=local_now().date())).scalar_one_or_none()
    return jsonify(attendance_json(row) if row else None)


@attendance_bp.get("/history")
@login_required
def history():
    employee_id = employee_or_error()
    if not employee_id:
        return jsonify(error="Employee account required"), 403
    rows = db.session.execute(db.select(Attendance).filter_by(employee_id=employee_id)
                              .order_by(Attendance.work_date.desc()).limit(90)).scalars()
    return jsonify([attendance_json(a) for a in rows])


@attendance_bp.post("/check-in")
@login_required
def check_in():
    employee_id = employee_or_error()
    if not employee_id:
        return jsonify(error="Employee account required"), 403
    now = local_now()
    existing = db.session.execute(db.select(Attendance).filter_by(
        employee_id=employee_id, work_date=now.date())).scalar_one_or_none()
    if existing:
        return jsonify(error="You have already checked in today"), 409
    leave = db.session.execute(db.select(LeaveRequest).filter(
        LeaveRequest.employee_id == employee_id,
        LeaveRequest.status == "approved",
        LeaveRequest.start_date <= now.date(),
        LeaveRequest.end_date >= now.date())).first()
    if leave:
        return jsonify(error="Approved leave is recorded for today"), 409
    office_hour, office_minute = map(
        int, os.getenv("OFFICE_START", "09:00").split(":"))
    status = "late" if now.time() > time(office_hour, office_minute) else "present"
    row = Attendance(employee_id=employee_id, work_date=now.date(),
                     check_in=datetime.now(timezone.utc), status=status)
    db.session.add(row)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="A check-in already exists"), 409
    return jsonify(attendance_json(row)), 201


@attendance_bp.post("/check-out")
@login_required
def check_out():
    employee_id = employee_or_error()
    if not employee_id:
        return jsonify(error="Employee account required"), 403
    row = db.session.execute(db.select(Attendance).filter_by(
        employee_id=employee_id, work_date=local_now().date())).scalar_one_or_none()
    if not row or row.check_out:
        return jsonify(error="Check in first; check-out is allowed only once"), 409
    now = datetime.now(timezone.utc)
    checked_in = row.check_in
    if checked_in.tzinfo is None:
        checked_in = checked_in.replace(tzinfo=timezone.utc)
    row.check_out = now
    row.work_minutes = max(0, int((now - checked_in).total_seconds() // 60))
    db.session.commit()
    return jsonify(attendance_json(row))
