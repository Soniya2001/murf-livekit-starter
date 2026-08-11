import asyncio
import os
import sys
import random
import argparse
import logging
from dotenv import load_dotenv
from livekit import api
from livekit.protocol.sip import ListSIPOutboundTrunkRequest

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("outbound_call")

# Load environment variables
load_dotenv(".env.local")

async def make_outbound_call(
    destination: str,
    caller_name: str | None = None
) -> str:
    """Initiates an outbound SIP call using LiveKit API.
    
    Args:
        destination: The destination phone number or SIP URI.
        caller_name: Optional caller name.
        
    Returns:
        The room name that the SIP participant joins.
    """
    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    trunk_id = os.getenv("LIVEKIT_SIP_TRUNK_ID")
    
    # 1. Validation
    if not url:
        raise ValueError("LIVEKIT_URL environment variable is missing.")
    if not api_key:
        raise ValueError("LIVEKIT_API_KEY environment variable is missing.")
    if not api_secret:
        raise ValueError("LIVEKIT_API_SECRET environment variable is missing.")
    if not trunk_id:
        raise ValueError("LIVEKIT_SIP_TRUNK_ID environment variable is missing.")
    if not destination:
        raise ValueError("Destination phone number/SIP URI is missing.")
        
    # Convert WebSocket URL to HTTP/HTTPS for LiveKitAPI client
    if url.startswith("wss://"):
        api_url = url.replace("wss://", "https://")
    elif url.startswith("ws://"):
        api_url = url.replace("ws://", "http://")
    else:
        api_url = url

    logger.info("Initializing LiveKitAPI client...")
    lkapi = api.LiveKitAPI(url=api_url, api_key=api_key, api_secret=api_secret)
    
    try:
        # 2. Check outbound trunk configuration
        logger.info(f"Listing outbound trunks to verify trunk ID: {trunk_id}...")
        try:
            outbound_trunks = await lkapi.sip.list_sip_outbound_trunk(ListSIPOutboundTrunkRequest())
            
            # Robust check across potential list structures
            trunks_list = []
            if hasattr(outbound_trunks, "results"):
                trunks_list = outbound_trunks.results
            elif isinstance(outbound_trunks, list):
                trunks_list = outbound_trunks
            else:
                trunks_list = getattr(outbound_trunks, "items", [])
                
            found = False
            for trunk in trunks_list:
                t_id = getattr(trunk, "sip_trunk_id", None) or getattr(trunk, "id", None)
                if t_id == trunk_id:
                    found = True
                    break
                    
            if not found:
                raise ValueError(f"Configured SIP Trunk ID '{trunk_id}' was not found on the LiveKit server. Outbound calling is not available.")
            logger.info("SIP trunk configuration verified successfully.")
        except Exception as e:
            if isinstance(e, ValueError):
                raise e
            logger.warning(f"Unable to list/verify trunks dynamically due to error: {e}. Proceeding with call initiation anyway.")

        # 3. Create room and invite participant
        room_name = f"sip_room_{random.randint(10000, 99999)}"
        participant_identity = f"sip_user_{random.randint(1000, 9999)}"
        p_name = caller_name or "SIP Guest"
        
        agent_name = os.getenv("AGENT_NAME")
        if agent_name:
            logger.info(f"Dispatching agent '{agent_name}' to room '{room_name}'...")
            try:
                req = api.CreateAgentDispatchRequest(
                    room=room_name,
                    agent_name=agent_name
                )
                await lkapi.agent_dispatch.create_dispatch(req)
                logger.info(f"Agent '{agent_name}' dispatched successfully to room '{room_name}'.")
            except Exception as e:
                logger.warning(f"Failed to explicitly dispatch agent: {e}. Falling back to default routing.")

        logger.info(f"Initiating outbound SIP call to '{destination}' in room '{room_name}'...")
        request = api.CreateSIPParticipantRequest(
            sip_trunk_id=trunk_id,
            sip_call_to=destination,
            room_name=room_name,
            participant_identity=participant_identity,
            participant_name=p_name,
        )
        
        participant = await lkapi.sip.create_sip_participant(request)
        p_id = getattr(participant, "participant_id", None) or getattr(participant, "participant_identity", "unknown")
        logger.info(f"Call initiated successfully. SIP participant ID: {p_id}")
        return room_name
        
    finally:
        await lkapi.aclose()

def main():
    parser = argparse.ArgumentParser(description="Initiate outbound FinBuddy voice call.")
    parser.add_argument(
        "--to",
        help="Destination phone number/SIP URI (defaults to OUTBOUND_CALL_TO env var)",
        default=os.getenv("OUTBOUND_CALL_TO")
    )
    parser.add_argument(
        "--name",
        help="Caller name if known",
        default=None
    )
    args = parser.parse_args()
    
    destination = args.to
    if not destination:
        print("Error: Destination phone number or SIP URI must be configured via --to or OUTBOUND_CALL_TO environment variable.")
        sys.exit(1)
        
    # Check other variables exist for warning output
    has_trunk = bool(os.getenv("LIVEKIT_SIP_TRUNK_ID"))
    
    print("Starting outbound FinBuddy call...")
    print(f"Destination configured: {'yes' if destination else 'no'}")
    print(f"SIP trunk configured: {'yes' if has_trunk else 'no'}")
    
    try:
        room_name = asyncio.run(make_outbound_call(destination, args.name))
        print(f"Call initiated successfully. Room: {room_name}")
    except Exception as e:
        print(f"Outbound call failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
