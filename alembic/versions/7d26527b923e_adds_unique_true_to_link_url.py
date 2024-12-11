"""adds unique True to link_url

Revision ID: 7d26527b923e
Revises: cf4bbc3325c5
Create Date: 2024-12-05 22:29:04.732518

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "7d26527b923e"
down_revision = "cf4bbc3325c5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, "groups", ["link_url"])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "groups", type_="unique")
    # ### end Alembic commands ###