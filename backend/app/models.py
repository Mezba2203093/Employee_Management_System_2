from datetime import datetime, timezone

from .extensions import db

# User Model

class User(db.Model):

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False,
        default="employee"
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
# Department Model

class Department(db.Model):

    __tablename__ = "departments"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    description = db.Column(
        db.String(255),
        nullable=True
    )

    employees = db.relationship(
        "Employee",
        back_populates="department_info"
    )

# Employee Model


class Employee(db.Model):

    __tablename__ = "employees"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    employee_code = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    full_name = db.Column(
        db.String(120),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    department_id = db.Column(
    db.Integer,
    db.ForeignKey("departments.id"),
    nullable=False
    )

    designation = db.Column(
        db.String(80),
        nullable=True
    )

    joining_date = db.Column(
        db.Date,
        nullable=True
    )

    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )
    department_info = db.relationship(
    "Department",
    back_populates="employees"
    )
    attendance_records = db.relationship(
        "Attendance",
        back_populates="employee"
    )
    leave_requests = db.relationship(
    "LeaveRequest",
    back_populates="employee"
    )
    
    # Leave Request Model

class LeaveRequest(db.Model):

    __tablename__ = "leave_requests"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.id"),
        nullable=False
    )

    start_date = db.Column(
        db.Date,
        nullable=False
    )

    end_date = db.Column(
        db.Date,
        nullable=False
    )

    reason = db.Column(
        db.Text,
        nullable=False
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="Pending"
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    employee = db.relationship(
        "Employee",
        back_populates="leave_requests"
    )

    __table_args__ = (

        db.CheckConstraint(
            "end_date >= start_date",
            name="valid_leave_date_range"
        ),

        db.CheckConstraint(
            "status IN ('Pending', 'Approved', 'Rejected')",
            name="valid_leave_status"
        ),

    )

# Attendance Model

class Attendance(db.Model):

    __tablename__ = "attendance"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.id"),
        nullable=False
    )

    attendance_date = db.Column(
        db.Date,
        nullable=False
    )

    check_in = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    check_out = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="Present"
    )

    employee = db.relationship(
        "Employee",
        back_populates="attendance_records"
    )

    __table_args__ = (

        db.UniqueConstraint(
            "employee_id",
            "attendance_date",
            name="unique_employee_attendance_date"
        ),

        db.CheckConstraint(
            "status IN ('Present', 'Absent', 'Late', 'Leave')",
            name="valid_attendance_status"
        ),

    )