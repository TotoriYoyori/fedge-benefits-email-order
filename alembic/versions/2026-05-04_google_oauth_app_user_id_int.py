"""google oauth app_user_id int

Revision ID: 62c7835dbeb7
Revises: f545786d436b
Create Date: 2026-05-04 13:06:21.053360

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '62c7835dbeb7'
down_revision: Union[str, Sequence[str], None] = 'f545786d436b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("google_oauth_credentials", recreate="always") as batch:
        batch.alter_column(
            "app_user_id",
            existing_type=sa.VARCHAR(length=255),
            type_=sa.Integer(),
            existing_nullable=False,
        )

    with op.batch_alter_table("google_oauth_states", recreate="always") as batch:
        batch.alter_column(
            "app_user_id",
            existing_type=sa.VARCHAR(length=255),
            type_=sa.Integer(),
            existing_nullable=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("google_oauth_states", recreate="always") as batch:
        batch.alter_column(
            "app_user_id",
            existing_type=sa.Integer(),
            type_=sa.VARCHAR(length=255),
            existing_nullable=False,
        )

    with op.batch_alter_table("google_oauth_credentials", recreate="always") as batch:
        batch.alter_column(
            "app_user_id",
            existing_type=sa.Integer(),
            type_=sa.VARCHAR(length=255),
            existing_nullable=False,
        )
