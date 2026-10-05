import json
import logging
from uuid import uuid4
from aegis.config import settings
from aegis.retrieval.models import RetrievalResult, VerificationDecision
from aegis.qa.models import GeneratedAnswer, Claim, ClaimType

logger = logging.getLogger("aegis_qa")

class AnswerGenerator:
    def generate(self, retrieval_result: RetrievalResult) -> GeneratedAnswer:
        # Decision Gating
        if retrieval_result.decision == VerificationDecision.CONFLICTED:
            return self._generate_conflict(retrieval_result)
        elif retrieval_result.decision == VerificationDecision.INSUFFICIENT_EVIDENCE:
            return self._generate_insufficient(retrieval_result)
        elif retrieval_result.decision == VerificationDecision.NOT_APPLICABLE:
            return self._generate_not_applicable(retrieval_result)
        elif retrieval_result.decision == VerificationDecision.NOT_VERIFIED:
            return self._generate_not_verified(retrieval_result)
            
        # If VERIFIED, try LLM, fallback if needed
        if not settings.llm_api_key:
            logger.warning("LLM API key not found. Using deterministic fallback generator.")
            return self._generate_fallback(retrieval_result)
            
        return self._call_llm(retrieval_result)
        
    def _generate_conflict(self, rr: RetrievalResult) -> GeneratedAnswer:
        text = "The supplied documentation contains conflicting applicable values. I cannot determine a single value from the verified evidence.\n\n"
        claims = []
        
        # Group verified evidence by subject and predicate to find actual conflicts
        by_subj_pred = {}
        for ev in rr.verified_evidence:
            key = (ev.subject, ev.predicate)
            if key not in by_subj_pred:
                by_subj_pred[key] = []
            by_subj_pred[key].append(ev)
            
        conflicting_groups = []
        for key, evs in by_subj_pred.items():
            values = set(e.value for e in evs)
            if len(values) > 1:
                conflicting_groups.append((key, evs))
                
        # If somehow no groups have multiple values, just fallback to showing all
        if not conflicting_groups:
            conflicting_groups = [((None, None), rr.verified_evidence)]
        
        for (subj, pred), evs in conflicting_groups:
            if subj and pred:
                group_text = f"Conflicting evidence was found for {subj} {pred}."
            else:
                group_text = "Conflicting evidence was found."
                
            # Sort by value just to be deterministic
            evs_sorted = sorted(evs, key=lambda x: str(x.value))
            
            # Create a SINGLE claim for the conflict group, but include ALL evidence IDs for it.
            # The prompt asks for:
            # Value A: 180 bar
            # Value B: 200 bar
            claim_text = group_text + "\n"
            evidence_ids = []
            
            for i, ev in enumerate(evs_sorted):
                val_str = f"{ev.value}"
                if ev.unit:
                    val_str += f" {ev.unit}"
                
                label = chr(ord('A') + (i % 26))
                claim_text += f"- Value {label}: {val_str} [{ev.evidence_id}]\n"
                evidence_ids.append(ev.evidence_id)
                
            text += claim_text + "\n"
            
            claims.append(Claim(
                claim_id=str(uuid4()),
                text=claim_text.strip(),
                evidence_ids=evidence_ids,
                confidence=1.0,
                claim_type=ClaimType.CONFLICT
            ))
            
        return GeneratedAnswer(text=text.strip(), claims=claims, is_fallback=True)

    def _generate_insufficient(self, rr: RetrievalResult) -> GeneratedAnswer:
        text = "The supplied documentation does not establish the requested value."
        return GeneratedAnswer(
            text=text,
            claims=[Claim(
                claim_id=str(uuid4()),
                text=text,
                evidence_ids=[],
                confidence=1.0,
                claim_type=ClaimType.ABSTENTION
            )],
            is_fallback=True
        )
        
    def _generate_not_applicable(self, rr: RetrievalResult) -> GeneratedAnswer:
        text = "The retrieved evidence does not apply to the requested context."
        return GeneratedAnswer(
            text=text,
            claims=[Claim(
                claim_id=str(uuid4()),
                text=text,
                evidence_ids=[],
                confidence=1.0,
                claim_type=ClaimType.ABSTENTION
            )],
            is_fallback=True
        )

    def _generate_not_verified(self, rr: RetrievalResult) -> GeneratedAnswer:
        text = "No verified evidence was found for this query."
        return GeneratedAnswer(
            text=text,
            claims=[Claim(
                claim_id=str(uuid4()),
                text=text,
                evidence_ids=[],
                confidence=1.0,
                claim_type=ClaimType.ABSTENTION
            )],
            is_fallback=True
        )

    def _generate_fallback(self, rr: RetrievalResult) -> GeneratedAnswer:
        if not rr.verified_evidence:
            return self._generate_insufficient(rr)
            
        claims = []
        text_lines = []
        for ev in rr.verified_evidence:
            val_str = ""
            if ev.validity_info:
                vmin = ev.validity_info.get('fw_version_min')
                vmax = ev.validity_info.get('fw_version_max')
                if vmin and vmax: val_str = f" (for FW {vmin} to {vmax})"
                elif vmin: val_str = f" (for FW >= {vmin})"
                elif vmax: val_str = f" (for FW <= {vmax})"

            if ev.value is not None:
                fact_str = f"{ev.subject} {ev.predicate}: {ev.value} {ev.unit if ev.unit else ''}{val_str}".strip() + "."
                text_lines.append(fact_str + f" [{ev.evidence_id}]")
                claims.append(Claim(
                    claim_id=str(uuid4()),
                    text=fact_str,
                    evidence_ids=[ev.evidence_id],
                    confidence=1.0,
                    claim_type=ClaimType.FACTUAL
                ))
            else:
                # Relation fallback
                fact_str = f"{ev.subject} {ev.predicate}{val_str}."
                text_lines.append(fact_str + f" [{ev.evidence_id}]")
                claims.append(Claim(
                    claim_id=str(uuid4()),
                    text=fact_str,
                    evidence_ids=[ev.evidence_id],
                    confidence=1.0,
                    claim_type=ClaimType.FACTUAL
                ))
        
        return GeneratedAnswer(text="\n".join(text_lines), claims=claims, is_fallback=True)

    def _call_llm(self, rr: RetrievalResult) -> GeneratedAnswer:
        # In this environment, we just use deterministic fallback since we don't have a real LLM.
        # If we had a real LLM, we would build the prompt with rr and parse the output JSON.
        return self._generate_fallback(rr)
