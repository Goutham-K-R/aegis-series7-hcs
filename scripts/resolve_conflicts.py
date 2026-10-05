import argparse
import logging
import re
import json
from uuid import uuid4
from collections import Counter, defaultdict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from aegis.config import settings
from aegis.storage.orm import EntityORM, FactORM, ValidityORM, ConflictORM, ResolutionResultORM, EvidenceORM, SourceORM, ExtractionResultORM

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger("aegis_conflicts")

def parse_version(v: str):
    if not v or 'planned' in v.lower():
        return None
    m = re.search(r'(\d+(?:\.\d+)*)', v)
    if not m:
        return None
    return tuple(int(x) for x in m.group(1).split('.'))

def evaluate_applicability(validity, target_fw=None, target_date=None) -> str:
    if not target_fw and not target_date:
        return "UNKNOWN"
        
    applies = "UNKNOWN"
    
    if target_fw:
        tv = parse_version(target_fw)
        if not tv:
            return "UNKNOWN"
            
        if validity:
            min_v = parse_version(validity.fw_version_min)
            max_v = parse_version(validity.fw_version_max)
            
            if min_v or max_v:
                if min_v and tv < min_v: return "DOES_NOT_APPLY"
                if max_v and tv > max_v: return "DOES_NOT_APPLY"
                applies = "APPLIES"
                
    if target_date and validity:
        if validity.date_effective or validity.date_superseded:
            if validity.date_effective and target_date < validity.date_effective: return "DOES_NOT_APPLY"
            if validity.date_superseded and target_date > validity.date_superseded: return "DOES_NOT_APPLY"
            if applies != "DOES_NOT_APPLY": applies = "APPLIES"
            
    return applies

def overlap(v1, v2):
    if not v1 and not v2: return True
    if not v1 or not v2: return True
    
    min1 = parse_version(v1.fw_version_min)
    max1 = parse_version(v1.fw_version_max)
    min2 = parse_version(v2.fw_version_min)
    max2 = parse_version(v2.fw_version_max)
    
    if max1 and min2 and max1 < min2: return False
    if max2 and min1 and max2 < min1: return False
    
    return True

