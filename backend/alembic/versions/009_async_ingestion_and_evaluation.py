"""Add missing async ingestion and evaluation framework tables: ingestion_jobs, evaluation_runs, evaluation_result_items

Revision ID: 009_async_ingestion_and_evaluation
Revises: 008_ai_control_plane
Create Date: 2026-10-20 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "009_async_ingestion_and_evaluation"
down_revision: Union[str, None] = "008_ai_control_plane"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Ingestion Jobs
    op.create_table(
        "ingestion_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("knowledge_base_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "QUEUED",
                "PROCESSING",
                "COMPLETED",
                "FAILED",
                "CANCELLED",
                name="ingestionjobstatus",
                native_enum=False,
                length=50,
            ),
            nullable=False,
            server_default="QUEUED",
        ),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_stage", sa.String(length=50), nullable=False, server_default="QUEUED"),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["knowledge_base_id"], ["knowledge_bases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ingestion_jobs_id"), "ingestion_jobs", ["id"], unique=False)
    op.create_index(op.f("ix_ingestion_jobs_company_id"), "ingestion_jobs", ["company_id"], unique=False)
    op.create_index(op.f("ix_ingestion_jobs_knowledge_base_id"), "ingestion_jobs", ["knowledge_base_id"], unique=False)
    op.create_index(op.f("ix_ingestion_jobs_document_id"), "ingestion_jobs", ["document_id"], unique=False)
    op.create_index(op.f("ix_ingestion_jobs_status"), "ingestion_jobs", ["status"], unique=False)

    # 2. Evaluation Runs
    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("ai_employee_id", sa.Uuid(), nullable=False),
        sa.Column("knowledge_base_id", sa.Uuid(), nullable=True),
        sa.Column("dataset_name", sa.String(length=100), nullable=False, server_default="golden_dataset"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="PENDING"),
        sa.Column("total_queries", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_baseline", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("duration_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("metrics_summary", sa.JSON(), nullable=False),
        sa.Column("comparison_to_baseline", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ai_employee_id"], ["ai_employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["knowledge_base_id"], ["knowledge_bases.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_evaluation_runs_id"), "evaluation_runs", ["id"], unique=False)
    op.create_index(op.f("ix_evaluation_runs_company_id"), "evaluation_runs", ["company_id"], unique=False)
    op.create_index(op.f("ix_evaluation_runs_ai_employee_id"), "evaluation_runs", ["ai_employee_id"], unique=False)
    op.create_index(op.f("ix_evaluation_runs_knowledge_base_id"), "evaluation_runs", ["knowledge_base_id"], unique=False)
    op.create_index(op.f("ix_evaluation_runs_dataset_name"), "evaluation_runs", ["dataset_name"], unique=False)
    op.create_index(op.f("ix_evaluation_runs_status"), "evaluation_runs", ["status"], unique=False)
    op.create_index(op.f("ix_evaluation_runs_is_baseline"), "evaluation_runs", ["is_baseline"], unique=False)

    # 3. Evaluation Result Items
    op.create_table(
        "evaluation_result_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evaluation_run_id", sa.Uuid(), nullable=False),
        sa.Column("query_id", sa.String(length=50), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False, server_default="general"),
        sa.Column("answerable", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("expected_chunk_ids", sa.JSON(), nullable=False),
        sa.Column("reference_answer", sa.Text(), nullable=True),
        sa.Column("retrieved_chunk_ids", sa.JSON(), nullable=False),
        sa.Column("retrieval_scores", sa.JSON(), nullable=False),
        sa.Column("generated_answer", sa.Text(), nullable=True),
        sa.Column("citations", sa.JSON(), nullable=False),
        sa.Column("recall_at_1", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("recall_at_3", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("recall_at_5", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("precision_at_1", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("precision_at_3", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("precision_at_5", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("reciprocal_rank", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("ndcg_at_5", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("faithfulness", sa.Float(), nullable=True),
        sa.Column("answer_relevance", sa.Float(), nullable=True),
        sa.Column("refusal_correct", sa.Boolean(), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("token_usage", sa.JSON(), nullable=True),
        sa.Column("judge_reasoning", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["evaluation_run_id"], ["evaluation_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_evaluation_result_items_id"), "evaluation_result_items", ["id"], unique=False)
    op.create_index(op.f("ix_evaluation_result_items_evaluation_run_id"), "evaluation_result_items", ["evaluation_run_id"], unique=False)
    op.create_index(op.f("ix_evaluation_result_items_query_id"), "evaluation_result_items", ["query_id"], unique=False)
    op.create_index(op.f("ix_evaluation_result_items_category"), "evaluation_result_items", ["category"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_evaluation_result_items_category"), table_name="evaluation_result_items")
    op.drop_index(op.f("ix_evaluation_result_items_query_id"), table_name="evaluation_result_items")
    op.drop_index(op.f("ix_evaluation_result_items_evaluation_run_id"), table_name="evaluation_result_items")
    op.drop_index(op.f("ix_evaluation_result_items_id"), table_name="evaluation_result_items")
    op.drop_table("evaluation_result_items")

    op.drop_index(op.f("ix_evaluation_runs_is_baseline"), table_name="evaluation_runs")
    op.drop_index(op.f("ix_evaluation_runs_status"), table_name="evaluation_runs")
    op.drop_index(op.f("ix_evaluation_runs_dataset_name"), table_name="evaluation_runs")
    op.drop_index(op.f("ix_evaluation_runs_knowledge_base_id"), table_name="evaluation_runs")
    op.drop_index(op.f("ix_evaluation_runs_ai_employee_id"), table_name="evaluation_runs")
    op.drop_index(op.f("ix_evaluation_runs_company_id"), table_name="evaluation_runs")
    op.drop_index(op.f("ix_evaluation_runs_id"), table_name="evaluation_runs")
    op.drop_table("evaluation_runs")

    op.drop_index(op.f("ix_ingestion_jobs_status"), table_name="ingestion_jobs")
    op.drop_index(op.f("ix_ingestion_jobs_document_id"), table_name="ingestion_jobs")
    op.drop_index(op.f("ix_ingestion_jobs_knowledge_base_id"), table_name="ingestion_jobs")
    op.drop_index(op.f("ix_ingestion_jobs_company_id"), table_name="ingestion_jobs")
    op.drop_index(op.f("ix_ingestion_jobs_id"), table_name="ingestion_jobs")
    op.drop_table("ingestion_jobs")
