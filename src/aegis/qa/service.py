import logging
from typing import Tuple
from aegis.retrieval import retrieve_and_verify
from aegis.retrieval.models import RetrievalResult
from aegis.qa.generator import AnswerGenerator
from aegis.qa.validator import ClaimValidator
from aegis.qa.models import GeneratedAnswer

logger = logging.getLogger("aegis_qa_service")

class QuestionAnswerService:
    def __init__(self, session):
        self.session = session
        self.generator = AnswerGenerator()
        self.validator = ClaimValidator()

    def answer_question(self, question: str) -> Tuple[GeneratedAnswer, RetrievalResult]:
        # 1. Retrieve and Verify Evidence (Phase 7A)
        rr = retrieve_and_verify(question, self.session)
        
        # 2. Generate Answer (Phase 7B)
        answer = self.generator.generate(rr)
        
        # 3. Validate Generated Claims
        answer = self.validator.validate(answer, rr)
        
        # 4. Fallback if validation failed
        if answer.validation_status == "FAILED":
            logger.warning("Generated answer failed validation. Returning deterministic fallback.")
            answer = self.generator._generate_fallback(rr)
            answer = self.validator.validate(answer, rr)
            
        return answer, rr
