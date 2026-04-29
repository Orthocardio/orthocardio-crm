import os
import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

# [FIX ULTIMATE] Codificación robusta
if "@" in DATABASE_URL and "://" in DATABASE_URL:
    try:
        scheme, rest = DATABASE_URL.split("://", 1)
        auth, host_port_db = rest.rsplit("@", 1) # Usar rsplit para manejar @ en password
        user, password = auth.split(":", 1)
        encoded_password = urllib.parse.quote_plus(password)
        DATABASE_URL = f"{scheme}://{user}:{encoded_password}@{host_port_db}"
    except Exception as e:
        print(f"Error parseando URL: {e}")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

try:
    engine = create_engine(DATABASE_URL, connect_args=connect_args)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
except Exception as e:
    print(f"ERROR CRÍTICO DE BASE DE DATOS: {e}")
    # Fallback a SQLite temporal para evitar crash del búnker
    engine = create_engine("sqlite:///./fallback.db")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
