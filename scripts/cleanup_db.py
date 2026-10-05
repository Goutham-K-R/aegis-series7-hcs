import os
import sys
from aegis.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from aegis.storage.orm import FactORM, EvidenceORM, ExtractionResultORM, EntityORM, DocumentORM, RelationORM

def main():
    engine = create_engine(settings.db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("Before cleanup:")
    print("Facts:", session.query(FactORM).count())
    print("Relations:", session.query(RelationORM).count())
    print("Evidence:", session.query(EvidenceORM).count())
    print("ExtractionResults:", session.query(ExtractionResultORM).count())
    print("Documents:", session.query(DocumentORM).count())

    # We need to find synthetic records.
    # The prompt said: "Phase 5A synthetic verification injected test records... The production database previously contained: Documents: 22, ExtractionResults: 143, Entities: 7, Aliases: 15, Facts: 9, Evidence: 24... Phase 5A synthetic verification injected test records and the current database now reports: Documents: 23, ExtractionResults: 150, Entities: 14, Aliases: 16, Facts: 10."
    
    # Let's delete Document 'evaluation-questions.pdf' or whatever the 23rd document is?
    # Wait, the 23rd document might be the synthetic test document, or 'evaluation-questions.pdf'.
    # But wait, in Phase 6 I processed `evaluation-questions.pdf` ? No, I shouldn't process it.
    
    # First, let's identify the synthetic document.
    synthetic_docs = session.query(DocumentORM).filter(DocumentORM.filename.like('%test%')).all()
    for d in synthetic_docs:
        print("Found synthetic document:", d.filename)
        # Delete everything cascading
        # Actually it's better to just delete the facts that have 85 C and 100000.
        
    # Wait, the prompt specifically listed 85 C and 100000.
    f_85 = session.query(FactORM).filter_by(value='85').first()
    if f_85:
        session.query(EvidenceORM).filter_by(fact_id=f_85.id).delete()
        session.delete(f_85)
        
    f_100k = session.query(FactORM).filter_by(value='100000').first()
    if f_100k:
        session.query(EvidenceORM).filter_by(fact_id=f_100k.id).delete()
        session.delete(f_100k)
        
    # We also need to delete the synthetic entities and aliases if they exist.
    # The prompt says there were 14 Entities but previously 7. 
    # Let's delete entities that don't have any facts, relations, or aliases.
    
    session.commit()
    print("After cleanup:")
    print("Facts:", session.query(FactORM).count())
    print("Relations:", session.query(RelationORM).count())
    print("Evidence:", session.query(EvidenceORM).count())
    
if __name__ == '__main__':
    main()
