"""added youtube link

Revision ID: 1a372f700faf
Revises: 5fc6ea4be3d
Create Date: 2013-11-02 20:37:52.118635

"""

# revision identifiers, used by Alembic.
revision = '1a372f700faf'
down_revision = '5fc6ea4be3d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('urlsforitems', sa.Column('youtube_url', sa.String))

def downgrade():
    op.drop_column('urlsforitems', 'youtube_url')

