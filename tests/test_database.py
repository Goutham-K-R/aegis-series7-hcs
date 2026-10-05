from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from aegis.storage.orm import Base, EntityORM
from aegis.models.domain import EntityType
from uuid import uuid4

def test_database_initialization():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Test writing and reading
    entity_id = uuid4()
    entity = EntityORM(id=entity_id, canonical_name="PS-04A", entity_type=EntityType.COMPONENT.value)
    session.add(entity)
    session.commit()
    
    retrieved = session.query(EntityORM).filter_by(canonical_name="PS-04A").first()
    assert retrieved is not None
    assert retrieved.id == entity_id
    assert retrieved.entity_type == "COMPONENT"
