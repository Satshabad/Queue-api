"""add claimed column

Revision ID: 5fc6ea4be3d
Revises: None
Create Date: 2013-09-15 18:21:03.726098

"""

# revision identifiers, used by Alembic.
revision = '5fc6ea4be3d'
down_revision = '2bc40e473a33'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('users', sa.Column('claimed', sa.Boolean))


def downgrade():
    op.drop_column('users', 'claimed')
