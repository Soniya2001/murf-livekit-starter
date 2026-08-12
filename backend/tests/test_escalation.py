import pytest
import sqlite3
import json
import os
import re
from datetime import datetime
from unittest.mock import AsyncMock, patch

import db
from agent import Assistant

@pytest.fixture(autouse=True)
def setup_temp_db(tmp_path):
    """Fixture to set up a temporary SQLite database for testing."""
    db_file = tmp_path / "test_finbuddy.db"
    original_db_path = db.DB_PATH
    db.DB_PATH = str(db_file)
    db.init_db()
    yield
    db.DB_PATH = original_db_path

@pytest.mark.asyncio
async def test_normal_question_no_escalation():
    """Verify that a normal query does not trigger escalation database changes."""
    # Ensure database is empty initially
    escalations = db.list_escalations()
    assert len(escalations) == 0

    assistant = Assistant()
    # Looking up a normal scheme shouldn't trigger create_escalation
    res = await assistant.lookup_government_scheme("PMMY", "overview")
    assert "MUDRA" in res
    
    escalations = db.list_escalations()
    assert len(escalations) == 0

@pytest.mark.asyncio
async def test_create_escalation_success():
    """Verify that create_escalation tool creates record successfully with random reference ID."""
    assistant = Assistant()
    raw_res = await assistant.create_escalation(
        user_id="caller-123",
        issue_summary="Suspected UPI Fraud",
        what_happened="User received a scam request for 5000 INR",
        agent_checks="Advised not to click random payment links",
        urgency="high",
        language="Tamil",
        preferred_follow_up="phone",
        caller_name="Ramesh"
    )
    res = json.loads(raw_res)
    assert res["success"] is True
    assert res["status"] == "OPEN"
    ref_id = res["reference_id"]
    assert ref_id.startswith("FIN-")
    
    # Retrieve from db
    record = db.get_escalation(ref_id)
    assert record is not None
    assert record["user_id"] == "caller-123"
    assert record["caller_name"] == "Ramesh"
    assert record["issue_summary"] == "Suspected UPI Fraud"
    assert record["urgency"] == "high"
    assert record["language"] == "Tamil"
    assert record["preferred_follow_up"] == "phone"
    assert record["status"] == "OPEN"

@pytest.mark.asyncio
async def test_create_escalation_sanitization():
    """Verify sensitive information (OTP, PIN, Account numbers) is rejected/removed from summary fields."""
    assistant = Assistant()
    raw_res = await assistant.create_escalation(
        user_id="caller-999",
        issue_summary="Account issue with number 123456789012 and OTP 987654",
        what_happened="I shared my pin 1111 and password secret123",
        agent_checks="Warned customer",
        urgency="high",
        language="English",
        preferred_follow_up="email",
        caller_name="Suresh"
    )
    res = json.loads(raw_res)
    ref_id = res["reference_id"]
    record = db.get_escalation(ref_id)
    
    # Ensure sensitive credentials aren't present in plain text
    assert "123456789012" not in record["issue_summary"]
    assert "987654" not in record["issue_summary"]
    assert "1111" not in record["what_happened"]
    assert "secret123" not in record["what_happened"]
    
    # Check that they were replaced with placeholder/scrubbed values
    assert "SCRUBBED" in record["issue_summary"]
    assert "SCRUBBED" in record["what_happened"]

def test_database_status_updates():
    """Verify listing escalations and updating status works correctly."""
    ref_id = "FIN-20260812-0001"
    db.create_escalation(
        user_id="test-user",
        reference_id=ref_id,
        caller_name="Test Caller",
        issue_summary="General support needed",
        what_happened="Nothing special",
        agent_checks="None",
        urgency="medium",
        language="Hindi",
        preferred_follow_up="email"
    )
    
    escalations = db.list_escalations(status="OPEN")
    assert len(escalations) == 1
    assert escalations[0]["reference_id"] == ref_id
    
    # Update status to IN_REVIEW
    updated = db.update_escalation_status(ref_id, "IN_REVIEW")
    assert updated is True
    
    record = db.get_escalation(ref_id)
    assert record["status"] == "IN_REVIEW"
    
    # Verify filters
    open_list = db.list_escalations(status="OPEN")
    assert len(open_list) == 0
    
    review_list = db.list_escalations(status="IN_REVIEW")
    assert len(review_list) == 1
