from sqlmodel import create_engine, SQLModel, Session
from app.config.settings import get_settings
import os

settings = get_settings()

db_url = settings.DATABASE_URL
if db_url in ("sqlite:///./falconiq.db", "sqlite:///falconiq.db", "sqlite:///../falconiq.db"):
    # Always resolve to the absolute path of backend/falconiq.db regardless of working directory
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    db_path = os.path.join(backend_dir, "falconiq.db")
    db_url = f"sqlite:///{db_path}"

connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}

engine = create_engine(
    db_url,
    echo=settings.DB_ECHO,
    connect_args=connect_args
)

def init_db() -> None:
    """Creates all tables defined in SQLModel metadata."""
    SQLModel.metadata.create_all(engine)

def get_session() -> Session: # type: ignore
    """Dependency for yielding a database session."""
    with Session(engine) as session:
        yield session
