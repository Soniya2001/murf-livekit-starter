import os
import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from outbound_call import make_outbound_call
from agent import Assistant

# 1. Test missing or empty variables
@pytest.mark.asyncio
async def test_missing_sip_trunk_id():
    """Verify ValueError is raised if LIVEKIT_SIP_TRUNK_ID is missing."""
    with patch.dict(os.environ, {
        "LIVEKIT_URL": "wss://test-url.livekit.cloud",
        "LIVEKIT_API_KEY": "test_key",
        "LIVEKIT_API_SECRET": "test_secret",
        "LIVEKIT_SIP_TRUNK_ID": ""
    }):
        with pytest.raises(ValueError, match="LIVEKIT_SIP_TRUNK_ID environment variable is missing."):
            await make_outbound_call("+15105550100")

@pytest.mark.asyncio
async def test_missing_destination():
    """Verify ValueError is raised if destination destination is empty."""
    with patch.dict(os.environ, {
        "LIVEKIT_URL": "wss://test-url.livekit.cloud",
        "LIVEKIT_API_KEY": "test_key",
        "LIVEKIT_API_SECRET": "test_secret",
        "LIVEKIT_SIP_TRUNK_ID": "ST_XYZ"
    }):
        with pytest.raises(ValueError, match="Destination phone number/SIP URI is missing."):
            await make_outbound_call("")

@pytest.mark.asyncio
async def test_missing_livekit_url():
    """Verify ValueError is raised if LIVEKIT_URL is missing."""
    with patch.dict(os.environ, {
        "LIVEKIT_URL": "",
        "LIVEKIT_API_KEY": "test_key",
        "LIVEKIT_API_SECRET": "test_secret",
        "LIVEKIT_SIP_TRUNK_ID": "ST_XYZ"
    }):
        with pytest.raises(ValueError, match="LIVEKIT_URL environment variable is missing."):
            await make_outbound_call("+15105550100")

# 2. Test request construction
@pytest.mark.asyncio
@patch("livekit.api.LiveKitAPI")
async def test_outbound_call_request_construction(mock_lkapi_class):
    """Verify that CreateSIPParticipantRequest is built with correct arguments."""
    mock_lkapi_instance = MagicMock()
    mock_lkapi_instance.sip = MagicMock()
    
    # Mock list outbound trunks to verify it checks the trunk
    mock_trunk = MagicMock()
    mock_trunk.sip_trunk_id = "ST_MOCK_TRUNK"
    
    # Async list call return mock
    mock_list_response = MagicMock()
    mock_list_response.results = [mock_trunk]
    
    mock_lkapi_instance.sip.list_sip_outbound_trunk = AsyncMock(return_value=mock_list_response)
    
    # Mock agent dispatch service
    mock_lkapi_instance.agent_dispatch = MagicMock()
    mock_lkapi_instance.agent_dispatch.create_dispatch = AsyncMock()
    
    # Async create participant return mock
    mock_participant = MagicMock()
    mock_participant.participant_sid = "PA_MOCK_SID"
    mock_lkapi_instance.sip.create_sip_participant = AsyncMock(return_value=mock_participant)
    mock_lkapi_instance.aclose = AsyncMock()
    
    mock_lkapi_class.return_value = mock_lkapi_instance
    
    with patch.dict(os.environ, {
        "LIVEKIT_URL": "wss://test-url.livekit.cloud",
        "LIVEKIT_API_KEY": "test_key",
        "LIVEKIT_API_SECRET": "test_secret",
        "LIVEKIT_SIP_TRUNK_ID": "ST_MOCK_TRUNK",
        "AGENT_NAME": "my-agent"
    }):
        room = await make_outbound_call("+15105550100", caller_name="Ramesh")
        assert room.startswith("sip_room_")
        
        # Verify trunk list was called
        mock_lkapi_instance.sip.list_sip_outbound_trunk.assert_called_once()
        
        # Verify agent dispatch was called
        mock_lkapi_instance.agent_dispatch.create_dispatch.assert_called_once()
        
        # Verify create SIP participant was called with correct parameters
        mock_lkapi_instance.sip.create_sip_participant.assert_called_once()
        call_args = mock_lkapi_instance.sip.create_sip_participant.call_args[0][0]
        
        assert call_args.sip_trunk_id == "ST_MOCK_TRUNK"
        assert call_args.sip_call_to == "+15105550100"
        assert call_args.room_name == room
        assert call_args.participant_name == "Ramesh"
        assert call_args.participant_identity.startswith("sip_user_")

# 3. Test Greeting Logic (Assistant class system prompt replacements)
def test_assistant_greeting_non_sip():
    """Verify that a non-SIP assistant contains the default system greeting."""
    assistant = Assistant(user_id="browser_user", initial_info="")
    assert "How can I help you learn about financial schemes" in assistant.instructions
    assert "You must greet the user immediately with this exact greeting:" not in assistant.instructions

def test_assistant_greeting_sip_unknown():
    """Verify that a SIP assistant with unknown caller gets the correct outbound greeting."""
    assistant = Assistant(user_id="sip_user", initial_info="", is_sip=True)
    assert "Hello, this is FinBuddy, an AI financial information assistant. I'm calling to inform you about newly launched and updated government financial schemes" in assistant.instructions
    assert "OUTBOUND CALL ENVIRONMENT" in assistant.instructions
    assert "How can I help you learn about financial schemes" not in assistant.instructions

def test_assistant_greeting_sip_known():
    """Verify that a SIP assistant with known caller uses their name in the outbound greeting."""
    initial_info = json.dumps({"name": "Ramesh", "facts": {"schemes_checked": "APY"}})
    assistant = Assistant(user_id="sip_user", initial_info=initial_info, is_sip=True)
    assert "Hello Ramesh, this is FinBuddy, an AI financial information assistant. I'm calling to inform you" in assistant.instructions
    assert "OUTBOUND CALL ENVIRONMENT" in assistant.instructions

# 4. Safety and Refusals check via prompt content
def test_financial_guardrails_present():
    """Verify that instructions mandate strict financial safety guardrails."""
    assistant = Assistant(user_id="browser_user", is_sip=True)
    assert "Never ask for or accept an OTP" in assistant.instructions
    assert "PIN" in assistant.instructions
    assert "password" in assistant.instructions
    assert "bank account number" in assistant.instructions
