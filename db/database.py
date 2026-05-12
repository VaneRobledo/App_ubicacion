from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# -----------------------------
# URL de conexión PostgreSQL
# -----------------------------
DATABASE_URL = (
    "postgresql://usuario:password@localhost:5432/geobusiness"
)

# -----------------------------
# Engine
# -----------------------------
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

# -----------------------------
# Sesiones
# -----------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# -----------------------------
# Base para modelos
# -----------------------------
Base = declarative_base()

# -----------------------------
# Dependency FastAPI
# -----------------------------
def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()