import getpass
import click
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash
from .extensions import db
from .models import User


def register_cli(app):
    @app.cli.command("init-admin")
    @click.option("--email", prompt=True, help="Administrator email")
    def init_admin(email):
        email = email.strip().lower()
        password = getpass.getpass("New admin password (12+ chars): ")
        if "@" not in email or len(password) < 12:
            raise click.ClickException("Valid email and 12+ character password required")
        db.session.add(User(email=email, password_hash=generate_password_hash(password),
                            role="admin", enabled=True))
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise click.ClickException("Administrator email already exists")
        click.echo("Admin created. Do not share its credentials.")
