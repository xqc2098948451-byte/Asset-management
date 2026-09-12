"""Create the Data Collection schema and approved internal tables."""

from sqlalchemy import text

from alembic import op
from asset_management.data_collection.adapters.database.schema import SCHEMA, metadata

revision = "0001_data_collection"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{SCHEMA}"'))
    metadata.create_all(bind, checkfirst=False)


def downgrade() -> None:
    bind = op.get_bind()
    metadata.drop_all(bind, checkfirst=True)
    bind.execute(text(f'DROP SCHEMA IF EXISTS "{SCHEMA}"'))
