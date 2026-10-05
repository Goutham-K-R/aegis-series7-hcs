import sys
import os
from typing import List, Tuple
from sqlalchemy.orm import Session
from aegis.storage.orm import FactORM, RelationORM, EvidenceORM, ExtractionResultORM, SourceORM, DocumentORM, DocumentLocationORM, ValidityORM, ConflictORM, EntityORM

from .models import QueryAnalysis, RetrievalCandidate, VerifiedEvidence, VerificationDecision, RetrievalResult

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'scripts')))
from resolve_conflicts import evaluate_applicability, overlap

class EvidenceVerifier:
    def __init__(self, session: Session):
        self.session = session
        
    def verify(self, qa: QueryAnalysis, candidates: List[RetrievalCandidate]) -> Tuple[List[VerifiedEvidence], VerificationDecision, str]:
        if len(qa.ambiguity_indicators) > 0:
            return [], VerificationDecision.INSUFFICIENT_EVIDENCE, f"Ambiguous entities requested: {qa.ambiguity_indicators}"
            
        if not candidates:
            return [], VerificationDecision.INSUFFICIENT_EVIDENCE, "No candidates retrieved."
            
        verified = []
        applicable_facts = []
        conflicts = set()
        found_any_fact = False
        
        for cand in candidates:
            if cand.fact_id:
                fact = self.session.query(FactORM).filter_by(id=cand.fact_id).first()
                if not fact:
                    continue
                found_any_fact = True
                # Get Evidence
                evidences = self.session.query(EvidenceORM).filter_by(fact_id=fact.id).all()
                valid_evs = []
                for ev in evidences:
                    # check provenance chain
                    if not ev.extraction_result_id: continue
                    ext = self.session.query(ExtractionResultORM).filter_by(id=ev.extraction_result_id).first()
                    if not ext: continue
                    if not ext.document_location_id: continue
                    loc = self.session.query(DocumentLocationORM).filter_by(id=ext.document_location_id).first()
                    if not loc: continue
                    if not ext.document_id: continue
                    doc = self.session.query(DocumentORM).filter_by(id=ext.document_id).first()
                    if not doc: continue
                    src = self.session.query(SourceORM).filter_by(document_id=doc.id).first()
                    if not src: continue
                    valid_evs.append((ev, ext, loc, doc, src))
                    
                if not valid_evs:
                    continue
                    
                # Applicability check
                val = self.session.query(ValidityORM).filter_by(id=fact.validity_id).first() if fact.validity_id else None
                if qa.firmware_context:
                    app = evaluate_applicability(val, target_fw=qa.firmware_context)
                    if app == "DOES_NOT_APPLY":
                        continue
                else:
                    # if there is no context but fact is scoped, we might have ambiguity later
                    pass
                
                applicable_facts.append((fact, valid_evs, val))
                
            elif cand.relation_id:
                # verify relation
                rel = self.session.query(RelationORM).filter_by(id=cand.relation_id).first()
                if not rel:
                    continue
                found_any_fact = True
                evidences = self.session.query(EvidenceORM).filter_by(relation_id=rel.id).all()
                valid_evs = []
                for ev in evidences:
                    # check provenance chain
                    if not ev.extraction_result_id: continue
                    ext = self.session.query(ExtractionResultORM).filter_by(id=ev.extraction_result_id).first()
                    if not ext: continue
                    if not ext.document_location_id: continue
                    loc = self.session.query(DocumentLocationORM).filter_by(id=ext.document_location_id).first()
                    if not loc: continue
                    if not ext.document_id: continue
                    doc = self.session.query(DocumentORM).filter_by(id=ext.document_id).first()
                    if not doc: continue
                    src = self.session.query(SourceORM).filter_by(document_id=doc.id).first()
                    if not src: continue
                    valid_evs.append((ev, ext, loc, doc, src))
                    
                if not valid_evs:
                    continue
                    
                applicable_facts.append((rel, valid_evs, None)) # treat rel as a fact for now
                
        # Conflict Detection
        if not applicable_facts:
            if found_any_fact:
                return [], VerificationDecision.NOT_APPLICABLE, "Evidence found but does not apply to requested context."
            else:
                return [], VerificationDecision.INSUFFICIENT_EVIDENCE, "The supplied documentation does not establish the requested value."
            
        # Group by (subject, predicate)
        by_subj_pred = {}
        for item, evs, val in applicable_facts:
            if isinstance(item, FactORM):
                key = (item.subject_id, item.predicate)
            else:
                key = (item.source_entity_id, item.relation_type)
            if key not in by_subj_pred: by_subj_pred[key] = []
            by_subj_pred[key].append((item, evs, val))
            
        is_conflicted = False
        conflict_reason = ""
        
        for (subj, pred), items in by_subj_pred.items():
            if isinstance(items[0][0], FactORM):
                # if multiple different values for same predicate
                values = set(f.value for f, evs, val in items)
                if len(values) > 1:
                    has_contradiction = False
                    for i in range(len(items)):
                        for j in range(i+1, len(items)):
                            if items[i][0].value != items[j][0].value:
                                c = self.session.query(ConflictORM).filter(
                                    ((ConflictORM.fact_a_id == items[i][0].id) & (ConflictORM.fact_b_id == items[j][0].id)) |
                                    ((ConflictORM.fact_a_id == items[j][0].id) & (ConflictORM.fact_b_id == items[i][0].id))
                                ).first()
                                if c and c.conflict_type == "CONTRADICTION":
                                    has_contradiction = True
                                    break
                        if has_contradiction: break
                    
                    if has_contradiction:
                        is_conflicted = True
                        if not qa.firmware_context:
                            conflict_reason = f"Multiple contradicting values for {pred} without specific firmware context."
                        else:
                            conflict_reason = f"Contradicting applicable values for {pred} on firmware {qa.firmware_context}."
                        
            for item, evs, val in items:
                subject_ent = self.session.query(EntityORM).filter_by(id=item.source_entity_id if isinstance(item, RelationORM) else item.subject_id).first()
                subject_name = subject_ent.canonical_name if subject_ent else "Unknown"
                
                for ev, ext, loc, doc, src in evs:
                    v_ev = VerifiedEvidence(
                        fact_id=str(item.id) if isinstance(item, FactORM) else None,
                        relation_id=str(item.id) if isinstance(item, RelationORM) else None,
                        evidence_id=str(ev.id),
                        extraction_result_id=str(ext.id),
                        source_id=str(src.id),
                        document_id=str(doc.id),
                        document_filename=doc.filename,
                        document_location=loc.location_value,
                        extraction_method=ext.method,
                        extraction_reliability=ext.extraction_reliability,
                        source_authority=src.authority,
                        validity_info={"fw_version_min": val.fw_version_min, "fw_version_max": val.fw_version_max} if val else None,
                        subject=subject_name,
                        predicate=item.predicate if isinstance(item, FactORM) else item.relation_type,
                        value=item.value if isinstance(item, FactORM) else getattr(item, 'target_entity_id', None),
                        unit=item.unit if isinstance(item, FactORM) else None
                    )
                    verified.append(v_ev)
                    
        if is_conflicted:
            return verified, VerificationDecision.CONFLICTED, conflict_reason
            
        return verified, VerificationDecision.VERIFIED, "Evidence verified successfully."
