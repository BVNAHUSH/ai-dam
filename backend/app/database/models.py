from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class Asset(Base):
    __tablename__ = "assets"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # ---------------------------------------------------------
    # FILE INFORMATION
    # ---------------------------------------------------------

    file_path = Column(
        Text,
        nullable=False,
        unique=True,
        index=True,
    )

    filename = Column(
        String(500),
        nullable=False,
        index=True,
    )

    file_type = Column(
        String(50),
        nullable=False,
        index=True,
    )

    mime_type = Column(
        String(100),
    )

    file_size = Column(
        Integer,
        nullable=False,
    )

    sha256 = Column(
        String(64),
        nullable=False,
        index=True,
    )

    modified_time = Column(
        Float,
        nullable=False,
    )

    # ---------------------------------------------------------
    # MEDIA METADATA
    # ---------------------------------------------------------

    width = Column(Integer)

    height = Column(Integer)

    duration = Column(Float)

    # ---------------------------------------------------------
    # AI / CONTENT INFORMATION
    # ---------------------------------------------------------

    description = Column(Text)

    extracted_text = Column(Text)

    objects = Column(Text)

    activities = Column(Text)

    topics = Column(Text)

    # ---------------------------------------------------------
    # EMBEDDING INFORMATION
    # ---------------------------------------------------------

    embedding_id = Column(
        String(200)
    )

    embedding = Column(
        LargeBinary
    )

    embedding_status = Column(
        String(30),
        nullable=False,
        default="pending",
        index=True,
    )

    embedding_model = Column(
        String(100)
    )

    embedding_dimension = Column(
        Integer
    )

    # ---------------------------------------------------------
    # PROCESSING STATUS
    # ---------------------------------------------------------

    status = Column(
        String(30),
        nullable=False,
        default="pending",
        index=True,
    )

    error_message = Column(
        Text
    )

    # ---------------------------------------------------------
    # TIMESTAMPS
    # ---------------------------------------------------------

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
class PDFChunk(Base):
    __tablename__ = "pdf_chunks"

    id = Column(Integer, primary_key=True, index=True)

    asset_id = Column(
        Integer,
        nullable=False,
        index=True,
    )

    page_number = Column(
        Integer,
        nullable=False,
        index=True,
    )

    chunk_index = Column(
        Integer,
        nullable=False,
    )

    text = Column(
        Text,
        nullable=False,
    )

    embedding = Column(
        LargeBinary,
    )

    embedding_status = Column(
        String(30),
        nullable=False,
        default="pending",
        index=True,
    )

    embedding_model = Column(
        String(100),
    )

    embedding_dimension = Column(
        Integer,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )