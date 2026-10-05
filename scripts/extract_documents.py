import sys
import logging
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from aegis.config import settings
from aegis.ingestion.extractor import BatchExtractor

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger("aegis_extract")

def main():
    db_url = settings.db_url
    dataset_path = settings.dataset_path
    
    logger.info(f"Connecting to database: {db_url}")
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    
    with Session() as session:
        batch = BatchExtractor(session, dataset_path)
        logger.info("Starting batch extraction...")
        stats = batch.extract_all()
        
    print(f"Documents: {stats['total_documents']}")
    print(f"SUCCESS: {stats['SUCCESS']}")
    print(f"PARTIAL: {stats['PARTIAL']}")
    print(f"REQUIRES_OCR: {stats['REQUIRES_OCR']}")
    print(f"FAILED: {stats['FAILED']}")
    print(f"UNSUPPORTED: {stats['UNSUPPORTED']}")
    print(f"Extraction results: {stats['total_results']}")

if __name__ == "__main__":
    main()
