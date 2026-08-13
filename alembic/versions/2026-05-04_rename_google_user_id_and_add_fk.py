"""rename google user_id and add fk

Revision ID: ab31512d58b8
Revises: 62c7835dbeb7
Create Date: 2026-05-04 13:10:53.233125

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ab31512d58b8'
down_revision: Union[str, Sequence[str], None] = '62c7835dbeb7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("DROP TABLE IF EXISTS _alembic_tmp_google_oauth_credentials")
    op.execute("DROP TABLE IF EXISTS _alembic_tmp_google_oauth_states")

    op.create_table(
        "_alembic_tmp_google_oauth_credentials",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("token_uri", sa.String(length=255), nullable=False),
        sa.Column("client_id", sa.String(length=255), nullable=True),
        sa.Column("client_secret", sa.String(length=255), nullable=True),
        sa.Column("scopes", sa.Text(), nullable=False),
        sa.Column("expiry", sa.DateTime(timezone=True), nullable=True),
        sa.Column("email_address", sa.String(length=255), nullable=True),
        sa.Column("created_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_time", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("google_oauth_credentials_user_id_fkey")),
        sa.PrimaryKeyConstraint("id", name=op.f("google_oauth_credentials_pkey")),
    )
    op.execute(
        """
        INSERT INTO _alembic_tmp_google_oauth_credentials (
            id, user_id, access_token, refresh_token, token_uri, client_id,
            client_secret, scopes, expiry, email_address, created_time, updated_time
        )
        SELECT
            id, app_user_id, access_token, refresh_token, token_uri, client_id,
            client_secret, scopes, expiry, email_address, created_time, updated_time
        FROM google_oauth_credentials
        """
    )
    op.drop_index(
        op.f("google_oauth_credentials_app_user_id_idx"),
        table_name="google_oauth_credentials",
    )
    op.drop_table("google_oauth_credentials")
    op.rename_table(
        "_alembic_tmp_google_oauth_credentials",
        "google_oauth_credentials",
    )
    op.create_index(
        op.f("google_oauth_credentials_user_id_idx"),
        "google_oauth_credentials",
        ["user_id"],
        unique=True,
    )

    op.create_table(
        "_alembic_tmp_google_oauth_states",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("code_verifier", sa.Text(), nullable=True),
        sa.Column("created_time", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("google_oauth_states_user_id_fkey")),
        sa.PrimaryKeyConstraint("id", name=op.f("google_oauth_states_pkey")),
    )
    op.execute(
        """
        INSERT INTO _alembic_tmp_google_oauth_states (
            id, state, user_id, code_verifier, created_time
        )
        SELECT
            id, state, app_user_id, code_verifier, created_time
        FROM google_oauth_states
        """
    )
    op.drop_index(
        op.f("google_oauth_states_app_user_id_idx"),
        table_name="google_oauth_states",
    )
    op.drop_index(
        op.f("google_oauth_states_state_idx"),
        table_name="google_oauth_states",
    )
    op.drop_table("google_oauth_states")
    op.rename_table("_alembic_tmp_google_oauth_states", "google_oauth_states")
    op.create_index(
        op.f("google_oauth_states_user_id_idx"),
        "google_oauth_states",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("google_oauth_states_state_idx"),
        "google_oauth_states",
        ["state"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE IF EXISTS _alembic_tmp_google_oauth_credentials")
    op.execute("DROP TABLE IF EXISTS _alembic_tmp_google_oauth_states")

    op.create_table(
        "_alembic_tmp_google_oauth_states",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(length=255), nullable=False),
        sa.Column("app_user_id", sa.Integer(), nullable=False),
        sa.Column("code_verifier", sa.Text(), nullable=True),
        sa.Column("created_time", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("google_oauth_states_pkey")),
    )
    op.execute(
        """
        INSERT INTO _alembic_tmp_google_oauth_states (
            id, state, app_user_id, code_verifier, created_time
        )
        SELECT
            id, state, user_id, code_verifier, created_time
        FROM google_oauth_states
        """
    )
    op.drop_index(
        op.f("google_oauth_states_user_id_idx"),
        table_name="google_oauth_states",
    )
    op.drop_index(
        op.f("google_oauth_states_state_idx"),
        table_name="google_oauth_states",
    )
    op.drop_table("google_oauth_states")
    op.rename_table("_alembic_tmp_google_oauth_states", "google_oauth_states")
    op.create_index(
        op.f("google_oauth_states_app_user_id_idx"),
        "google_oauth_states",
        ["app_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("google_oauth_states_state_idx"),
        "google_oauth_states",
        ["state"],
        unique=True,
    )

    op.create_table(
        "_alembic_tmp_google_oauth_credentials",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("app_user_id", sa.Integer(), nullable=False),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("token_uri", sa.String(length=255), nullable=False),
        sa.Column("client_id", sa.String(length=255), nullable=True),
        sa.Column("client_secret", sa.String(length=255), nullable=True),
        sa.Column("scopes", sa.Text(), nullable=False),
        sa.Column("expiry", sa.DateTime(timezone=True), nullable=True),
        sa.Column("email_address", sa.String(length=255), nullable=True),
        sa.Column("created_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_time", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("google_oauth_credentials_pkey")),
    )
    op.execute(
        """
        INSERT INTO _alembic_tmp_google_oauth_credentials (
            id, app_user_id, access_token, refresh_token, token_uri, client_id,
            client_secret, scopes, expiry, email_address, created_time, updated_time
        )
        SELECT
            id, user_id, access_token, refresh_token, token_uri, client_id,
            client_secret, scopes, expiry, email_address, created_time, updated_time
        FROM google_oauth_credentials
        """
    )
    op.drop_index(
        op.f("google_oauth_credentials_user_id_idx"),
        table_name="google_oauth_credentials",
    )
    op.drop_table("google_oauth_credentials")
    op.rename_table(
        "_alembic_tmp_google_oauth_credentials",
        "google_oauth_credentials",
    )
    op.create_index(
        op.f("google_oauth_credentials_app_user_id_idx"),
        "google_oauth_credentials",
        ["app_user_id"],
        unique=True,
    )
