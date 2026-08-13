import pytest
import json
import asyncio
from unittest.mock import MagicMock, AsyncMock
import db
from agent import Assistant

@pytest.fixture(autouse=True)
def setup_temp_db(tmp_path):
    """Fixture to set up a temporary SQLite database for testing."""
    db_file = tmp_path / "test_finbuddy_integration.db"
    original_db_path = db.DB_PATH
    db.DB_PATH = str(db_file)
    db.init_db()
    yield
    db.DB_PATH = original_db_path

@pytest.mark.asyncio
async def test_real_call_success_flow():
    """Verify that a successful lookup marks the call as SUCCESS if the speech is not interrupted."""
    assistant = Assistant()
    assistant.call_id = "RM_mock_active_call"
    assistant.language = "English"

    # Simulate start of call in database
    db.start_call_outcome(assistant.call_id, "user-123", "BROWSER", "English")

    # Simulate eligibility inquiry tool call - should set pending_success = True
    res_str = await assistant.lookup_government_scheme("PMJDY", "eligibility")
    res = json.loads(res_str)
    assert res["success"] is True
    assert assistant.pending_success is True
    assert assistant.call_goal_completed is False

    # Mock the SpeechCreatedEvent and Handle
    mock_speech_handle = MagicMock()
    mock_speech_handle.interrupted = False  # Not interrupted!
    
    mock_future = MagicMock()
    mock_speech_handle._done_fut = mock_future

    mock_event = MagicMock()
    mock_event.speech_handle = mock_speech_handle

    # Simulate the speech_created event registration
    callbacks = []
    def add_callback(cb):
        callbacks.append(cb)
    mock_future.add_done_callback = add_callback

    # Register the callback logic matching agent.py
    mock_room = MagicMock()
    mock_room.isconnected = MagicMock(return_value=True)
    mock_ctx = MagicMock()
    mock_ctx.room = mock_room

    def on_speech_created(ev):
        speech_handle = ev.speech_handle
        def on_done(fut):
            if not speech_handle.interrupted or mock_ctx.room.isconnected():
                if getattr(assistant, "pending_success", False):
                    assistant.call_goal_completed = True
                    assistant.success_reason = assistant.pending_success_reason
                    assistant.scheme_name = assistant.pending_scheme_name
                    assistant.information_requested = assistant.pending_information_requested
                    assistant.pending_success = False
        speech_handle._done_fut.add_done_callback(on_done)

    on_speech_created(mock_event)

    # Fire the playout completion callback
    assert len(callbacks) == 1
    callbacks[0](mock_future)

    # Check outcomes
    assert assistant.call_goal_completed is True
    assert assistant.success_reason == "Eligibility check completed"
    assert assistant.scheme_name == "PMJDY"

@pytest.mark.asyncio
async def test_real_call_voice_interrupted_flow():
    """Verify that a successful lookup marks the call as SUCCESS if it was interrupted by voice (connection remains connected)."""
    assistant = Assistant()
    assistant.call_id = "RM_mock_voice_interrupted_call"
    assistant.language = "English"

    # Simulate start of call in database
    db.start_call_outcome(assistant.call_id, "user-123", "BROWSER", "English")

    res_str = await assistant.lookup_government_scheme("PMJDY", "eligibility")
    res = json.loads(res_str)
    assert res["success"] is True

    # Speech interrupted (True) but room still connected (True)
    mock_speech_handle = MagicMock()
    mock_speech_handle.interrupted = True
    
    mock_future = MagicMock()
    mock_speech_handle._done_fut = mock_future
    mock_event = MagicMock()
    mock_event.speech_handle = mock_speech_handle

    callbacks = []
    def add_callback(cb):
        callbacks.append(cb)
    mock_future.add_done_callback = add_callback

    mock_room = MagicMock()
    mock_room.isconnected = MagicMock(return_value=True)  # Still connected!
    mock_ctx = MagicMock()
    mock_ctx.room = mock_room

    def on_speech_created(ev):
        speech_handle = ev.speech_handle
        def on_done(fut):
            if not speech_handle.interrupted or mock_ctx.room.isconnected():
                if getattr(assistant, "pending_success", False):
                    assistant.call_goal_completed = True
                    assistant.success_reason = assistant.pending_success_reason
                    assistant.scheme_name = assistant.pending_scheme_name
                    assistant.information_requested = assistant.pending_information_requested
                    assistant.pending_success = False
        speech_handle._done_fut.add_done_callback(on_done)

    on_speech_created(mock_event)
    callbacks[0](mock_future)

    # Check outcomes - should be completed successfully
    assert assistant.call_goal_completed is True
    assert assistant.success_reason == "Eligibility check completed"

