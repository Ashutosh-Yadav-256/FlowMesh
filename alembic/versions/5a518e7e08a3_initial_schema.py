"""initial_schema

Revision ID: 5a518e7e08a3
Revises: 
Create Date: 2026-09-22 12:56:40.470248

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '5a518e7e08a3'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    pass



def downgrade() -> None:

    pass
