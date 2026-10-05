with open('tests/test_retrieval.py', 'a') as f:
    f.write('''
def test_a17_alarm_query(session):
    setup_db(session)
    res = retrieve_and_verify("What does alarm A17 mean?", session)
    assert res.decision in [VerificationDecision.INSUFFICIENT_EVIDENCE, VerificationDecision.VERIFIED]

def test_a18_alarm_query(session):
    setup_db(session)
    res = retrieve_and_verify("What does alarm A18 mean?", session)
    assert res.decision in [VerificationDecision.INSUFFICIENT_EVIDENCE, VerificationDecision.VERIFIED]

def test_a19_alarm_query(session):
    setup_db(session)
    res = retrieve_and_verify("What does alarm A19 mean?", session)
    assert res.decision in [VerificationDecision.INSUFFICIENT_EVIDENCE, VerificationDecision.VERIFIED]

def test_ps04a_temperature_query(session):
    setup_db(session)
    res = retrieve_and_verify("What is the maximum continuous temperature for PS-04A?", session)
    assert res.decision in [VerificationDecision.INSUFFICIENT_EVIDENCE, VerificationDecision.VERIFIED]

def test_3phase_400v_compatibility_query(session):
    setup_db(session)
    res = retrieve_and_verify("Is it compatible with 3-phase 400 V?", session)
    assert res.decision in [VerificationDecision.INSUFFICIENT_EVIDENCE, VerificationDecision.VERIFIED]

def test_unknown_entity_query(session):
    setup_db(session)
    res = retrieve_and_verify("What is the pressure of Q1?", session)
    assert res.decision in [VerificationDecision.INSUFFICIENT_EVIDENCE, VerificationDecision.VERIFIED]

def test_explicit_firmware_31(session):
    setup_db(session)
    res = retrieve_and_verify("firmware 3.1", session)
    assert res.query_analysis.firmware_context == "3.1"

def test_explicit_firmware_321(session):
    setup_db(session)
    res = retrieve_and_verify("firmware 3.2.1", session)
    assert res.query_analysis.firmware_context == "3.2.1"

def test_planned_33(session):
    setup_db(session)
    res = retrieve_and_verify("planned 3.3", session)
    assert res.decision in [VerificationDecision.INSUFFICIENT_EVIDENCE, VerificationDecision.VERIFIED]
''')
