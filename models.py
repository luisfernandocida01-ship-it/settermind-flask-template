# models.py
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
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

class Analysis(Base):
    __tablename__ = 'analyses'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_url = Column(String, nullable=False)
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
    created_at = Column(DateTime, default=datetime.utcnow)

    # Clave foránea para vincular la estrategia a un usuario
    owner_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    
    # Relación para que SQLAlchemy sepa cómo conectar
    owner = relationship('User', back_populates='strategies')    