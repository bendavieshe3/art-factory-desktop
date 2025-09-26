"""
Database initialization and session management.
"""

from pathlib import Path
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session, Query
from sqlalchemy.engine import Engine

from .base import Base


# Database configuration
DATABASE_DIR = Path.home() / ".art-factory"
DATABASE_PATH = DATABASE_DIR / "art_factory.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Test database for unit tests
TEST_DATABASE_URL = "sqlite:///:memory:"


class DatabaseManager:
    """Manage database connections and sessions."""

    def __init__(self, database_url: str = None, echo: bool = False):
        """
        Initialize database manager.

        Args:
            database_url: Database URL (defaults to production DB)
            echo: Enable SQL echo for debugging
        """
        self.database_url = database_url or DATABASE_URL
        self.echo = echo
        self.engine = None
        self.SessionLocal = None
        self._initialized = False

    def init(self):
        """Initialize database engine and session factory."""
        if self._initialized:
            return

        # Create database directory if needed
        if "sqlite" in self.database_url and ":memory:" not in self.database_url:
            db_path = self.database_url.replace("sqlite:///", "")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Create engine
        self.engine = create_engine(
            self.database_url,
            echo=self.echo,
            connect_args=(
                {"check_same_thread": False} if "sqlite" in self.database_url else {}
            ),
        )

        # Enable foreign keys for SQLite
        if "sqlite" in self.database_url:

            @event.listens_for(Engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        # Create session factory
        self.SessionLocal = scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        )

        # Add query property to Base
        Base.query = self.SessionLocal.query_property()

        self._initialized = True

    def create_all(self):
        """Create all database tables."""
        if not self._initialized:
            self.init()
        Base.metadata.create_all(bind=self.engine)

    def drop_all(self):
        """Drop all database tables."""
        if not self._initialized:
            self.init()
        Base.metadata.drop_all(bind=self.engine)

    def get_session(self):
        """Get a new database session."""
        if not self._initialized:
            self.init()
        return self.SessionLocal()

    @contextmanager
    def session_scope(self):
        """
        Provide a transactional scope for database operations.

        Usage:
            with db_manager.session_scope() as session:
                session.add(model)
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self):
        """Close database connections."""
        if self.SessionLocal:
            self.SessionLocal.remove()
        if self.engine:
            self.engine.dispose()
        self._initialized = False


# Global database manager instance
db_manager = DatabaseManager()


def init_database(database_url: str = None, echo: bool = False):
    """
    Initialize the database.

    Args:
        database_url: Optional database URL (for testing)
        echo: Enable SQL echo for debugging
    """
    global db_manager
    if database_url:
        db_manager = DatabaseManager(database_url, echo)
    else:
        db_manager.echo = echo

    db_manager.init()
    db_manager.create_all()
    return db_manager


def get_session():
    """Get a database session."""
    return db_manager.get_session()


def session_scope():
    """Get a session context manager."""
    return db_manager.session_scope()


# Query helpers for soft deletes
class SoftDeleteQuery(Query):
    """Custom query class that filters out soft-deleted records by default."""

    def __new__(cls, entities, session=None):
        query = super().__new__(cls)
        query.__init__(entities, session)
        return query.filter_by(deleted_at=None)

    def with_deleted(self):
        """Include soft-deleted records in query."""
        return self.filter(True)

    def only_deleted(self):
        """Only return soft-deleted records."""
        return self.filter(self.column_descriptions[0]["entity"].deleted_at.isnot(None))
