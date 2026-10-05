from typing import List
from sqlalchemy.orm import Session
from aegis.storage.orm import EntityORM, AliasORM, FactORM, RelationORM, EvidenceORM, ExtractionResultORM
from .models import QueryAnalysis, RetrievalCandidate, RetrievalMethod
from .fts import FTSIndex
import logging

logger = logging.getLogger("aegis_retriever")

class CandidateRetriever:
    def __init__(self, session: Session):
        self.session = session
        self.fts = FTSIndex(session)

    def retrieve(self, qa: QueryAnalysis) -> List[RetrievalCandidate]:
        candidates = []
        
        # 1. Exact entity + predicate lookup
        if qa.entities and qa.requested_predicate:
            for ent_name in qa.entities:
                ent = self.session.query(EntityORM).filter_by(canonical_name=ent_name).first()
                if not ent:
                    # check if alias
                    al = self.session.query(AliasORM).filter_by(alias_name=ent_name).first()
                    if al:
                        ent = self.session.query(EntityORM).filter_by(id=al.canonical_entity_id).first()
                
                if ent:
                    facts = self.session.query(FactORM).filter_by(subject_id=ent.id, predicate=qa.requested_predicate).all()
                    for f in facts:
                        candidates.append(RetrievalCandidate(
                            fact_id=str(f.id),
                            entity_id=str(ent.id),
                            retrieval_method=RetrievalMethod.EXACT,
                            retrieval_score=1.0,
                            matched_terms=[ent_name, qa.requested_predicate]
                        ))
        
        # 2. Structured lookup (Relations, or just by Entity)
        if qa.entities and not qa.requested_predicate:
            # We want all facts and relations for these entities
            for ent_name in qa.entities:
                ent = self.session.query(EntityORM).filter_by(canonical_name=ent_name).first()
                if not ent:
                    al = self.session.query(AliasORM).filter_by(alias_name=ent_name).first()
                    if al:
                        ent = self.session.query(EntityORM).filter_by(id=al.canonical_entity_id).first()
                
                if ent:
                    # relations
                    rels = self.session.query(RelationORM).filter((RelationORM.source_entity_id == ent.id) | (RelationORM.target_entity_id == ent.id)).all()
                    for r in rels:
                        if qa.relation_type and r.relation_type != qa.relation_type:
                            continue
                        candidates.append(RetrievalCandidate(
                            relation_id=str(r.id),
                            entity_id=str(ent.id),
                            retrieval_method=RetrievalMethod.STRUCTURED,
                            retrieval_score=0.9,
                            matched_terms=[ent_name]
                        ))
                    
                    # facts
                    facts = self.session.query(FactORM).filter_by(subject_id=ent.id).all()
                    for f in facts:
                        candidates.append(RetrievalCandidate(
                            fact_id=str(f.id),
                            entity_id=str(ent.id),
                            retrieval_method=RetrievalMethod.STRUCTURED,
                            retrieval_score=0.8,
                            matched_terms=[ent_name]
                        ))
                        
        # 3. FTS5
        # If we have no exact candidates, or if we want to add evidence candidates directly
        if not candidates:
            ext_ids = self.fts.search(qa.normalized_query)
            for eid in ext_ids:
                # Find any evidence tied to this extraction
                evs = self.session.query(EvidenceORM).filter_by(extraction_result_id=eid).all()
                for ev in evs:
                    candidates.append(RetrievalCandidate(
                        evidence_id=str(ev.id),
                        extraction_result_id=str(eid),
                        retrieval_method=RetrievalMethod.FTS,
                        retrieval_score=0.5
                    ))
                    
        return candidates
