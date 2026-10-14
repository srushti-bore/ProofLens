"""Initial schema creation for ProofLens AI

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-10-14 12:00:00.000000 UTC

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # Ensure pgvector extension on PostgreSQL
    if is_postgres:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 1. users
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1' if not is_postgres else 'true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # 2. workspaces
    op.create_table(
        'workspaces',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_workspaces_id', 'workspaces', ['id'])
    op.create_index('ix_workspaces_owner_id', 'workspaces', ['owner_id'])

    # 3. workspace_members
    op.create_table(
        'workspace_members',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='member'),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('workspace_id', 'user_id', name='uq_workspace_user'),
    )
    op.create_index('ix_workspace_members_id', 'workspace_members', ['id'])
    op.create_index('ix_workspace_members_workspace_id', 'workspace_members', ['workspace_id'])
    op.create_index('ix_workspace_members_user_id', 'workspace_members', ['user_id'])

    # 4. documents
    op.create_table(
        'documents',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_hash', sa.String(length=64), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False, server_default='application/pdf'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='queued'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('page_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('storage_path', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_documents_id', 'documents', ['id'])
    op.create_index('ix_documents_workspace_id', 'documents', ['workspace_id'])
    op.create_index('ix_documents_file_hash', 'documents', ['file_hash'])
    op.create_index('ix_documents_status', 'documents', ['status'])

    # 5. document_pages
    op.create_table(
        'document_pages',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('document_id', sa.String(length=36), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('text_content', sa.Text(), nullable=False),
        sa.Column('char_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('document_id', 'page_number', name='uq_doc_page'),
    )
    op.create_index('ix_document_pages_id', 'document_pages', ['id'])
    op.create_index('ix_document_pages_document_id', 'document_pages', ['document_id'])
    op.create_index('ix_document_pages_page_number', 'document_pages', ['page_number'])

    # 6. document_chunks
    embedding_type = Vector(768) if is_postgres else sa.JSON()
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('document_id', sa.String(length=36), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', embedding_type, nullable=False),
        sa.Column('char_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_document_chunks_id', 'document_chunks', ['id'])
    op.create_index('ix_document_chunks_document_id', 'document_chunks', ['document_id'])
    op.create_index('ix_document_chunks_workspace_id', 'document_chunks', ['workspace_id'])
    op.create_index('ix_document_chunks_page_number', 'document_chunks', ['page_number'])

    # 7. conversations
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_conversations_id', 'conversations', ['id'])
    op.create_index('ix_conversations_workspace_id', 'conversations', ['workspace_id'])
    op.create_index('ix_conversations_user_id', 'conversations', ['user_id'])

    # 8. query_runs
    op.create_table(
        'query_runs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('conversation_id', sa.String(length=36), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=True),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('execution_time_ms', sa.Float(), nullable=False, server_default='0.0'),
    )
    op.create_index('ix_query_runs_id', 'query_runs', ['id'])
    op.create_index('ix_query_runs_workspace_id', 'query_runs', ['workspace_id'])
    op.create_index('ix_query_runs_user_id', 'query_runs', ['user_id'])
    op.create_index('ix_query_runs_conversation_id', 'query_runs', ['conversation_id'])

    # 9. answers
    op.create_table(
        'answers',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('query_run_id', sa.String(length=36), sa.ForeignKey('query_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('answer_text', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='supported'),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('abstention_reason', sa.Text(), nullable=True),
        sa.Column('retrieved_chunks_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_answers_id', 'answers', ['id'])
    op.create_index('ix_answers_query_run_id', 'answers', ['query_run_id'], unique=True)

    # 10. citations
    op.create_table(
        'citations',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('answer_id', sa.String(length=36), sa.ForeignKey('answers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_id', sa.String(length=36), sa.ForeignKey('document_chunks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_id', sa.String(length=36), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('excerpt', sa.Text(), nullable=False),
        sa.Column('is_validated', sa.Boolean(), nullable=False, server_default=sa.text('1' if not is_postgres else 'true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_citations_id', 'citations', ['id'])
    op.create_index('ix_citations_answer_id', 'citations', ['answer_id'])
    op.create_index('ix_citations_chunk_id', 'citations', ['chunk_id'])
    op.create_index('ix_citations_document_id', 'citations', ['document_id'])

    # 11. claim_verifications
    op.create_table(
        'claim_verifications',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('claim_text', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_claim_verifications_id', 'claim_verifications', ['id'])
    op.create_index('ix_claim_verifications_workspace_id', 'claim_verifications', ['workspace_id'])
    op.create_index('ix_claim_verifications_user_id', 'claim_verifications', ['user_id'])
    op.create_index('ix_claim_verifications_status', 'claim_verifications', ['status'])

    # 12. claim_citations
    op.create_table(
        'claim_citations',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('claim_verification_id', sa.String(length=36), sa.ForeignKey('claim_verifications.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_id', sa.String(length=36), sa.ForeignKey('document_chunks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_id', sa.String(length=36), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('excerpt', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_claim_citations_id', 'claim_citations', ['id'])
    op.create_index('ix_claim_citations_claim_verification_id', 'claim_citations', ['claim_verification_id'])
    op.create_index('ix_claim_citations_chunk_id', 'claim_citations', ['chunk_id'])
    op.create_index('ix_claim_citations_document_id', 'claim_citations', ['document_id'])


def downgrade() -> None:
    op.drop_table('claim_citations')
    op.drop_table('claim_verifications')
    op.drop_table('citations')
    op.drop_table('answers')
    op.drop_table('query_runs')
    op.drop_table('conversations')
    op.drop_table('document_chunks')
    op.drop_table('document_pages')
    op.drop_table('documents')
    op.drop_table('workspace_members')
    op.drop_table('workspaces')
    op.drop_table('users')
