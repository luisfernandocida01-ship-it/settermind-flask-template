# models.py
from sqlalchemy import Boolean, Column, String, DateTime, JSON, ForeignKey, Integer
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
from sqlalchemy import Text
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    analyses = relationship('Analysis', back_populates='owner')
    strategies = relationship('Strategy', back_populates='owner')
    outbox_items = relationship("OutboxItem", back_populates="owner", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="owner", cascade="all, delete-orphan")
    api_keys = relationship('ApiKey', back_populates='owner', cascade="all, delete-orphan")

class ApiKey(Base):
    __tablename__ = 'api_keys'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key_hash = Column(String(64), unique=True, index=True, nullable=False) # SHA-256
    user_email = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    monthly_limit = Column(Integer, default=1000)
    current_usage = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    owner = relationship('User', back_populates='api_keys')

class Analysis(Base):
    __tablename__ = 'analyses'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_url = Column(String, nullable=True, default='')
    created_at = Column(DateTime, default=datetime.utcnow)
    result_data = Column(JSON, nullable=False)
    owner_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    owner = relationship('User', back_populates='analyses')

class Strategy(Base):
    __tablename__ = 'strategies'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    niche = Column(String, nullable=False)
    avatar = Column(String, nullable=False)
    keywords = Column(JSON, nullable=False)
    hashtags = Column(JSON, nullable=False)
    saved_posts = Column(JSON, default=list)  # <-- Almacén de posts calificados
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    owner = relationship('User', back_populates='strategies')

class OutboxItem(Base):
    __tablename__ = 'outbox_items'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_url = Column(String, nullable=False)
    prospect_username = Column(String, nullable=False)
    prospect_comment = Column(String, nullable=False)
    identified_pain = Column(String, default='')
    score = Column(String, default='')
    selected_opener = Column(String, nullable=False)
    status = Column(String, default='pending')
    notes = Column(Text, default='')  # <--- Agregar esta línea
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    owner = relationship('User', back_populates='outbox_items')

class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_data = Column(JSON, nullable=False)
    status = Column(String, default='iniciado')
    notes = Column(String, default='')
    exported = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    owner = relationship('User', back_populates='conversations')