from databases import Database
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = 'postgresql://postgres:BnCQdXPBOqJzqskFkfwoCtwQZCBFMRzr@monorail.proxy.rlwy.net:17422/railway'

engine = create_engine(DATABASE_URL)

"""Each instance of the SessionLocal class will be a database session. The class itself is not a database session yet.
We name it SessionLocal to distinguish it from the Session we are importing from SQLAlchemy.
We will use Session (the one imported from SQLAlchemy) later.
To create the SessionLocal class, use the function sessionmaker"""
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

database = Database(DATABASE_URL)






