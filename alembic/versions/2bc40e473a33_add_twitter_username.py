"""add twitter username to User

Revision ID: 2bc40e473a33
Revises: None
Create Date: 2013-06-15 16:20:47.790063

"""

# revision identifiers, used by Alembic.
revision = '2bc40e473a33'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('users', sa.Column('twitter_name', sa.String))

def downgrade():
    op.drop_column('users', 'twitter_name')
