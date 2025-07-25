import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# ⬅️ Load file .env
load_dotenv()

# ⬅️ Ambil URL dari environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Buat engine SQLAlchemy
engine = create_engine(DATABASE_URL)

# Session untuk operasi database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base untuk deklarasi model
Base = declarative_base()
