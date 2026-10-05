import sys
import logging
from collections import defaultdict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from aegis.config import settings
from aegis.storage.orm import (
    DocumentORM, ExtractionResultORM, DocumentLocationORM, SourceORM,
    EntityORM, AliasORM, FactORM, RelationORM, EvidenceORM
)

def main():
    engine = create_engine(settings.db_url)
    Session = sessionmaker(bind=engine)
    
    with Session() as session:
        docs = session.query(DocumentORM).all()
        exts = session.query(ExtractionResultORM).all()
        locs = {l.id: l for l in session.query(DocumentLocationORM).all()}
        facts = session.query(FactORM).all()
        aliases = session.query(AliasORM).all()
        rels = session.query(RelationORM).all()
        entities = {e.id: e for e in session.query(EntityORM).all()}
        evidences = session.query(EvidenceORM).all()
        
        doc_map = {d.id: d for d in docs}
        doc_stats = defaultdict(lambda: {"format": "", "method": set(), "reliability": set(), "units": 0, "ev_links": 0})
        
        for e in exts:
            d = doc_map[e.document_id]
            doc_stats[d.id]["filename"] = d.filename
            doc_stats[d.id]["format"] = d.format
            doc_stats[d.id]["method"].add(e.method)
            doc_stats[d.id]["reliability"].add(e.extraction_reliability)
            doc_stats[d.id]["units"] += 1
            
        for ev in evidences:
            if ev.extraction_result_id:
                e = next((x for x in exts if x.id == ev.extraction_result_id), None)
                if e:
                    doc_stats[e.document_id]["ev_links"] += 1

    with open("audit_report.txt", "w", encoding="utf-8") as f:
        f.write("=== DOCUMENT COVERAGE ===\n")
        for did, st in doc_stats.items():
            f.write(f"{st['filename']} | {st['format']} | {list(st['method'])} | {list(st['reliability'])} | Units: {st['units']} | Ev Links: {st['ev_links']}\n")
            
        f.write("\n=== KNOWLEDGE INVENTORY ===\n")
        f.write("ENTITIES:\n")
        for e in entities.values():
            f.write(f"- {e.id}: {e.canonical_name} ({e.entity_type})\n")
            
        f.write("FACTS:\n")
        for ft in facts:
            subj = entities[ft.subject_id].canonical_name
            f.write(f"- {ft.id}: {subj} {ft.predicate} {ft.value} {ft.unit} [{ft.status}]\n")
            
        f.write("ALIASES:\n")
        for a in aliases:
            ent = entities[a.canonical_entity_id].canonical_name
            f.write(f"- {a.id}: {ent} = {a.alias_name} (Confirmed: {a.is_confirmed})\n")
            
        f.write("RELATIONS:\n")
        for r in rels:
            src = entities[r.source_entity_id].canonical_name
            tgt = entities[r.target_entity_id].canonical_name
            f.write(f"- {r.id}: {src} {r.relation_type} {tgt}\n")

        f.write("\n=== RAW TEXT SEARCH ===\n")
        keywords = ["Aegis Series-7 HCS", "HPU", "PLC-03", "IV-21", "PS-04", "PS-04A", "PS-40", 
                    "Q1", "T1", "TB-7", "A17", "A18", "A19", "ECN-1042", "ECN-1058", "firmware", 
                    "180", "200", "175", "bar", "400 V", "480 V", "MTBF", "temperature"]
                    
        ev_ext_ids = set(ev.extraction_result_id for ev in evidences if ev.extraction_result_id)
        
        for k in keywords:
            matches = [e for e in exts if k.lower() in e.raw_text.lower()]
            generated_knowledge = [e for e in matches if e.id in ev_ext_ids]
            f.write(f"Keyword: '{k}' -> {len(matches)} occurrences, {len(generated_knowledge)} converted to knowledge\n")
            if len(matches) > 0 and len(matches) > len(generated_knowledge):
                f.write(f"  Missed examples:\n")
                for e in matches:
                    if e.id not in ev_ext_ids:
                        f.write(f"    - [{doc_map[e.document_id].filename} / {locs[e.document_location_id].location_value}] {e.raw_text[:100]}...\n")

if __name__ == "__main__":
    main()
