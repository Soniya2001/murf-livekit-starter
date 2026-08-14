import pytest
import json
import asyncio
from unittest.mock import MagicMock
import db
from agent import Assistant
from government_scheme_specialist import GovernmentSchemeSpecialist
from cyber_fraud_specialist import CyberFraudSpecialist

@pytest.fixture(autouse=True)
def setup_temp_db(tmp_path):
    """Fixture to set up a temporary SQLite database for testing."""
    db_file = tmp_path / "test_finbuddy_handoff.db"
    original_db_path = db.DB_PATH
    db.DB_PATH = str(db_file)
    db.init_db()
    yield
    db.DB_PATH = original_db_path

@pytest.mark.asyncio
async def test_handoff_pmmy_question():
    """Verify that calling the handoff tool creates a Specialist with correct params."""
    assistant = Assistant()
    mock_session = MagicMock()
    
    # Mock say() returning a handle that can be awaited for playout
    mock_handle = MagicMock()
    mock_handle.wait_for_playout = MagicMock(side_effect=asyncio.sleep)
    mock_session.say = MagicMock(side_effect=lambda *args, **kwargs: asyncio.sleep(0.001, result=mock_handle))
    
    assistant._session = mock_session
    
    # Hand off
    res_str = await assistant.handoff_to_government_scheme_specialist(
        user_query="Who is eligible for PMMY?",
        scheme_name="PMMY",
        conversation_context="User asking eligibility",
        language="English",
        user_id="user_test_handoff"
    )
    res = json.loads(res_str)
    assert res["success"] is True
    
    # Verify update_agent was called on session with GovernmentSchemeSpecialist instance
    mock_session.update_agent.assert_called_once()
    called_agent = mock_session.update_agent.call_args[0][0]
    assert isinstance(called_agent, GovernmentSchemeSpecialist)
    assert called_agent.scheme_name == "PMMY"
    assert called_agent.language == "English"
    assert called_agent.user_id == "user_test_handoff"
    assert called_agent.user_query == "Who is eligible for PMMY?"

@pytest.mark.asyncio
async def test_handoff_cyber_fraud_scam():
    """Verify handoff_to_cyber_fraud_specialist correctly instantiates CyberFraudSpecialist."""
    assistant = Assistant()
    mock_session = MagicMock()
    
    # Mock say() returning a handle that can be awaited for playout
    mock_handle = MagicMock()
    mock_handle.wait_for_playout = MagicMock(side_effect=asyncio.sleep)
    mock_session.say = MagicMock(side_effect=lambda *args, **kwargs: asyncio.sleep(0.001, result=mock_handle))
    
    assistant._session = mock_session
    
    # Hand off
    res_str = await assistant.handoff_to_cyber_fraud_specialist(
        user_query="Someone called asking for my UPI PIN",
        intent="suspected_impersonation",
        conversation_context="Caller claims to represent bank",
        language="Tamil",
        user_id="user_test_fraud"
    )
    res = json.loads(res_str)
    assert res["success"] is True
    
    # Verify update_agent was called on session with CyberFraudSpecialist instance
    mock_session.update_agent.assert_called_once()
    called_agent = mock_session.update_agent.call_args[0][0]
    assert isinstance(called_agent, CyberFraudSpecialist)
    assert called_agent.intent == "suspected_impersonation"
    assert called_agent.language == "Tamil"
    assert called_agent.user_id == "user_test_fraud"
    assert called_agent.user_query == "Someone called asking for my UPI [SCRUBBED]"



@pytest.mark.asyncio
async def test_specialist_lookup_scheme_tool():
    """Verify Specialist can use lookup tool and marks goals successfully via main assistant reference."""
    assistant = Assistant()
    assistant.call_id = "handoff_call_123"
    assistant.language = "English"
    
    # Database starts
    db.start_call_outcome(assistant.call_id, "user-123", "BROWSER", "English")
    
    specialist = GovernmentSchemeSpecialist(
        main_assistant=assistant,
        user_id="user-123",
        language="English",
        scheme_name="PMJDY",
        user_query="What documents do I need for PMJDY?"
    )
    
    res_str = await specialist.lookup_government_scheme("PMJDY", "documents")
    res = json.loads(res_str)
    assert res["success"] is True
    assert assistant.pending_success is True
    assert assistant.pending_success_reason == "Document list provided"

@pytest.mark.asyncio
async def test_specialist_native_languages():
    """Verify specialist greeting scripts are generated correctly in native scripts."""
    assistant = Assistant()
    
    # Hindi
    specialist_hi = GovernmentSchemeSpecialist(
        main_assistant=assistant,
        user_id="user-hi",
        language="Hindi",
        scheme_name="PMMY"
    )
    assert "नमस्ते" in specialist_hi.instructions
    
    # Tamil
    specialist_ta = CyberFraudSpecialist(
        main_assistant=assistant,
        user_id="user-ta",
        language="Tamil",
        user_query="Scam message"
    )
    assert "வணக்கம்" in specialist_ta.instructions
    
    # Telugu
    specialist_te = CyberFraudSpecialist(
        main_assistant=assistant,
        user_id="user-te",
        language="Telugu",
        user_query="Scam link clicked"
    )
    assert "నమస్కారం" in specialist_te.instructions

@pytest.mark.asyncio
async def test_handoff_privacy_guardrail():
    """Verify sensitive credentials are not passed through handoff context."""
    assistant = Assistant()
    mock_session = MagicMock()
    # Mock say() returning a handle that can be awaited for playout
    mock_handle = MagicMock()
    mock_handle.wait_for_playout = MagicMock(side_effect=asyncio.sleep)
    mock_session.say = MagicMock(side_effect=lambda *args, **kwargs: asyncio.sleep(0.001, result=mock_handle))
    
    assistant._session = mock_session

    
    res_str = await assistant.handoff_to_cyber_fraud_specialist(
        user_query="My password is secret123",
        intent="scam_link",
        conversation_context="User entered pin 987654",
        language="English",
        user_id="user-sensitive"
    )
    
    called_agent = mock_session.update_agent.call_args[0][0]
    assert "secret123" not in called_agent.user_query
    assert "987654" not in called_agent.instructions


@pytest.mark.asyncio
async def test_handoff_back_to_main():
    """Verify that specialists can hand back to the main assistant."""
    assistant = Assistant()
    mock_session = MagicMock()
    mock_handle = MagicMock()
    mock_handle.wait_for_playout = MagicMock(side_effect=asyncio.sleep)
    mock_session.say = MagicMock(side_effect=lambda *args, **kwargs: asyncio.sleep(0.001, result=mock_handle))
    
    assistant._session = mock_session


    
    specialist = GovernmentSchemeSpecialist(
        main_assistant=assistant,
        user_id="user_back",
        language="English",
        scheme_name="APY"
    )
    
    res_str = await specialist.return_to_main_agent(
        user_query="I want to report a cyber fraud",
        intent="CYBER_FRAUD",
        language="English"
    )
    res = json.loads(res_str)
    assert res["success"] is True
    
    # Check that update_agent was called on session with the main assistant instance
    mock_session.update_agent.assert_called_once_with(assistant)
    mock_session.tts.update_options.assert_called_once_with(voice="Anisha")
    
    # Check that query and intent were successfully queued on the main assistant
    assert assistant.queued_handoff_query == "I want to report a cyber fraud"
    assert assistant.queued_handoff_intent == "CYBER_FRAUD"
    
    # Verify prompt instructions injection
    assert "IMMEDIATE DELEGATION QUEUED" in assistant.instructions
    assert "I want to report a cyber fraud" in assistant.instructions


