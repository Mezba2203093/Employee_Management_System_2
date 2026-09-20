from calendar import monthrange
from datetime import date
from decimal import Decimal
from flask import Blueprint, jsonify, request
from sqlalchemy import func
from ..extensions import db
from ..models import Attendance, Employee, LeaveRequest
from .common import require_admin
from .attendance import local_now

report_bp = Blueprint("reports", __name__, url_prefix="/api")


@report_bp.get("/dashboard")
@require_admin
def dashboard():
    today = local_now().date()
    total = db.session.scalar(db.select(func.count()).select_from(Employee)
                              .filter_by(active=True)) or 0
    present = db.session.scalar(db.select(func.count()).select_from(Attendance)
                                .join(Employee, Attendance.employee_id == Employee.id)
                                .filter(Attendance.work_date == today, Employee.active.is_(True))) or 0
    late = db.session.scalar(db.select(func.count()).select_from(Attendance)
                             .join(Employee, Attendance.employee_id == Employee.id)
                             .filter(Attendance.work_date == today, Attendance.status == "late",
                                     Employee.active.is_(True))) or 0
    on_leave = db.session.scalar(db.select(func.count(func.distinct(LeaveRequest.employee_id)))
                                 .select_from(LeaveRequest)
                                 .join(Employee, LeaveRequest.employee_id == Employee.id)
                                 .filter(LeaveRequest.status == "approved",
                                         LeaveRequest.start_date <= today,
                                         LeaveRequest.end_date >= today,
                                         Employee.active.is_(True))) or 0
    return jsonify(total=total, present=present - on_leave,
                   on_leave=on_leave, absent=max(0, total - present - on_leave))


@report_bp.get("/reports/monthly")
@require_admin
def monthly_report():
    month_text = request.args.get("month", local_now().strftime("%Y-%m"))
    try:
        year, month = map(int, month_text.split("-"))
        first, last = date(year, month, 1), date(
            year, month, monthrange(year, month)[1])
    except (ValueError, TypeError):
        return jsonify(error="month must be YYYY-MM"), 400
    days = sum(date(year, month, day).weekday() <
               5 for day in range(1, last.day + 1))
    rows = db.session.execute(db.select(Employee).filter_by(active=True)
                              .order_by(Employee.id)).scalars()
    result = []
    for employee in rows:
        attendances = db.session.execute(db.select(Attendance).filter(
            Attendance.employee_id == employee.id,
            Attendance.work_date >= first, Attendance.work_date <= last)).scalars()
        records = list(attendances)
        present_days = sum(a.work_date.weekday() < 5 for a in records)
        late_days = sum(a.status == "late" for a in records)
        estimate = employee.base_salary * \
            Decimal(present_days) / Decimal(days or 1)
        result.append(dict(employee_code=employee.code, name=employee.name,
                           present_days=present_days, late_days=late_days,
                           work_minutes=sum(a.work_minutes for a in records),
                           attendance_based_estimate=str(estimate.quantize(Decimal("0.01")))))
    return jsonify(month=month_text, scheduled_weekdays=days,
                   note="Illustrative attendance-only estimate; NOT a payroll calculation. "
                        "Approved paid leave, holidays, overtime and deductions are excluded.",
                   employees=result)
