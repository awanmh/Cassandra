import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Base class for models
Base = declarative_base()

class ScanResult(Base):
    __tablename__ = 'scan_results'
    
    id = Column(Integer, primary_key=True, index=True)
    target = Column(String, index=True)
    scan_type = Column(String)
    severity = Column(String)
    details = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)

class FoundSecret(Base):
    __tablename__ = 'found_secrets'
    
    id = Column(Integer, primary_key=True, index=True)
    target = Column(String, index=True)
    secret_type = Column(String)
    value = Column(String)
    file_source = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class FoundEndpoint(Base):
    __tablename__ = 'found_endpoints'
    
    id = Column(Integer, primary_key=True, index=True)
    target = Column(String, index=True)
    endpoint = Column(String)
    source_url = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Database Setup
DB_USER = os.getenv("POSTGRES_USER", "cassandra")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "secretphrasesecure")
DB_HOST = os.getenv("POSTGRES_SERVER", "localhost")
DB_NAME = os.getenv("POSTGRES_DB", "cassandra_db")

# Construct connection string
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

# Create Engine
engine = create_engine(DATABASE_URL)

# Session Local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully.")
    except Exception as e:
        print(f"Error creating database tables: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