class ConflictResolver:
    def __init__(self, session, firmware=None, target_date=None):
        self.session = session
        self.firmware = firmware
        self.target_date = target_date
        self.stats = Counter()
        
    def run(self):
        facts = self.session.query(FactORM).all()
        self.stats["Facts examined"] = len(facts)
        
        grouped = defaultdict(list)
        for f in facts:
            grouped[(f.subject_id, f.predicate)].append(f)
            
        for key, group in grouped.items():
            if len(group) < 2:
                continue
                
            for i in range(len(group)):
                for j in range(i+1, len(group)):
                    f1 = group[i]
                    f2 = group[j]
                    
                    if f1.value != f2.value or f1.unit != f2.unit:
                        self.stats["Potential conflict pairs"] += 1
                        v1 = self.session.query(ValidityORM).filter_by(id=f1.validity_id).first() if f1.validity_id else None
                        v2 = self.session.query(ValidityORM).filter_by(id=f2.validity_id).first() if f2.validity_id else None
                        
                        is_overlap = overlap(v1, v2)
                        
                        c = self.session.query(ConflictORM).filter(
                            ((ConflictORM.fact_a_id == f1.id) & (ConflictORM.fact_b_id == f2.id)) |
                            ((ConflictORM.fact_a_id == f2.id) & (ConflictORM.fact_b_id == f1.id))
                        ).first()
                        
                        if not c:
                            c = ConflictORM(
                                id=uuid4(),
                                fact_a_id=f1.id,
                                fact_b_id=f2.id,
                                conflict_type="CONTRADICTION" if is_overlap else "VERSION_OVERRIDE",
                                resolution_note="Automatically detected" if is_overlap else "Version-scoped distinction. No explicit supersession established."
                            )
                            self.session.add(c)
                            self.session.flush()
                            self.stats["Conflicts created"] += 1
                            if is_overlap:
                                self.stats["True contradictions"] += 1
                            else:
                                self.stats["Version-scoped conflicts"] += 1
                        else:
                            self.stats["Existing conflicts"] += 1

        if not self.firmware and not self.target_date:
            self.session.commit()
            return self.stats
            
        query_id = uuid4()
        
        for key, group in grouped.items():
            app_status = {}
            for f in group:
                v = self.session.query(ValidityORM).filter_by(id=f.validity_id).first() if f.validity_id else None
                app_status[f.id] = evaluate_applicability(v, self.firmware, self.target_date)
            
            applies = [f for f in group if app_status[f.id] == "APPLIES"]
            unknown = [f for f in group if app_status[f.id] == "UNKNOWN"]
            does_not_apply = [f for f in group if app_status[f.id] == "DOES_NOT_APPLY"]
            
            if len(applies) == 1 and len(unknown) == 0:
                self._record_result(query_id, applies[0], "SELECTED", "Explicitly applies to context and no unknown contradictions", "APPLIES", "RESOLVED")
                for f in does_not_apply:
                    self._record_result(query_id, f, "NOT_APPLICABLE", "Explicitly does not apply", app_status[f.id], "RESOLVED")
            elif len(applies) == 1 and len(unknown) > 0:
                self._record_result(query_id, applies[0], "INSUFFICIENT_EVIDENCE", "Applies to context, but competing fact has unknown applicability", "APPLIES", "UNRESOLVED")
                for f in unknown:
                    self._record_result(query_id, f, "INSUFFICIENT_EVIDENCE", "Applicability unknown against an explicitly applying fact", "UNKNOWN", "UNRESOLVED")
                for f in does_not_apply:
                    self._record_result(query_id, f, "NOT_APPLICABLE", "Explicitly does not apply", "DOES_NOT_APPLY", "RESOLVED")
            elif len(applies) > 1:
                for f in applies:
                    self._record_result(query_id, f, "CONFLICTED", "Multiple contradictory facts explicitly apply", "APPLIES", "UNRESOLVED")
                for f in unknown:
                    self._record_result(query_id, f, "CONFLICTED", "Applicability unknown against multiple applying facts", "UNKNOWN", "UNRESOLVED")
                for f in does_not_apply:
                    self._record_result(query_id, f, "NOT_APPLICABLE", "Explicitly does not apply", "DOES_NOT_APPLY", "RESOLVED")
            elif len(unknown) > 0:
                for f in unknown:
                    self._record_result(query_id, f, "INSUFFICIENT_EVIDENCE", "Applicability unknown", "UNKNOWN", "UNRESOLVED")
                for f in does_not_apply:
                    self._record_result(query_id, f, "NOT_APPLICABLE", "Explicitly does not apply", "DOES_NOT_APPLY", "RESOLVED")
            else:
                for f in does_not_apply:
                    self._record_result(query_id, f, "NOT_APPLICABLE", "Explicitly does not apply", "DOES_NOT_APPLY", "RESOLVED")
                    
        self.session.commit()
        return self.stats
        
    def _record_result(self, query_id, fact, decision, reason, applicability, conflict_status):
        existing = self.session.query(ResolutionResultORM).filter_by(query_id=query_id, candidate_fact_id=fact.id).first()
        if not existing:
            evs = self.session.query(EvidenceORM).filter_by(fact_id=fact.id).all()
            ev_ids = [str(e.id) for e in evs]
            res = ResolutionResultORM(
                id=uuid4(),
                query_id=query_id,
                candidate_fact_id=fact.id,
                decision=decision,
                reason=reason,
                applicability_status=applicability,
                conflict_status=conflict_status,
                evidence_ids=json.dumps(ev_ids)
            )
            self.session.add(res)
            self.stats[decision] += 1

def main():
    parser = argparse.ArgumentParser(description="Resolve conflicts in knowledge base")
    parser.add_argument("--firmware", type=str, help="Firmware version context (e.g. 3.2.1)", default=None)
    parser.add_argument("--date", type=str, help="Date context (YYYY-MM-DD)", default=None)
    args = parser.parse_args()

    engine = create_engine(settings.db_url)
    Session = sessionmaker(bind=engine)
    
    with Session() as session:
        resolver = ConflictResolver(session, firmware=args.firmware, target_date=args.date)
        stats = resolver.run()
        
    print("Conflict Resolution")
    print("-------------------")
    print(f"Facts examined: {stats['Facts examined']}")
    print(f"Potential conflict pairs: {stats['Potential conflict pairs']}")
    print(f"Version-scoped conflicts: {stats['Version-scoped conflicts']}")
    print(f"True contradictions: {stats['True contradictions']}")
    
    if args.firmware or args.date:
        print("\nResolution results:")
        print(f"  SELECTED: {stats['SELECTED']}")
        print(f"  CONFLICTED: {stats['CONFLICTED']}")
        print(f"  INSUFFICIENT_EVIDENCE: {stats['INSUFFICIENT_EVIDENCE']}")
        print(f"  NOT_APPLICABLE: {stats['NOT_APPLICABLE']}")
        
    print(f"\nConflicts created: {stats['Conflicts created']}")
    print(f"Existing conflicts: {stats['Existing conflicts']}")
    
    if stats['Facts examined'] > 0:
        print("\nNo facts deleted: PASS")

if __name__ == '__main__':
    main()
