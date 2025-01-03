"""set unique to false for embedding.model_id

Revision ID: 9ec95ec6fcd3
Revises: 3a61afcf31ae
Create Date: 2024-12-22 20:05:33.206200

"""
from alembic import op
import sqlalchemy as sa
import pgvector


# revision identifiers, used by Alembic.
revision = '9ec95ec6fcd3'
down_revision = '3a61afcf31ae'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('embeddings', schema=None) as batch_op:
        batch_op.drop_index('ix_embeddings_model_id')
        batch_op.create_index(batch_op.f('ix_embeddings_model_id'), ['model_id'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('embeddings', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_embeddings_model_id'))
        batch_op.create_index('ix_embeddings_model_id', ['model_id'], unique=True)

    # ### end Alembic commands ###
