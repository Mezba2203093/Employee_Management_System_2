from . import create_app
from .extensions import db
from .models import Department, Employee


def seed_database():

    app = create_app()

    with app.app_context():

        # Create sample departments


        departments = [
            {
                "name": "IT",
                "description": "Information Technology"
            },
            {
                "name": "HR",
                "description": "Human Resources"
            },
            {
                "name": "Finance",
                "description": "Financial Operations"
            }
        ]

        for department_data in departments:

            existing_department = Department.query.filter_by(
                name=department_data["name"]
            ).first()

            if existing_department is None:

                department = Department(**department_data)

                db.session.add(department)

        db.session.commit()

        # Create sample employees


        employees = [
            {
                "employee_code": "EMP001",
                "full_name": "Rahim Ahmed",
                "email": "rahim@example.com",
                "department": "IT",
                "designation": "Software Engineer"
            },
            {
                "employee_code": "EMP002",
                "full_name": "Karim Hasan",
                "email": "karim@example.com",
                "department": "HR",
                "designation": "HR Officer"
            },
            {
                "employee_code": "EMP003",
                "full_name": "Nadia Islam",
                "email": "nadia@example.com",
                "department": "Finance",
                "designation": "Accountant"
            }
        ]

        for employee_data in employees:

            existing_employee = Employee.query.filter_by(
                employee_code=employee_data["employee_code"]
            ).first()

            if existing_employee is None:

                department = Department.query.filter_by(
                    name=employee_data["department"]
                ).first()

                employee = Employee(
                    employee_code=employee_data["employee_code"],
                    full_name=employee_data["full_name"],
                    email=employee_data["email"],
                    department_id=department.id,
                    designation=employee_data["designation"]
                )

                db.session.add(employee)

        db.session.commit()

        print("Sample departments and employees inserted successfully!")


if __name__ == "__main__":

    seed_database()