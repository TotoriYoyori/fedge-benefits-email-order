"""remove_google_oauth_and_non_user_tables

Revision ID: 10d13104bba8
Revises: 5093b00cea81
Create Date: 2026-04-17 18:43:56.232528

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '10d13104bba8'
down_revision: Union[str, Sequence[str], None] = '5093b00cea81'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_table("google_oauth_states")
    op.drop_table("google_oauth_credentials")


def downgrade() -> None:
    """Downgrade schema."""
    # Re-creating tables as they were in previous migrations if needed
    sa_datetime = sa.DateTime(timezone=True)
    op.create_table(
        "google_oauth_credentials",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("app_user_id", sa.String(length=255), nullable=False),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("token_uri", sa.String(length=255), nullable=False),
        sa.Column("client_id", sa.String(length=255), nullable=True),
        sa.Column("client_secret", sa.String(length=255), nullable=True),
        sa.Column("scopes", sa.Text(), nullable=False),
        sa.Column("expiry", sa_datetime, nullable=True),
        sa.Column("email_address", sa.String(length=255), nullable=True),
        sa.Column("created_time", sa_datetime, nullable=False),
        sa.Column("updated_time", sa_datetime, nullable=False),
    )
    op.create_index("google_oauth_credentials_app_user_id_idx", "google_oauth_credentials", ["app_user_id"], unique=True)

    op.create_table(
        "google_oauth_states",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("state", sa.String(length=255), nullable=False),
        sa.Column("app_user_id", sa.String(length=255), nullable=False),
        sa.Column("code_verifier", sa.Text(), nullable=True),
        sa.Column("created_time", sa_datetime, nullable=False),
    )
    op.create_index("google_oauth_states_state_idx", "google_oauth_states", ["state"], unique=True)
    op.create_index("google_oauth_states_app_user_id_idx", "google_oauth_states", ["app_user_id"], unique=False)
