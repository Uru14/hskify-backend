from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from databases import Database

DATABASE_URL = "postgresql://postgres:BnCQdXPBOqJzqskFkfwoCtwQZCBFMRzr@monorail.proxy.rlwy.net:17422/railway"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy models
Base = declarative_base()

# Database instance for async support
database = Database(DATABASE_URL)