@pytest.mark.asyncio
async def test_real_call_abrupt_cut_flow():
    """Verify that a successful lookup remains FAILED if the speech is interrupted and the connection is disconnected."""
    assistant = Assistant()
    assistant.call_id = "RM_mock_cut_call"
    assistant.language = "English"

    # Simulate start of call in database
    db.start_call_outcome(assistant.call_id, "user-123", "BROWSER", "English")

    res_str = await assistant.lookup_government_scheme("PMJDY", "eligibility")
    res = json.loads(res_str)
    assert res["success"] is True

    # Speech interrupted (True) and room disconnected (False)
    mock_speech_handle = MagicMock()
    mock_speech_handle.interrupted = True
    
    mock_future = MagicMock()
    mock_speech_handle._done_fut = mock_future
    mock_event = MagicMock()
    mock_event.speech_handle = mock_speech_handle

    callbacks = []
    def add_callback(cb):
        callbacks.append(cb)
    mock_future.add_done_callback = add_callback

    mock_room = MagicMock()
    mock_room.isconnected = MagicMock(return_value=False)  # Disconnected!
    mock_ctx = MagicMock()
    mock_ctx.room = mock_room

    def on_speech_created(ev):
        speech_handle = ev.speech_handle
        def on_done(fut):
            if not speech_handle.interrupted or mock_ctx.room.isconnected():
                if getattr(assistant, "pending_success", False):
                    assistant.call_goal_completed = True
                    assistant.success_reason = assistant.pending_success_reason
                    assistant.scheme_name = assistant.pending_scheme_name
                    assistant.information_requested = assistant.pending_information_requested
                    assistant.pending_success = False
        speech_handle._done_fut.add_done_callback(on_done)

    on_speech_created(mock_event)
    callbacks[0](mock_future)

    # Check outcomes - should NOT be completed
    assert assistant.call_goal_completed is False
    assert assistant.pending_success is True

@pytest.mark.asyncio
async def test_general_overview_not_success():
    """Verify that general overview lookup does NOT trigger a success outcome."""
    assistant = Assistant()
    assistant.call_id = "RM_overview_only"
    assistant.language = "English"

    db.start_call_outcome(assistant.call_id, "user-123", "BROWSER", "English")

    # Call overview -> should NOT trigger pending_success or call_goal_completed
    res_str = await assistant.lookup_government_scheme("PMJDY", "overview")
    res = json.loads(res_str)
    assert res["success"] is True
    assert assistant.pending_success is False
    assert assistant.call_goal_completed is False

@pytest.mark.asyncio
async def test_successful_objective_followed_by_bye():
    """Verify that completing a successful lookup and then hanging up cleanly results in SUCCESS."""
    assistant = Assistant()
    assistant.call_id = "RM_mock_success_bye"
    assistant.language = "English"

    db.start_call_outcome(assistant.call_id, "user-123", "BROWSER", "English")

    # Complete lookup
    res_str = await assistant.lookup_government_scheme("PMJDY", "eligibility")
    res = json.loads(res_str)
    assert res["success"] is True

    # Complete the speech playout normally
    mock_speech_handle = MagicMock()
    mock_speech_handle.interrupted = False
    mock_future = MagicMock()
    mock_speech_handle._done_fut = mock_future
    mock_event = MagicMock()
    mock_event.speech_handle = mock_speech_handle

    callbacks = []
    mock_future.add_done_callback = lambda cb: callbacks.append(cb)

    mock_room = MagicMock()
    mock_room.isconnected = MagicMock(return_value=True)
    mock_ctx = MagicMock()
    mock_ctx.room = mock_room

    def on_speech_created(ev):
        speech_handle = ev.speech_handle
        def on_done(fut):
            if not speech_handle.interrupted or mock_ctx.room.isconnected():
                if getattr(assistant, "pending_success", False):
                    assistant.call_goal_completed = True
                    assistant.success_reason = assistant.pending_success_reason
                    assistant.scheme_name = assistant.pending_scheme_name
                    assistant.information_requested = assistant.pending_information_requested
                    assistant.pending_success = False
        speech_handle._done_fut.add_done_callback(on_done)

    on_speech_created(mock_event)
    callbacks[0](mock_future)

    # Now verify it's marked as SUCCESS
    assert assistant.call_goal_completed is True
    
    # Simulate call ends cleanly
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

@pytest.mark.asyncio
async def test_tool_timeout_failed():
    """Verify that a tool timeout triggers a FAILED outcome."""
    assistant = Assistant()
    assistant.call_id = "RM_mock_timeout"
    assistant.language = "English"

    db.start_call_outcome(assistant.call_id, "user-123", "BROWSER", "English")

    # Simulate timeout lookup
    res_str = await assistant.lookup_government_scheme("timeout_scheme", "eligibility")
    res = json.loads(res_str)
    assert res["success"] is False
    assert res["error_type"] == "TIMEOUT"
    assert assistant.call_goal_completed is False

@pytest.mark.asyncio
async def test_tool_not_found_failed():
    """Verify that a NOT_FOUND tool result results in a FAILED outcome."""
    assistant = Assistant()
    assistant.call_id = "RM_mock_not_found"
    assistant.language = "English"

    db.start_call_outcome(assistant.call_id, "user-123", "BROWSER", "English")

    res_str = await assistant.lookup_government_scheme("Unknown Scheme", "eligibility")
    res = json.loads(res_str)
    assert res["success"] is False
    assert res["error_type"] == "NOT_FOUND"
    assert assistant.call_goal_completed is False
