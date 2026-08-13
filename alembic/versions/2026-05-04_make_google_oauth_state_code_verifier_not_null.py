"""make google oauth state code_verifier not null

Revision ID: 4f0d7dd8a4c1
Revises: f205227fcace
Create Date: 2026-05-04 16:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4f0d7dd8a4c1"
down_revision: Union[str, Sequence[str], None] = "f205227fcace"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("google_oauth_states", recreate="always") as batch:
        batch.alter_column(
            "code_verifier",
            existing_type=sa.Text(),
            nullable=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("google_oauth_states", recreate="always") as batch:
        batch.alter_column(
            "code_verifier",
            existing_type=sa.Text(),
            nullable=True,
        )
