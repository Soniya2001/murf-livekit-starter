import pytest
import sqlite3
import json
import os
from datetime import datetime, timedelta

import db
from agent import Assistant

@pytest.fixture(autouse=True)
def setup_temp_db(tmp_path):
    """Fixture to set up a temporary SQLite database for testing."""
    db_file = tmp_path / "test_finbuddy_analytics.db"
    original_db_path = db.DB_PATH
    db.DB_PATH = str(db_file)
    db.init_db()
    yield
    db.DB_PATH = original_db_path

def test_zero_call_dashboard_state():
    """Verify statistics when there are no calls in the database."""
    summary = db.get_analytics_summary()
    assert summary["total_calls"] == 0
    assert summary["successful_calls"] == 0
    assert summary["failed_calls"] == 0
    assert summary["success_rate"] == 0.0

def test_call_record_creation_and_unique_id():
    """Verify a call record is created with a unique ID and IN_PROGRESS state."""
    call_id = "test-call-unique-123"
    res = db.start_call_outcome(
        call_id=call_id,
        user_id="user-123",
        call_type="BROWSER",
        language="English"
    )
    assert res["success"] is True
    assert res["call_id"] == call_id

    # Retrieve and check
    record = db.get_call_outcome(call_id)
    assert record is not None
    assert record["user_id"] == "user-123"
    assert record["call_type"] == "BROWSER"
    assert record["outcome"] == "IN_PROGRESS"
    assert record["language"] == "English"
    assert record["started_at"] is not None

def test_successful_eligibility_outcome():
    """Verify that completing an eligibility enquiry triggers success outcome."""
    assistant = Assistant()
    assistant.call_id = "call-eligibility-abc"
    assistant.language = "English"

    # Simulate start of call in database
    db.start_call_outcome(assistant.call_id, "user-abc", "BROWSER", "English")

    # Simulate eligibility inquiry tool call
    res_str = asyncio_run(assistant.lookup_government_scheme("PMJDY", "eligibility"))
    res = json.loads(res_str)
    assert res["success"] is True
    assert assistant.call_goal_completed is True
    assert assistant.success_reason == "Eligibility check completed"
    assert assistant.scheme_name == "PMJDY"

    # Simulate call cleanup
    db.update_call_outcome(
        call_id=assistant.call_id,
        outcome="SUCCESS" if assistant.call_goal_completed else "FAILED",
        success_reason=assistant.success_reason,
        scheme_name=assistant.scheme_name,
        information_requested=assistant.information_requested,
        language=assistant.language
    )

    record = db.get_call_outcome(assistant.call_id)
    assert record["outcome"] == "SUCCESS"
    assert record["success_reason"] == "Eligibility check completed"
    assert record["scheme_name"] == "PMJDY"

def test_successful_document_list_outcome():
    """Verify that requesting a scheme's document list triggers success outcome."""
    assistant = Assistant()
    assistant.call_id = "call-docs-abc"
    assistant.language = "Tamil"

    # Simulate start of call in database
    db.start_call_outcome(assistant.call_id, "user-abc", "SIP", "Tamil")

    # Simulate document lookup tool call
    res_str = asyncio_run(assistant.lookup_government_scheme("PMMY", "documents"))
    res = json.loads(res_str)
    assert res["success"] is True
    assert assistant.call_goal_completed is True
    assert assistant.success_reason == "Document list provided"
    assert assistant.scheme_name == "PMMY"

    # Simulate call cleanup
    db.update_call_outcome(
        call_id=assistant.call_id,
        outcome="SUCCESS" if assistant.call_goal_completed else "FAILED",
        success_reason=assistant.success_reason,
        scheme_name=assistant.scheme_name,
        information_requested=assistant.information_requested,
        language=assistant.language
    )

    record = db.get_call_outcome(assistant.call_id)
    assert record["outcome"] == "SUCCESS"
    assert record["success_reason"] == "Document list provided"
    assert record["scheme_name"] == "PMMY"
    assert record["language"] == "Tamil"

def test_failed_incomplete_call():
    """Verify that hanging up early results in a FAILED outcome with incomplete reason."""
    call_id = "failed-call-incomplete"
    db.start_call_outcome(call_id, "user-failed", "BROWSER", "Hindi")
    
    # Simulate early disconnect without completing any goals
    db.update_call_outcome(
        call_id=call_id,
        outcome="FAILED",
        success_reason="Incomplete call",
        language="Hindi"
    )

    record = db.get_call_outcome(call_id)
    assert record["outcome"] == "FAILED"
    assert record["success_reason"] == "Incomplete call"
    assert record["language"] == "Hindi"

def test_failed_technical_call():
    """Verify that a technical failure results in FAILED with appropriate reason."""
    call_id = "failed-call-tech"
    db.start_call_outcome(call_id, "user-tech", "SIP", "English")

    db.update_call_outcome(
        call_id=call_id,
        outcome="FAILED",
        success_reason="Technical call failure"
    )

    record = db.get_call_outcome(call_id)
    assert record["outcome"] == "FAILED"
    assert record["success_reason"] == "Technical call failure"

def test_aggregate_call_statistics():
    """Verify summary calculations: totals, success/failure counts, and rate."""
    db.start_call_outcome("c1", "u1", "BROWSER")
    db.update_call_outcome("c1", "SUCCESS", "Document list provided")

    db.start_call_outcome("c2", "u2", "SIP")
    db.update_call_outcome("c2", "SUCCESS", "Eligibility check completed")

    db.start_call_outcome("c3", "u3", "BROWSER")
    db.update_call_outcome("c3", "FAILED", "Incomplete call")

    summary = db.get_analytics_summary()
    assert summary["total_calls"] == 3
    assert summary["successful_calls"] == 2
    assert summary["failed_calls"] == 1
    assert summary["success_rate"] == 66.67

def test_privacy_protections():
    """Verify that sensitive fields (OTP, PIN, passwords, account numbers) are not tracked/exposed."""
    # Ensure there is no column or data storing raw/sensitive payloads
    conn = sqlite3.connect(db.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(call_outcomes)")
    columns = [row[1] for row in cursor.fetchall()]
    
    sensitive_keywords = ["otp", "pin", "password", "cvv", "aadhaar", "pan", "account_number", "card_number"]
    for kw in sensitive_keywords:
        assert kw not in columns

    # Verify that we don't save raw conversation history or sensitive variables
    db.start_call_outcome("c4", "u4", "BROWSER")
    db.update_call_outcome(
        call_id="c4",
        outcome="SUCCESS",
        success_reason="Eligibility check completed",
        scheme_name="PMJDY"
    )
    record = db.get_call_outcome("c4")
    for key, val in record.items():
        if isinstance(val, str):
            for kw in sensitive_keywords:
                assert kw not in val.lower()


# Helper to run async functions synchronously in pytest
def asyncio_run(coro):
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # run in executor or new thread if loop already active
        import nest_asyncio
        nest_asyncio.apply()
        return loop.run_until_complete(coro)
    else:
        return asyncio.run(coro)
