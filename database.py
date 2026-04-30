import os
import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_URL") or "sqlite:///./orthocardio_crm.db"

# Normalización de URL para SQLAlchemy y Supabase Transaction Pooler (Port 6543)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# [FIX] Supabase Pooler requiere el tenant_id en el usuario si no se detecta
# Formato: postgresql://postgres.[TENANT_ID]:[PASSWORD]@...
if "pooler.supabase.com" in DATABASE_URL or "supabase.co" in DATABASE_URL:
    if "sslmode" not in DATABASE_URL:
        separator = "&" if "?" in DATABASE_URL else "?"
        DATABASE_URL += f"{separator}sslmode=require"
    
# Configuración dinámica de argumentos de conexión
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

try:
    engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
except Exception as e:
    print(f"FALLBACK: Error crítico de conexión ({e}). Reintentando con SQLite local.")
    engine = create_engine("sqlite:///./orthocardio_crm.db", connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

