"""symphony orchestration tables (agent_session, gate_result, pull_request)

Revision ID: 8a3f1c2d9e10
Revises: 41a0fefb2dc6
Create Date: 2026-05-06 13:30:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8a3f1c2d9e10"
down_revision = "41a0fefb2dc6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "symphony_agent_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.String(length=255), nullable=True),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "completion_tokens", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["run_id"], ["symphony_runs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_symphony_agent_sessions_run_id"),
        "symphony_agent_sessions",
        ["run_id"],
        unique=False,
    )

    op.create_table(
        "symphony_gate_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("gate_name", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("output", sa.Text(), nullable=False, server_default=""),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"], ["symphony_runs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_symphony_gate_results_run_id"),
        "symphony_gate_results",
        ["run_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_symphony_gate_results_gate_name"),
        "symphony_gate_results",
        ["gate_name"],
        unique=False,
    )

    op.create_table(
        "symphony_pull_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=False),
        sa.Column("branch", sa.String(length=255), nullable=False),
        sa.Column("base_branch", sa.String(length=255), nullable=False),
        sa.Column("is_draft", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("body", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"], ["symphony_runs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", name="uq_symphony_pull_requests_run_id"),
    )
    op.create_index(
        op.f("ix_symphony_pull_requests_run_id"),
        "symphony_pull_requests",
        ["run_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_symphony_pull_requests_run_id"),
        table_name="symphony_pull_requests",
    )
    op.drop_table("symphony_pull_requests")
    op.drop_index(
        op.f("ix_symphony_gate_results_gate_name"),
        table_name="symphony_gate_results",
    )
    op.drop_index(
        op.f("ix_symphony_gate_results_run_id"),
        table_name="symphony_gate_results",
    )
    op.drop_table("symphony_gate_results")
    op.drop_index(
        op.f("ix_symphony_agent_sessions_run_id"),
        table_name="symphony_agent_sessions",
    )
    op.drop_table("symphony_agent_sessions")
