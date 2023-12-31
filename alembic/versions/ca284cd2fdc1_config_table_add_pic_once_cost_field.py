"""config table add pic_once_cost field

Revision ID: ca284cd2fdc1
Revises: 
Create Date: 2023-10-07 15:49:33.154120

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'ca284cd2fdc1'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('config', sa.Column('pic_once_cost', sa.Float(precision=2), nullable=False, comment='一次发送图文消耗的 USDT'))
    op.alter_column('config', 'once_cost',
               existing_type=mysql.FLOAT(),
               comment='一次发送普通供需消耗的 USDT',
               existing_comment='一次发送消耗的 USDT',
               existing_nullable=False)
    op.create_foreign_key(None, 'msgs', 'users', ['user_id'], ['user_id'])
    op.create_foreign_key(None, 'pays', 'users', ['user_id'], ['user_id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'pays', type_='foreignkey')
    op.drop_constraint(None, 'msgs', type_='foreignkey')
    op.alter_column('config', 'once_cost',
               existing_type=mysql.FLOAT(),
               comment='一次发送消耗的 USDT',
               existing_comment='一次发送普通供需消耗的 USDT',
               existing_nullable=False)
    op.drop_column('config', 'pic_once_cost')
    # ### end Alembic commands ###
