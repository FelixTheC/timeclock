"""create tables

Revision ID: c42ddfb0d23a
Revises: 
Create Date: 2021-07-15 22:52:38.163052

"""
import datetime

import sqlalchemy as sa

from alembic import op
# revision identifiers, used by Alembic.
from src.models import uuid_str

revision = "c42ddfb0d23a"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "employee",
        sa.Column("id", sa.String, primary_key=True, default=uuid_str),
        sa.Column("uid", sa.String),
        sa.Column("name", sa.String),
        sa.Column("active", sa.Boolean, nullable=True, default=True),
        sa.Column("checked_in", sa.Boolean, default=True),
        sa.UniqueConstraint("uid", "name", name="unique_uid_name_1"),
    )

    op.create_table(
        "rcauthentication",
        sa.Column("id", sa.String, primary_key=True, default=uuid_str),
        sa.Column("uid", sa.String),
        sa.Column("requested_at", sa.DATETIME, default=datetime.datetime.utcnow),
        sa.Column("authenticated_at", sa.DateTime, nullable=True),
        sa.Column("success", sa.Boolean, default=False),
        sa.UniqueConstraint("uid", name="rcauthentication_uid_uindex"),
    )

    op.create_table(
        "timeclock",
        sa.Column("id", sa.String, primary_key=True, default=uuid_str),
        sa.Column("check_in", sa.DateTime),
        sa.Column("check_out", sa.DATETIME, default=datetime.datetime.utcnow),
        sa.Column("total", sa.Float, nullable=True),
        sa.Column("employee_id", sa.Integer, sa.ForeignKey("employee.id")),
    )


def downgrade():
    op.drop_table("employee")
    op.drop_table("rcauthentication")
    op.drop_table("timeclock")
