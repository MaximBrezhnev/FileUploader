"""empty message

Revision ID: 61a42d300cd1
Revises: ba57f15d1450
Create Date: 2024-08-29 14:36:17.794541

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '61a42d300cd1'
down_revision: Union[str, None] = 'ba57f15d1450'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('file_filename_key', 'file', type_='unique')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('file_filename_key', 'file', ['filename'])
    # ### end Alembic commands ###
