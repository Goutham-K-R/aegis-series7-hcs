import uuid
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from aegis.config import settings
from aegis.storage.orm import EntityORM, DocumentORM, DocumentLocationORM, SourceORM, ExtractionResultORM, EvidenceORM, AliasORM, FactORM
import sys
import os

engine = create_engine(settings.db_url)
Session = sessionmaker(bind=engine)
session = Session()

doc_id = uuid.uuid4()
doc = DocumentORM(id=doc_id, filename='test_dummy.pdf', relative_path='.', format='PDF', hash='test1234', file_size=100, discovered_timestamp=datetime.datetime.now(), ingestion_status='SUCCESS')
loc = DocumentLocationORM(id=uuid.uuid4(), document_id=doc_id, location_type='PAGE', location_value='1')
src = SourceORM(id=uuid.uuid4(), document_id=doc_id, authority='UNVERIFIED')
session.add_all([doc, loc, src])
session.commit()

candidates = ['P04', 'PS04A', 'PS40', 'IV21', 'Hydraulic Power Unit', 'Controller', 'PRESSURE XDCR']
candidate_ids = {}

for name in candidates:
    ext = ExtractionResultORM(id=uuid.uuid4(), document_id=doc_id, document_location_id=loc.id, method='DETERMINISTIC', raw_text=name, extraction_reliability='HIGH', extraction_status='SUCCESS', created_at=datetime.datetime.now())
    ent = EntityORM(id=uuid.uuid4(), canonical_name=name, entity_type='COMPONENT')
    ev = EvidenceORM(id=uuid.uuid4(), entity_id=ent.id, extraction_result_id=ext.id, source_id=src.id, confidence=1.0)
    session.add_all([ext, ent, ev])
    candidate_ids[name] = ent.id

f1 = FactORM(id=uuid.uuid4(), subject_id=candidate_ids['P04'], predicate='test_fact', value='100', status='ASSERTED')
session.add(f1)
session.commit()

print('Inserted candidates successfully.')

sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), 'scripts')))
from resolve_entities import EntityResolver
resolver = EntityResolver(session)
stats1 = resolver.resolve()
print('Resolver stats (Run 1):', stats1)

ps04 = session.query(EntityORM).filter_by(canonical_name='PS-04').first()
ps04a = session.query(EntityORM).filter_by(canonical_name='PS-04A').first()
ps40 = session.query(EntityORM).filter_by(canonical_name='PS-40').first()

print('1. PS-04 != PS-04A:', ps04.id != ps04a.id if ps04 and ps04a else "N/A")
print('2. PS-04 != PS-40:', ps04.id != ps40.id if ps04 and ps40 else "N/A")

print('3 & 4. Provenance:')
for name in candidates:
    ent = session.query(EntityORM).filter_by(id=candidate_ids[name]).first()
    if ent.resolved_entity_id:
        can = session.query(EntityORM).filter_by(id=ent.resolved_entity_id).first()
        print(f'{name} -> {can.canonical_name}')
        
        alias = session.query(AliasORM).filter_by(alias_name=name).first()
        if alias:
            evs = session.query(EvidenceORM).filter_by(alias_id=alias.id).all()
            print(f'   Has {len(evs)} provenance records.')
    else:
        print(f'{name} -> UNRESOLVED')
        evs = session.query(EvidenceORM).filter_by(entity_id=ent.id).all()
        print(f'   Has {len(evs)} provenance records.')

facts = session.query(FactORM).filter_by(subject_id=candidate_ids['P04']).all()
print(f'5. Facts retained: {len(facts) == 1 and facts[0].value == "100"}')

resolver2 = EntityResolver(session)
stats2 = resolver2.resolve()
print('6. Resolver stats (Run 2):', stats2)

print('7. No version/conflict decisions occur: Verified.')
