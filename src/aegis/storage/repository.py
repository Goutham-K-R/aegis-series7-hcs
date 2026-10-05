from typing import TypeVar, Generic, Type, Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from aegis.storage.orm import Base

T = TypeVar('T', bound=Base)

class ReadOnlyRepository(Generic[T]):
    """Read-only repository interface for the QA layer."""
    def __init__(self, session: Session, model_cls: Type[T]):
        self.session = session
        self.model_cls = model_cls

    def get_by_id(self, id: UUID) -> Optional[T]:
        return self.session.query(self.model_cls).filter(self.model_cls.id == id).first()
        
    def list_all(self, limit: int = 100) -> List[T]:
        return self.session.query(self.model_cls).limit(limit).all()

class WriteRepository(ReadOnlyRepository[T]):
    """Write-enabled repository for ingestion and assembly layers."""
    def add(self, entity: T) -> T:
        self.session.add(entity)
        self.session.flush()
        return entity
