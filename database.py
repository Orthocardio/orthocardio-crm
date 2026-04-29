import os
import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# [FIX] Codificación segura para contraseñas con @ o *
if "@" in DATABASE_URL and ":" in DATABASE_URL:
    try:
        # Extraer partes para codificar solo el password
        prefix, rest = DATABASE_URL.split("://", 1)
        auth, host_path = rest.split("@", 1)
        user, password = auth.split(":", 1)
        encoded_password = urllib.parse.quote_plus(password)
        DATABASE_URL = f"{prefix}://{user}:{encoded_password}@{host_path}"
    except:
        pass

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
