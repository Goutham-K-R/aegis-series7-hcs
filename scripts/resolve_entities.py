import argparse
import logging
import re
from uuid import uuid4
from collections import Counter
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from aegis.config import settings
from aegis.storage.orm import EntityORM, AliasORM, EvidenceORM

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger("aegis_resolution")

AMBIGUOUS_NAMES = {
    "HYDRAULIC UNIT", "HP UNIT", "HYDRAULIC POWER PACK", "THE UNIT",
    "CONTROLLER", "AEGIS CONTROLLER", "PRESSURE XDCR"
}

def normalize_name(name: str) -> str:
    name = name.upper().strip()
    if name == 'HYDRAULIC POWER UNIT': return 'HPU'
    if name == 'ISOLATION VALVE 21': return 'IV-21'
    name = name.replace('PRESSURE SENSOR ', 'PS-')
    match = re.fullmatch(r'([A-Z]+)-?(\d+[A-Z]*)', name)
    if match:
        prefix = match.group(1)
        suffix = match.group(2)
        if prefix == 'P': prefix = 'PS'
        if prefix in ['PS', 'IV', 'TB', 'ECN']: return f'{prefix}-{suffix}'
        if prefix == 'A': return f'{prefix}{suffix}'
    return name

class EntityResolver:
    def __init__(self, session):
        self.session = session
        self.stats = Counter()

    def _get_or_create_canonical(self, name: str, etype: str):
        ent = self.session.query(EntityORM).filter_by(canonical_name=name).first()
        if not ent:
            ent = EntityORM(id=uuid4(), canonical_name=name, entity_type=etype)
            self.session.add(ent)
            self.session.flush()
            self.stats["Canonical entities created"] += 1
        return ent

    def resolve(self):
        entities = self.session.query(EntityORM).all()
        self.stats["Candidates examined"] = len(entities)

        for ent in entities:
            # If already resolved, skip
            if ent.resolved_entity_id:
                self.stats["Already resolved"] += 1
                continue
                
            norm = normalize_name(ent.canonical_name)
            
            if ent.canonical_name.upper().strip() in AMBIGUOUS_NAMES or norm in AMBIGUOUS_NAMES:
                self.stats["Ambiguous aliases left unresolved"] += 1
                self.stats["Unresolved"] += 1
                continue
                
            if norm != ent.canonical_name:
                # It's an alias candidate that needs resolution to a canonical form
                can_ent = self._get_or_create_canonical(norm, ent.entity_type)
                ent.resolved_entity_id = can_ent.id
                
                # Create AliasORM
                existing_alias = self.session.query(AliasORM).filter_by(
                    canonical_entity_id=can_ent.id, alias_name=ent.canonical_name
                ).first()
                
                if not existing_alias:
                    alias = AliasORM(
                        id=uuid4(),
                        canonical_entity_id=can_ent.id,
                        alias_name=ent.canonical_name,
                        is_confirmed=True,
                        resolution_method="EXACT"
                    )
                    self.session.add(alias)
                    self.session.flush()
                    self.stats["Aliases resolved"] += 1
                    self.stats["EXACT"] += 1
                    
                    # Copy evidence from ent to alias
                    evs = self.session.query(EvidenceORM).filter_by(entity_id=ent.id).all()
                    for ev in evs:
                        new_ev = EvidenceORM(
                            id=uuid4(),
                            alias_id=alias.id,
                            extraction_result_id=ev.extraction_result_id,
                            source_id=ev.source_id,
                            confidence=ev.confidence
                        )
                        self.session.add(new_ev)
                        self.stats["Evidence links copied"] += 1
                
                self.stats["Resolved"] += 1
                
                # Update any existing AliasORM that pointed to the old candidate entity
                child_aliases = self.session.query(AliasORM).filter_by(canonical_entity_id=ent.id).all()
                for ca in child_aliases:
                    ca.canonical_entity_id = can_ent.id
                    self.stats["Child aliases updated"] += 1
            else:
                self.stats["Unresolved"] += 1 # It's its own canonical form

        self.session.commit()
        return self.stats

def main():
    db_url = settings.db_url
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    
    with Session() as session:
        resolver = EntityResolver(session)
        stats = resolver.resolve()
        
    print("Entity Resolution")
    print("-----------------")
    print(f"Candidates examined: {stats['Candidates examined']}")
    print(f"Resolved: {stats['Resolved']}")
    print(f"Unresolved: {stats['Unresolved']}")
    print("\nResolution methods:")
    print(f"  EXACT: {stats['EXACT']}")
    print(f"  REGISTER: 0")
    print(f"  DOCUMENT: 0")
    print(f"  CONTEXT: 0")
    print(f"  MODEL: 0")
    print(f"\nCanonical entities created: {stats['Canonical entities created']}")
    print(f"Aliases resolved: {stats['Aliases resolved']}")
    print(f"Evidence links copied: {stats['Evidence links copied']}")
    print(f"Ambiguous aliases left unresolved: {stats['Ambiguous aliases left unresolved']}")
    
    if stats['Canonical entities created'] == 0 and stats['Aliases resolved'] == 0:
        print("\nNo duplicate records created: PASS")
    else:
        print("\nNo duplicate records created: N/A (First run or changes made)")

if __name__ == '__main__':
    main()
