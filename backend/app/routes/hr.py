from decimal import Decimal, InvalidOperation
from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from werkzeug.security import generate_password_hash
from ..extensions import db
from ..models import Department, Employee, User
from .common import require_admin

hr_bp = Blueprint("hr", __name__, url_prefix="/api")


def employee_json(e):
    return dict(id=e.id, code=e.code, name=e.name, email=e.email,
                department_id=e.department_id, designation=e.designation,
                base_salary=str(e.base_salary), active=e.active)


@hr_bp.get("/departments")
@require_admin
def departments():
    rows = db.session.execute(
        db.select(Department).order_by(Department.name)).scalars()
    return jsonify([dict(id=d.id, name=d.name) for d in rows])


@hr_bp.post("/departments")
@require_admin
def add_department():
    name = str(request.get_json(silent=True) or {}).get("name", "").strip()
    if not 2 <= len(name) <= 100:
        return jsonify(error="Department name must be 2-100 characters"), 400
    db.session.add(Department(name=name))
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="Department already exists"), 409
    return jsonify(message="Department added"), 201


@hr_bp.get("/employees")
@require_admin
def employees():
    query = db.select(Employee)
    term = request.args.get("search", "").strip()
    if term:
        pattern = f"%{term}%"
        query = query.filter(or_(Employee.code.ilike(pattern),
                                 Employee.name.ilike(pattern),
                                 Employee.designation.ilike(pattern)))
    rows = db.session.execute(query.order_by(Employee.id)).scalars()
    return jsonify([employee_json(e) for e in rows])


@hr_bp.post("/employees")
@require_admin
def add_employee():
    data = request.get_json(silent=True) or {}
    code = str(data.get("code", "")).strip()
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    designation = str(data.get("designation", "")).strip()
    try:
        department_id = int(data.get("department_id"))
        salary = Decimal(str(data.get("base_salary", "0")))
    except (TypeError, ValueError, InvalidOperation):
        return jsonify(error="Invalid department or salary"), 400
    if (not code or not name or "@" not in email or not designation
            or len(password) < 12 or not salary.is_finite() or salary < 0 or salary > 999999999):
        return jsonify(error="Complete all fields; password needs 12+ characters"), 400
    if not db.session.get(Department, department_id):
        return jsonify(error="Department does not exist"), 400
    emp = Employee(code=code, name=name, email=email, department_id=department_id,
                   designation=designation, base_salary=salary)
    db.session.add(emp)
    db.session.flush()
    db.session.add(User(email=email, password_hash=generate_password_hash(password),
                        role="employee", employee_id=emp.id))
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="Employee code or email already exists"), 409
    return jsonify(employee_json(emp)), 201


@hr_bp.patch("/employees/<int:employee_id>/status")
@require_admin
def set_employee_status(employee_id):
    emp = db.session.get(Employee, employee_id)
    if not emp:
        return jsonify(error="Employee not found"), 404
    active = (request.get_json(silent=True) or {}).get("active")
    if type(active) is not bool:
        return jsonify(error="active must be true or false"), 400
    emp.active = active
    db.session.commit()
    return jsonify(employee_json(emp))


@hr_bp.get("/employees/<int:employee_id>")
@require_admin
def employee_detail(employee_id):
    emp = db.session.get(Employee, employee_id)
    return (jsonify(employee_json(emp)), 200) if emp else (jsonify(error="Not found"), 404)


@hr_bp.patch("/employees/<int:employee_id>")
@require_admin
def update_employee(employee_id):
    emp = db.session.get(Employee, employee_id)
    if not emp:
        return jsonify(error="Employee not found"), 404
    data = request.get_json(silent=True) or {}
    for key in ("name", "designation", "phone"):
        if key in data:
            value = str(data[key]).strip()
            if key != "phone" and not value:
                return jsonify(error=f"{key} is required"), 400
            setattr(emp, key, value)
    if "department_id" in data:
        try:
            department_id = int(data["department_id"])
        except (ValueError, TypeError):
            return jsonify(error="Invalid department"), 400
        if not db.session.get(Department, department_id):
            return jsonify(error="Department does not exist"), 400
        emp.department_id = department_id
    if "base_salary" in data:
        try:
            salary = Decimal(str(data["base_salary"]))
        except (TypeError, InvalidOperation):
            return jsonify(error="Invalid salary"), 400
        if not salary.is_finite() or salary < 0 or salary > 999999999:
            return jsonify(error="Invalid salary"), 400
        emp.base_salary = salary
    db.session.commit()
    return jsonify(employee_json(emp))
