import sys
import argparse
import logging
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from aegis.config import settings
from aegis.knowledge.builder import KnowledgeBuilder

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger("aegis_knowledge")

def main():
    parser = argparse.ArgumentParser(description="Build Aegis Knowledge Base")
    parser.add_argument("--mode", choices=["deterministic", "model", "hybrid"], default="hybrid", help="Extraction mode")
    args = parser.parse_args()

    db_url = settings.db_url
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    
    with Session() as session:
        builder = KnowledgeBuilder(session, mode=args.mode)
        logger.info(f"Starting knowledge building in {args.mode} mode...")
        stats = builder.build_knowledge()
        
    print(f"Entities: {stats['entities']}")
    print(f"Aliases: {stats['aliases']}")
    print(f"Facts: {stats['facts']}")
    print(f"Relations: {stats['relations']}")
    print(f"Validity records: {stats.get('validities', 0)}")
    print(f"Evidence links: {stats['evidence_links']}")
    print(f"Rejected candidates: {stats['rejected']}")
    print(f"OCR-skipped content: {stats['ocr_skipped']}")
    print(f"Deterministic candidates: {stats['deterministic']}")
    print(f"Model candidates: {stats['model_candidates']}")

if __name__ == "__main__":
    main()
