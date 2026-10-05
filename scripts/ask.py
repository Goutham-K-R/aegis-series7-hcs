import sys
import argparse
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aegis.config import settings
from aegis.qa import QuestionAnswerService

logging.basicConfig(level=logging.WARNING)

def main():
    parser = argparse.ArgumentParser(description="Ask a question to the Aegis Knowledge System.")
    parser.add_argument("question", type=str, help="The question string")
    args = parser.parse_args()
    
    engine = create_engine(settings.db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    service = QuestionAnswerService(session)
    answer, rr = service.answer_question(args.question)
    
    print("Answer")
    print("------")
    print(answer.text)
    
    print("\nEvidence")
    print("--------")
    for e in rr.verified_evidence:
        print(f"[{e.evidence_id}]")
        print(f"Document: {e.document_id}")
        print(f"Location: {e.document_location}")
        print(f"Method: {e.extraction_method}")
        print(f"Reliability: {e.extraction_reliability}")
        print("")
        
    print("Decision:")
    print(rr.decision.value)
    
    print("\nClaims")
    print("------")
    for claim in answer.claims:
        print("Claim:")
        print(claim.text)
        print("Evidence:")
        for eid in claim.evidence_ids:
            print(f"[{eid}]")
        print("")

if __name__ == "__main__":
    main()
