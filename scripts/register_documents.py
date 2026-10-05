import sys
import logging
from pathlib import Path
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from aegis.config import settings
from aegis.storage.orm import Base
from aegis.ingestion.registry import DocumentRegistry

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger("aegis_register")

def main():
    db_url = settings.db_url
    dataset_path = settings.dataset_path
    
    logger.info(f"Connecting to database: {db_url}")
    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    
    with Session() as session:
        registry = DocumentRegistry(session)
        logger.info(f"Scanning dataset path: {dataset_path.absolute()}")
        stats = registry.scan_and_register(dataset_path)
        
    print(f"Documents discovered: {stats['discovered']}")
    print(f"New: {stats['new']}")
    print(f"Unchanged: {stats['unchanged']}")
    print(f"Changed: {stats['changed']}")
    print(f"Duplicates: {stats['duplicates']}")
    print(f"Errors: {stats['errors']}")

if __name__ == "__main__":
    main()
