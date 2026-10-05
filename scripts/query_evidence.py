import sys
import argparse
import json
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aegis.config import settings
from aegis.retrieval import retrieve_and_verify

logging.basicConfig(level=logging.WARNING)

def main():
    parser = argparse.ArgumentParser(description="Query Aegis Evidence deterministically.")
    parser.add_argument("query", type=str, help="The query string")
    args = parser.parse_args()
    
    engine = create_engine(settings.db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    result = retrieve_and_verify(args.query, session)
    
    print(f"Query: {result.query}")
    print(f"Entity: {result.query_analysis.entities}")
    print(f"Predicate: {result.query_analysis.requested_predicate}")
    print(f"Firmware context: {result.query_analysis.firmware_context}")
    print("\nCandidates")
    print("---------")
    for i, c in enumerate(result.candidates, 1):
        if c.fact_id:
            print(f"{i}. Fact ID: {c.fact_id} (Method: {c.retrieval_method.value})")
        elif c.relation_id:
            print(f"{i}. Relation ID: {c.relation_id} (Method: {c.retrieval_method.value})")
        else:
            print(f"{i}. Evidence ID: {c.evidence_id} (Method: {c.retrieval_method.value})")
            
    print("\nVerification")
    print("------------")
    print(f"Decision: {result.decision.value}")
    print(f"Reason: {result.reason}")
    
    print("\nEvidence")
    print("--------")
    for e in result.verified_evidence:
        print(f"- Evidence ID: {e.evidence_id}")
        print(f"  Document ID: {e.document_id}")
        print(f"  Location: {e.document_location}")
        print(f"  Method: {e.extraction_method}")
        print(f"  Reliability: {e.extraction_reliability}")
        print(f"  Validity: {e.validity_info}")
        print("")

if __name__ == "__main__":
    main()
