# database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Replace with your PostgreSQL connection string
# Example: "postgresql://user:password@host:port/database_name"
SQLALCHEMY_DATABASE_URL = "postgresql://metro_user:metro_password@localhost/hyderabad_metro"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()