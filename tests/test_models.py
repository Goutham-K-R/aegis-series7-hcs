from uuid import uuid4
from aegis.models.domain import Fact, FactStatus

def test_fact_model_serialization():
    subject_id = uuid4()
    fact = Fact(
        subject_id=subject_id,
        predicate="has_pressure",
        value="200",
        unit="bar",
        status=FactStatus.ASSERTED
    )
    assert fact.predicate == "has_pressure"
    assert fact.value == "200"
    assert fact.status == FactStatus.ASSERTED
    assert fact.subject_id == subject_id
    
    # Test JSON serialization
    json_data = fact.model_dump_json()
    assert "has_pressure" in json_data
