"""rename_date_and_at_columns_to_time_and_date_suffix

Revision ID: e95bc0011d68
Revises: fb433e7d7823
Create Date: 2026-04-15 13:01:59.179259

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e95bc0011d68'
down_revision: Union[str, Sequence[str], None] = 'fb433e7d7823'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Renaming columns instead of dropping and adding to preserve data.
    op.alter_column('google_oauth_credentials', 'created_at', new_column_name='created_time')
    op.alter_column('google_oauth_credentials', 'updated_at', new_column_name='updated_time')
    op.alter_column('google_oauth_states', 'created_at', new_column_name='created_time')
    op.alter_column('orders', 'date', new_column_name='order_date')
    op.alter_column('users', 'registration_date', new_column_name='registration_time')


def downgrade() -> None:
    """Downgrade schema."""
    # Reversing the renaming.
    op.alter_column('google_oauth_credentials', 'created_time', new_column_name='created_at')
    op.alter_column('google_oauth_credentials', 'updated_time', new_column_name='updated_at')
    op.alter_column('google_oauth_states', 'created_time', new_column_name='created_at')
    op.alter_column('orders', 'order_date', new_column_name='date')
    op.alter_column('users', 'registration_time', new_column_name='registration_date')
