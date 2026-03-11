import pytest
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Add backend to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from wms_service.app.models import Base
# Make sure to import all models so metadata is populated
from common.models import BaseEntity

# Connection config
# Use localhost:5433 because tests run on Host (Windows), mapping to Container:5432
DB_USER = "user"
DB_PASSWORD = "password"
DB_HOST = "localhost" 
DB_PORT = "5433"
DB_NAME = "interno_test"

# Main admin connection URL (to create the test DB)
ADMIN_DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres"
# Test DB connection URL
TEST_DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

@pytest.fixture(scope="session")
def setup_database():
    """
    Create the test database and tables at the start of the test session.
    Drop it at the end.
    """
    # 1. Connect to default DB to create the test DB
    admin_engine = create_engine(ADMIN_DATABASE_URL, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        # Check if DB exists and drop it to ensure clean state
        conn.execute(text(f"DROP DATABASE IF EXISTS {DB_NAME}"))
        conn.execute(text(f"CREATE DATABASE {DB_NAME}"))
    
    admin_engine.dispose()

    # 2. Connect to the NEW test DB to create tables
    test_engine = create_engine(TEST_DATABASE_URL, poolclass=NullPool)
    Base.metadata.create_all(test_engine)

    yield test_engine

    # 3. Teardown
    test_engine.dispose()
    
    # We can drop the DB if we want 'zero waste', or keep it for debugging.
    # User said "base de datos temporal". Dropping seems appropriate for clean runs.
    # However, connection locks might prevent drop if not careful.
    # For now, we will try to drop.
    admin_engine = create_engine(ADMIN_DATABASE_URL, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        try:
            # Terminate connections to test DB before dropping
            conn.execute(text(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{DB_NAME}'
                AND pid <> pg_backend_pid();
            """))
            conn.execute(text(f"DROP DATABASE {DB_NAME}"))
        except Exception as e:
            print(f"Warning: Could not drop test database: {e}")
    admin_engine.dispose()

@pytest.fixture(scope="module")
def engine(setup_database):
    """
    Returns the engine connected to nexosuite_test.
    """
    return setup_database

@pytest.fixture(scope="module")
def Session(engine):
    return sessionmaker(bind=engine)

@pytest.fixture
def session(engine):
    """
    Yields a session for each test.
    Wraps everything in a transaction that is ROLLED BACK after the test.
    Using SAVEPOINTS creates a nested scope so session.commit() in tests 
    doesn't actually commit to DB, just to the savepoint.
    """
    connection = engine.connect()
    transaction = connection.begin()
    
    # Create a Session bound to this connection
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    # Begin a nested transaction (SAVEPOINT)
    session.begin_nested()

    # Event to restart savepoint after commit
    from sqlalchemy import event
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        if transaction.nested and not transaction._parent.nested:
            session.expire_all()
            session.begin_nested()

    yield session

    session.close()
    # Rollback the outer transaction (cleanup)
    transaction.rollback()
    connection.close()
