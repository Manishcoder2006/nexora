import uuid
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

import app.models  # register all models with Base.metadata
from app.models.base import Base
from app.models.company import Company
from app.models.user import User
from app.models.membership import Membership, MembershipRole
from app.models.ai_employee import AIEmployee, AIEmployeeStatus
from app.models.knowledge_base import KnowledgeBase, KnowledgeBaseStatus
from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole


@pytest_asyncio.fixture(scope="function")
async def test_session():
    """Isolated in-memory async SQLite engine with StaticPool for model testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    async with session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_all_models_registered_in_metadata():
    """Verify that all core tables exist in Base.metadata."""
    table_names = set(Base.metadata.tables.keys())
    expected_tables = {
        "users", "companies", "memberships", "ai_employees",
        "knowledge_bases", "documents", "document_chunks",
        "ai_employee_knowledge_bases", "ai_employee_tools",
        "conversations", "messages", "public_chat_sessions",
        "public_usage_events", "orders", "leads", "support_tickets",
        "pending_tool_actions", "tool_executions", "trace_summaries",
        "audit_events", "usage_budgets", "usage_ledger_entries",
        "evaluation_runs", "evaluation_result_items",
        "playground_sessions", "playground_messages", "voice_sessions"
    }
    for table in expected_tables:
        assert table in table_names, f"Table '{table}' missing from Base.metadata"


@pytest.mark.asyncio
async def test_tenant_and_user_creation(test_session: AsyncSession):
    """Verify Company, User, and Membership creation with role OWNER."""
    company = Company(
        id=uuid.uuid4(),
        name="Nexora Inc",
        slug="nexora-inc"
    )
    user = User(
        id=uuid.uuid4(),
        email="founder@nexora.ai",
        hashed_password="hashed_pw_test",
        full_name="Nexora Founder"
    )
    test_session.add_all([company, user])
    await test_session.flush()

    membership = Membership(
        id=uuid.uuid4(),
        user_id=user.id,
        company_id=company.id,
        role=MembershipRole.OWNER
    )
    test_session.add(membership)
    await test_session.commit()

    # Query back
    result = await test_session.execute(select(Company).where(Company.slug == "nexora-inc"))
    fetched_company = result.scalar_one()
    assert fetched_company.name == "Nexora Inc"

    mem_result = await test_session.execute(select(Membership).where(Membership.company_id == company.id))
    fetched_mem = mem_result.scalar_one()
    assert fetched_mem.role == MembershipRole.OWNER


@pytest.mark.asyncio
async def test_ai_employee_and_knowledge_base_creation(test_session: AsyncSession):
    """Verify AIEmployee and KnowledgeBase creation with foreign keys."""
    company = Company(id=uuid.uuid4(), name="Test Tenant", slug="test-tenant")
    test_session.add(company)
    await test_session.flush()

    employee = AIEmployee(
        id=uuid.uuid4(),
        company_id=company.id,
        name="Support Agent",
        role="Customer Service Representative",
        system_prompt="You are a helpful customer service AI agent for Nexora.",
        status=AIEmployeeStatus.ACTIVE,
        public_id="emp_pub_test_123"
    )
    kb = KnowledgeBase(
        id=uuid.uuid4(),
        company_id=company.id,
        name="Customer FAQ",
        status=KnowledgeBaseStatus.ACTIVE
    )
    test_session.add_all([employee, kb])
    await test_session.flush()

    doc = Document(
        id=uuid.uuid4(),
        knowledge_base_id=kb.id,
        company_id=company.id,
        filename="faq.pdf",
        original_filename="faq.pdf",
        file_type="pdf",
        mime_type="application/pdf",
        file_size=1024,
        storage_path="/uploads/faq.pdf",
        status=DocumentStatus.PROCESSED
    )
    test_session.add(doc)
    await test_session.flush()

    chunk = DocumentChunk(
        id=uuid.uuid4(),
        document_id=doc.id,
        knowledge_base_id=kb.id,
        company_id=company.id,
        chunk_index=0,
        content="Nexora provides enterprise AI employee solutions.",
        token_count=10,
        chunk_metadata={"source": "faq.pdf"}
    )
    test_session.add(chunk)
    await test_session.commit()

    # Verify query
    chunk_res = await test_session.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc.id))
    fetched_chunk = chunk_res.scalar_one()
    assert fetched_chunk.chunk_index == 0
    assert fetched_chunk.company_id == company.id


@pytest.mark.asyncio
async def test_conversation_and_messages(test_session: AsyncSession):
    """Verify Conversation and Message persistence with citations and company_id."""
    company = Company(id=uuid.uuid4(), name="Conv Tenant", slug="conv-tenant")
    test_session.add(company)
    await test_session.flush()

    employee = AIEmployee(
        id=uuid.uuid4(),
        company_id=company.id,
        name="Assistant",
        role="AI Worker",
        system_prompt="Assistant prompt",
        status=AIEmployeeStatus.ACTIVE,
        public_id="emp_pub_conv_123"
    )
    test_session.add(employee)
    await test_session.flush()

    conv = Conversation(
        id=uuid.uuid4(),
        company_id=company.id,
        ai_employee_id=employee.id,
        title="Order Inquiry Session"
    )
    test_session.add(conv)
    await test_session.flush()

    msg1 = Message(
        id=uuid.uuid4(),
        conversation_id=conv.id,
        company_id=company.id,
        role=MessageRole.USER,
        content="Where is my order #12345?"
    )
    msg2 = Message(
        id=uuid.uuid4(),
        conversation_id=conv.id,
        company_id=company.id,
        role=MessageRole.ASSISTANT,
        content="Your order #12345 has shipped.",
        citations=[{"doc_id": "doc_1", "score": 0.95}]
    )
    test_session.add_all([msg1, msg2])
    await test_session.commit()

    messages = (await test_session.execute(
        select(Message).where(Message.conversation_id == conv.id).order_by(Message.created_at)
    )).scalars().all()

    assert len(messages) == 2
    assert messages[0].role == MessageRole.USER
    assert messages[1].role == MessageRole.ASSISTANT
    assert len(messages[1].citations) == 1
