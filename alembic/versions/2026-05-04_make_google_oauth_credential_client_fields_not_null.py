"""make google oauth user_google_credential client fields not null

Revision ID: 8c9d2a1b6e54
Revises: 4f0d7dd8a4c1
Create Date: 2026-05-04 17:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8c9d2a1b6e54"
down_revision: Union[str, Sequence[str], None] = "4f0d7dd8a4c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("google_oauth_credentials", recreate="always") as batch:
        batch.alter_column(
            "client_id",
            existing_type=sa.String(length=255),
            nullable=False,
        )
        batch.alter_column(
            "client_secret",
            existing_type=sa.String(length=255),
            nullable=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("google_oauth_credentials", recreate="always") as batch:
        batch.alter_column(
            "client_id",
            existing_type=sa.String(length=255),
            nullable=True,
        )
        batch.alter_column(
            "client_secret",
            existing_type=sa.String(length=255),
            nullable=True,
        )
