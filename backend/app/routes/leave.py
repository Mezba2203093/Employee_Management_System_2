from datetime import date
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from ..extensions import db
from ..models import Attendance, LeaveRequest
from .common import require_admin

leave_bp = Blueprint("leave", __name__, url_prefix="/api/leaves")


def leave_json(item):
    return dict(id=item.id, employee_id=item.employee_id,
                leave_type=item.leave_type,
                start_date=item.start_date.isoformat(), end_date=item.end_date.isoformat(),
                reason=item.reason, status=item.status)


@leave_bp.get("")
@login_required
def list_leaves():
    query = db.select(LeaveRequest).order_by(LeaveRequest.id.desc())
    if current_user.role != "admin":
        query = query.filter_by(employee_id=current_user.employee_id)
    rows = db.session.execute(query).scalars()
    return jsonify([leave_json(row) for row in rows])


@leave_bp.post("")
@login_required
def submit_leave():
    if current_user.role != "employee" or not current_user.employee_id:
        return jsonify(error="Employee account required"), 403
    data = request.get_json(silent=True) or {}
    try:
        start = date.fromisoformat(str(data.get("start_date", "")))
        end = date.fromisoformat(str(data.get("end_date", "")))
    except ValueError:
        return jsonify(error="Use YYYY-MM-DD dates"), 400
    reason = str(data.get("reason", "")).strip()
    leave_type = str(data.get("leave_type", "")).strip()
    if end < start or not reason or not 1 <= len(leave_type) <= 40:
        return jsonify(error="Invalid period, leave type or reason"), 400
    row = LeaveRequest(employee_id=current_user.employee_id, leave_type=leave_type,
                       start_date=start, end_date=end, reason=reason)
    db.session.add(row)
    db.session.commit()
    return jsonify(leave_json(row)), 201


@leave_bp.patch("/<int:leave_id>/decision")
@require_admin
def decide_leave(leave_id):
    row = db.session.get(LeaveRequest, leave_id)
    if not row:
        return jsonify(error="Leave request not found"), 404
    status = (request.get_json(silent=True) or {}).get("status")
    if row.status != "pending" or status not in {"approved", "rejected"}:
        return jsonify(error="Only pending requests may be approved/rejected"), 409
    if status == "approved":
        conflict = db.session.execute(db.select(Attendance).filter(
            Attendance.employee_id == row.employee_id,
            Attendance.work_date >= row.start_date,
            Attendance.work_date <= row.end_date)).first()
        if conflict:
            return jsonify(error="Cannot approve leave on recorded attendance dates"), 409
    row.status = status
    row.reviewed_by = current_user.id
    db.session.commit()
    return jsonify(leave_json(row))
