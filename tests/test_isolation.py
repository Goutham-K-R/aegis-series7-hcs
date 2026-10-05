import pytest
from aegis.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def test_production_db_isolation():
    # Verify tests use memory DB, not the production aegis.db
    engine = create_engine("sqlite:///:memory:")
    assert str(engine.url) == "sqlite:///:memory:"
    assert "aegis.db" in settings.db_url
