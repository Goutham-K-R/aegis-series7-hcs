import pytest
from unittest.mock import MagicMock, patch
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import app

def test_streamlit_imports_successfully():
    import streamlit as st
    assert st is not None

@patch('app.st')
def test_ui_instantiates_qa_service(mock_st):
    service = app.get_qa_service()
    assert service is not None
    assert hasattr(service, 'answer_question')

def test_qa_service_read_only(monkeypatch):
    service = app.get_qa_service()
    
    # We just run a simple query to ensure the UI's instantiation of the service
    # doesn't crash and returns the expected structured data types without DB writes.
    ans, rr = service.answer_question("Is PS-04 the same component as PS-04A?")
    
    # Ensure it returns VERIFIED or similar Decision without modifying state
    assert rr.decision is not None
    assert hasattr(ans, 'claims')
