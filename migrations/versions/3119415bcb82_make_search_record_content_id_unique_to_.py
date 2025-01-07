"""make search_record.content_id unique to flase and rename search_record.query to query_relation to avoid conflict

Revision ID: 3119415bcb82
Revises: da28b66f399d
Create Date: 2025-01-07 23:07:24.655076

"""
from alembic import op
import sqlalchemy as sa
import pgvector


# revision identifiers, used by Alembic.
revision = '3119415bcb82'
down_revision = 'da28b66f399d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('search_records', schema=None) as batch_op:
        batch_op.drop_index('ix_search_records_content_id')
        batch_op.create_index(batch_op.f('ix_search_records_content_id'), ['content_id'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('search_records', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_search_records_content_id'))
        batch_op.create_index('ix_search_records_content_id', ['content_id'], unique=True)

    # ### end Alembic commands ###
