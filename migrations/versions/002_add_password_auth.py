"""add_password_auth

Revision ID: 002_add_password_auth
Revises: 001_initial
Create Date: 2026-02-03 22:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_add_password_auth"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add hashed_password column
    op.add_column("users", sa.Column("hashed_password", sa.String(), nullable=True))

    # Make provider and provider_user_id columns nullable
    op.alter_column("users", "provider", existing_type=sa.String(), nullable=True)
    op.alter_column("users", "provider_user_id", existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    # Make provider and provider_user_id columns non-nullable
    # WARNING: This might fail if there are local users without provider info
    op.alter_column("users", "provider_user_id", existing_type=sa.String(), nullable=False)
    op.alter_column("users", "provider", existing_type=sa.String(), nullable=False)

    # Remove hashed_password column
    op.drop_column("users", "hashed_password")
