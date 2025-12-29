from sqlalchemy import DateTime, ForeignKey, Numeric, Integer, String, Text, BigInteger, Boolean, JSON, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, validates
from sqlalchemy_utils import URLType
from datetime import datetime
from sqlalchemy.sql import func
import re
import enum


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class UserType(enum.Enum):
    ADMIN = "Admin"
    STUDENT = "Student"


class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=True)
    phone: Mapped[str] = mapped_column(String(13), nullable=True, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    language: Mapped[str] = mapped_column(String(2), nullable=False, default="uz")
    address: Mapped[str] = mapped_column(String(150), nullable=True)
    lat: Mapped[float] = mapped_column(Numeric(9, 6), nullable=True)
    lon: Mapped[float] = mapped_column(Numeric(9, 6), nullable=True)


class Channel(Base):
    __tablename__ = 'channel'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(BigInteger)


class AI_Token(Base):
    __tablename__ = 'ai_token'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(150), nullable=True)
    token: Mapped[str] = mapped_column(String(150), nullable=True)
    count: Mapped[int] = mapped_column(BigInteger, default=0)