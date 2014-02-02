"""add no-show

Revision ID: 31fd29bb27c7
Revises: 1a372f700faf
Create Date: 2014-02-02 21:16:21.023249

"""

# revision identifiers, used by Alembic.
revision = '31fd29bb27c7'
down_revision = '1a372f700faf'

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('queue_items', sa.Column('no_show', sa.Boolean))

def downgrade():
    op.drop_column('queue_items', 'no_show')

