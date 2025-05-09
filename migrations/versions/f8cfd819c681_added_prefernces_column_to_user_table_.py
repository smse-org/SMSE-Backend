"""Added prefernces column to user table and upload_date and content_size to content table

Revision ID: f8cfd819c681
Revises: 070414f2e1a7
Create Date: 2025-04-05 23:47:01.331327

"""
from alembic import op
import sqlalchemy as sa
import pgvector


# revision identifiers, used by Alembic.
revision = 'f8cfd819c681'
down_revision = '070414f2e1a7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('contents', schema=None) as batch_op:
        batch_op.add_column(sa.Column('upload_date', sa.DateTime(), server_default=sa.text('now()'), nullable=False))
        batch_op.add_column(sa.Column('content_size', sa.Integer(), nullable=False))

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('preferences', sa.JSON(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('preferences')

    with op.batch_alter_table('contents', schema=None) as batch_op:
        batch_op.drop_column('content_size')
        batch_op.drop_column('upload_date')

    # ### end Alembic commands ###
