import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    from sqlalchemy import Text as Vector

from app.db.database import Base



class Document(Base):
    """
    Document table storing metadata for uploaded PDF files.
    """
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=True, default="default_user")
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False, default="pdf")
    created_at = Column(DateTime, default=datetime.utcnow)

    # One-to-many relationship with chunks
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    """
    DocumentChunk table storing extracted page snippets and 3072-dim embeddings.
    """
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    
    # 3072-dimensional vector column matching gemini-embedding-001
    embedding = Column(Vector(3072), nullable=True)
    
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="chunks")

    def get_metadata(self) -> dict:
        if self.metadata_json:
            try:
                return json.loads(self.metadata_json)
            except Exception:
                return {}
        return {}

    def set_metadata(self, meta_dict: dict):
        self.metadata_json = json.dumps(meta_dict)


from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean


class DecisionAnalysis(Base):
    """
    DecisionAnalysis table storing saved AI decision analysis results, RAG sources, matrix data, and multi-agent metadata.
    """
    __tablename__ = "decision_analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=True, default="default_user")
    problem = Column(Text, nullable=False)
    context = Column(Text, nullable=True, default="")
    constraints = Column(Text, nullable=True, default="")
    analysis = Column(Text, nullable=False)
    request_type = Column(String(50), nullable=False, default="SIMPLE_QUESTION")
    response_depth = Column(String(50), nullable=False, default="concise")
    multi_agent_used = Column(Boolean, default=False)
    agents_json = Column(Text, nullable=True)
    sources_json = Column(Text, nullable=True)
    matrix_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def get_sources(self) -> list:
        if self.sources_json:
            try:
                return json.loads(self.sources_json)
            except Exception:
                return []
        return []

    def set_sources(self, sources_list: list):
        self.sources_json = json.dumps([s.dict() if hasattr(s, 'dict') else s for s in sources_list])

    def get_matrix(self) -> dict | None:
        if self.matrix_json:
            try:
                return json.loads(self.matrix_json)
            except Exception:
                return None
        return None

    def set_matrix(self, matrix_obj):
        if matrix_obj:
            self.matrix_json = json.dumps(matrix_obj.dict() if hasattr(matrix_obj, 'dict') else matrix_obj)
        else:
            self.matrix_json = None

    def get_agents_metadata(self) -> list:
        if self.agents_json:
            try:
                return json.loads(self.agents_json)
            except Exception:
                return []
        return []

    def set_agents_metadata(self, agents_list: list):
        self.agents_json = json.dumps(agents_list)


class User(Base):
    """
    User table storing authenticated accounts, credentials, and OAuth profiles.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    auth_provider = Column(String(50), default="email")  # "email", "google", "github"
    created_at = Column(DateTime, default=datetime.utcnow)


class EmailVerificationOTP(Base):
    """
    EmailVerificationOTP table storing 6-digit email verification codes.
    """
    __tablename__ = "email_verification_otps"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), index=True, nullable=False)
    otp_code = Column(String(6), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)




