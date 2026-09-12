import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


@pytest.fixture(scope="session")
def database_url() -> str:
    value = os.environ.get("TEST_DATABASE_URL")
    if not value:
        pytest.fail("TEST_DATABASE_URL is required for PostgreSQL integration tests")
    return value


@pytest.fixture(scope="session")
def database_engine(database_url: str) -> Engine:
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS data_collection CASCADE"))
        connection.execute(text("DROP TABLE IF EXISTS public.alembic_version"))
    yield engine
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS data_collection CASCADE"))
        connection.execute(text("DROP TABLE IF EXISTS public.alembic_version"))
    engine.dispose()
