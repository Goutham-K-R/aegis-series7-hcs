import logging
from uuid import uuid4, UUID
from sqlalchemy.orm import Session
from aegis.storage.orm import (
    ExtractionResultORM, DocumentLocationORM, DocumentORM,
    EntityORM, AliasORM, FactORM, RelationORM, EvidenceORM, ValidityORM
)
from aegis.models.domain import FactStatus
from aegis.knowledge.extractors import KnowledgeExtractorFactory

logger = logging.getLogger(__name__)

class KnowledgeBuilder:
    def __init__(self, session: Session, mode: str = "hybrid"):
        self.session = session
        self.mode = mode
        self.stats = {
            "processed": 0,
            "entities": 0,
            "aliases": 0,
            "facts": 0,
            "relations": 0,
            "validities": 0,
            "evidence_links": 0,
            "rejected": 0,
            "ocr_skipped": 0,
            "deterministic": 0,
            "model_candidates": 0
        }

    def _get_or_create_entity(self, name: str, etype: str) -> UUID:
        e = self.session.query(EntityORM).filter_by(canonical_name=name).first()
        if not e:
            e = EntityORM(id=uuid4(), canonical_name=name, entity_type=etype)
            self.session.add(e)
            self.session.flush()
            self.stats["entities"] += 1
        return e.id

    def build_knowledge(self):
        results = self.session.query(ExtractionResultORM).all()
        
        for ext in results:
            self.stats["processed"] += 1
            
            if ext.extraction_status == "REQUIRES_OCR":
                self.stats["ocr_skipped"] += 1
                continue
                
            if ext.extraction_status not in ("SUCCESS", "PARTIAL"):
                continue
                
            doc = self.session.query(DocumentORM).filter_by(id=ext.document_id).first()
            loc = self.session.query(DocumentLocationORM).filter_by(id=ext.document_location_id).first()
            
            extractor = KnowledgeExtractorFactory.get_extractor(doc.format)
            if self.mode == "model" and doc.format not in ("JSON", "XLSX"):
                from aegis.knowledge.semantic import LLMSemanticExtractor
                extractor = LLMSemanticExtractor()
            elif self.mode == "hybrid" and doc.format not in ("JSON", "XLSX"):
                from aegis.knowledge.semantic import LLMSemanticExtractor
                extractor = LLMSemanticExtractor()
            elif self.mode == "deterministic" and doc.format not in ("JSON", "XLSX"):
                from aegis.knowledge.extractors import RuleBasedTextExtractor
                extractor = RuleBasedTextExtractor()
                
            try:
                from aegis.knowledge.semantic import SemanticExtractor
                if isinstance(extractor, SemanticExtractor):
                    candidates = extractor.extract(ext)
                else:
                    candidates = extractor.extract(ext, loc, doc)
            except Exception as e:
                logger.error(f"Failed to extract knowledge from {ext.id}: {e}")
                self.stats["rejected"] += 1
                continue
                
            has_validities = hasattr(candidates, 'validities') and candidates.validities
            if not (candidates.facts or candidates.aliases or candidates.relations or has_validities):
                continue
                
            from aegis.storage.orm import SourceORM
            src = self.session.query(SourceORM).filter_by(document_id=doc.id).first()
            if not src:
                src = SourceORM(id=uuid4(), document_id=doc.id, authority="UNVERIFIED")
                self.session.add(src)
                self.session.flush()
            source_id_to_use = src.id
            
            if hasattr(candidates, 'validities'):
                for v in candidates.validities:
                    # Idempotency check for validities
                    existing = self.session.query(ValidityORM).join(EvidenceORM).filter(
                        ValidityORM.fw_version_min == v.fw_version_min,
                        ValidityORM.fw_version_max == v.fw_version_max,
                        EvidenceORM.extraction_result_id == ext.id
                    ).first()
                    if existing:
                        continue
                        
                    val = ValidityORM(
                        id=uuid4(),
                        fw_version_min=v.fw_version_min,
                        fw_version_max=v.fw_version_max,
                        date_effective=v.date_effective,
                        date_superseded=v.date_superseded
                    )
                    self.session.add(val)
                    self.stats["validities"] += 1
                    
                    ev = EvidenceORM(
                        id=uuid4(),
                        validity_id=val.id,
                        extraction_result_id=ext.id,
                        source_id=source_id_to_use
                    )
                    self.session.add(ev)
                    self.stats["evidence_links"] += 1
            
            for ent in candidates.entities:
                self._get_or_create_entity(ent.canonical_name, ent.entity_type.value)
                
            for f in candidates.facts:
                subj_id = self._get_or_create_entity(f.subject, f.subject_type.value)
                
                validity_id = None
                if f.fw_version_min or f.fw_version_max:
                    # check for validity idempotency for this fact
                    existing_val = self.session.query(ValidityORM).join(EvidenceORM).filter(
                        ValidityORM.fw_version_min == f.fw_version_min,
                        ValidityORM.fw_version_max == f.fw_version_max,
                        EvidenceORM.extraction_result_id == ext.id
                    ).first()
                    
                    if existing_val:
                        validity_id = existing_val.id
                    else:
                        val = ValidityORM(
                            id=uuid4(),
                            fw_version_min=f.fw_version_min,
                            fw_version_max=f.fw_version_max,
                            date_effective=f.validity_context.date_effective if f.validity_context else None,
                            date_superseded=f.validity_context.date_superseded if f.validity_context else None
                        )
                        self.session.add(val)
                        
                        ev = EvidenceORM(
                            id=uuid4(),
                            validity_id=val.id,
                            extraction_result_id=ext.id,
                            source_id=subj_id
                        )
                        self.session.add(ev)
                        validity_id = val.id

                # Idempotency check
                existing = self.session.query(FactORM).join(EvidenceORM).filter(
                    FactORM.subject_id == subj_id,
                    FactORM.predicate == f.predicate,
                    FactORM.value == f.value,
                    EvidenceORM.extraction_result_id == ext.id
                ).first()
                if existing:
                    if validity_id and not existing.validity_id:
                        existing.validity_id = validity_id
                        self.session.add(existing)
                    continue

                fact = FactORM(
                    id=uuid4(),
                    subject_id=subj_id,
                    predicate=f.predicate,
                    value=f.value,
                    unit=f.unit,
                    validity_id=validity_id,
                    status=FactStatus.ASSERTED.value
                )
                self.session.add(fact)
                self.stats["facts"] += 1
                
                ev = EvidenceORM(
                    id=uuid4(),
                    fact_id=fact.id,
                    extraction_result_id=ext.id,
                    source_id=source_id_to_use
                )
                self.session.add(ev)
                self.stats["evidence_links"] += 1
                
            for a in candidates.aliases:
                ent_id = self._get_or_create_entity(a.canonical_name, a.entity_type.value)
                
                # Idempotency check
                existing = self.session.query(AliasORM).join(EvidenceORM).filter(
                    AliasORM.canonical_entity_id == ent_id,
                    AliasORM.alias_name == a.alias_name,
                    EvidenceORM.extraction_result_id == ext.id
                ).first()
                if existing:
                    continue
                
                alias = AliasORM(
                    id=uuid4(),
                    canonical_entity_id=ent_id,
                    alias_name=a.alias_name,
                    is_confirmed=a.is_confirmed,
                    resolution_method=a.resolution_method.value
                )
                self.session.add(alias)
                self.stats["aliases"] += 1
                
                ev = EvidenceORM(
                    id=uuid4(),
                    alias_id=alias.id,
                    extraction_result_id=ext.id,
                    source_id=source_id_to_use
                )
                self.session.add(ev)
                self.stats["evidence_links"] += 1
                
            for r in candidates.relations:
                src_id = self._get_or_create_entity(r.source_entity, "COMPONENT")
                tgt_id = self._get_or_create_entity(r.target_entity, "COMPONENT")
                
                # Idempotency check
                existing = self.session.query(RelationORM).join(EvidenceORM).filter(
                    RelationORM.source_entity_id == src_id,
                    RelationORM.target_entity_id == tgt_id,
                    RelationORM.relation_type == r.relation_type.value,
                    EvidenceORM.extraction_result_id == ext.id
                ).first()
                if existing:
                    continue
                
                rel = RelationORM(
                    id=uuid4(),
                    source_entity_id=src_id,
                    target_entity_id=tgt_id,
                    relation_type=r.relation_type.value
                )
                self.session.add(rel)
                self.stats["relations"] += 1
                
                ev = EvidenceORM(
                    id=uuid4(),
                    relation_id=rel.id,
                    extraction_result_id=ext.id,
                    source_id=source_id_to_use
                )
                self.session.add(ev)
                self.stats["evidence_links"] += 1
                
        self.session.commit()
        return self.stats
