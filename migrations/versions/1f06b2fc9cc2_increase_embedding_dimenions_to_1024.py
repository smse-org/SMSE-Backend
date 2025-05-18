"""Increase embedding dimenions to 1024

Revision ID: 1f06b2fc9cc2
Revises:
Create Date: 2025-05-18 22:37:51.744173

"""

from alembic import op
import sqlalchemy as sa
import pgvector


# revision identifiers, used by Alembic.
revision = "1f06b2fc9cc2"
down_revision = "3b251aa30fc4"
branch_labels = None
depends_on = None


def upgrade():
    # Drop the old vector column
    op.drop_column("embeddings", "vector")
    # Add the new vector column with 1024 dimensions
    op.add_column(
        "embeddings",
        sa.Column("vector", pgvector.sqlalchemy.Vector(1024), nullable=True),
    )
    # Note: You can set nullable=False in a later migration after recomputing embeddings


def downgrade():
    # Drop the 1024-dim vector column
    op.drop_column("embeddings", "vector")
    # Add the old vector column with 328 dimensions
    op.add_column(
        "embeddings",
        sa.Column("vector", pgvector.sqlalchemy.Vector(328), nullable=True),
    )
