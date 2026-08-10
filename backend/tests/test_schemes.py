import pytest
import asyncio
import json
from schemes_data import lookup_scheme_db
from agent import Assistant

@pytest.mark.asyncio
async def test_lookup_scheme_success():
    """Verify lookup returns successful structured data for valid schemes."""
    res = await lookup_scheme_db("PMJDY", "eligibility")
    assert res["success"] is True
    assert "Pradhan Mantri Jan Dhan Yojana" in res["scheme_name"]
    assert res["info_type"] == "eligibility"
    assert "10 years" in res["content"]
    assert "source" in res
    assert "retrieved_at" in res
    assert "source_updated_at" in res

@pytest.mark.asyncio
async def test_lookup_scheme_not_found():
    """Verify lookup returns a NOT_FOUND error for non-existent schemes."""
    res = await lookup_scheme_db("XYZ Financial Scheme", "overview")
    assert res["success"] is False
    assert res["error_type"] == "NOT_FOUND"
    assert "curated government-scheme dataset" in res["message"]

@pytest.mark.asyncio
async def test_lookup_scheme_timeout_simulation():
    """Verify that lookup raises TimeoutError when the scheme contains 'timeout'."""
    with pytest.raises(asyncio.TimeoutError):
        await lookup_scheme_db("timeout-pmjdy", "overview")

@pytest.mark.asyncio
async def test_lookup_scheme_field_fallback():
    """Verify that invalid fields fallback to 'overview'."""
    res = await lookup_scheme_db("APY", "invalid_field")
    assert res["success"] is True
    assert res["info_type"] == "overview"
    assert "guaranteed monthly pension" in res["content"]

@pytest.mark.asyncio
async def test_assistant_tool_success():
    """Test that the Assistant class tool method executes correctly for valid inputs."""
    assistant = Assistant()
    raw_res = await assistant.lookup_government_scheme("PMJDY", "eligibility")
    res = json.loads(raw_res)
    assert res["success"] is True
    assert "pmjdy" in res["source"]

@pytest.mark.asyncio
async def test_assistant_tool_not_found():
    """Test that the Assistant class tool method correctly handles not found schemes."""
    assistant = Assistant()
    raw_res = await assistant.lookup_government_scheme("XYZ Financial Scheme", "overview")
    res = json.loads(raw_res)
    assert res["success"] is False
    assert res["error_type"] == "NOT_FOUND"

@pytest.mark.asyncio
async def test_assistant_tool_timeout():
    """Test that the Assistant class tool method handles simulated timeouts successfully."""
    assistant = Assistant()
    raw_res = await assistant.lookup_government_scheme("pmjdy-timeout", "overview")
    res = json.loads(raw_res)
    assert res["success"] is False
    assert res["error_type"] == "TIMEOUT"

@pytest.mark.asyncio
async def test_assistant_tool_security_block():
    """Test that the Assistant class tool method blocks queries containing sensitive details."""
    assistant = Assistant()
    raw_res = await assistant.lookup_government_scheme("PMJDY with OTP", "overview")
    res = json.loads(raw_res)
    assert res["success"] is False
    assert res["error_type"] == "SECURITY_REFUSAL"

# --- DAY 5 EXPANDED PMMY TESTS ---

@pytest.mark.asyncio
async def test_lookup_pmmy_by_abbreviation():
    """Test PMMY lookup by abbreviation works."""
    res = await lookup_scheme_db("PMMY", "overview")
    assert res["success"] is True
    assert "Pradhan Mantri MUDRA Yojana" in res["scheme_name"]

@pytest.mark.asyncio
async def test_lookup_pmmy_by_full_name():
    """Test PMMY lookup by full name works."""
    res = await lookup_scheme_db("Pradhan Mantri MUDRA Yojana", "overview")
    assert res["success"] is True
    assert "mudra" in res["source"]

@pytest.mark.asyncio
async def test_lookup_pmmy_by_alias():
    """Test PMMY lookup by short alias works."""
    res = await lookup_scheme_db("PM Mudra", "overview")
    assert res["success"] is True
    assert "MUDRA" in res["scheme_name"]

@pytest.mark.asyncio
async def test_lookup_pmmy_loan_query():
    """Test PMMY lookup by common voice query phrase works."""
    res = await lookup_scheme_db("Mudra loan", "overview")
    assert res["success"] is True
    assert "Shishu" in res["content"] or "loans up to 10 Lakh" in res["content"]

@pytest.mark.asyncio
async def test_pmmy_eligibility():
    """Test PMMY eligibility information retrieval works."""
    res = await lookup_scheme_db("PMMY", "eligibility")
    assert res["success"] is True
    assert res["info_type"] == "eligibility"
    assert "non-farm sector" in res["content"]

@pytest.mark.asyncio
async def test_pmmy_benefits():
    """Test PMMY benefits and categories retrieval works."""
    res = await lookup_scheme_db("PMMY", "benefits")
    assert res["success"] is True
    assert res["info_type"] == "benefits"
    assert "Shishu" in res["content"]
    assert "Tarun" in res["content"]

@pytest.mark.asyncio
async def test_pmmy_application():
    """Test PMMY application processes retrieval works."""
    res = await lookup_scheme_db("PMMY", "application")
    assert res["success"] is True
    assert res["info_type"] == "application"
    assert "commercial banks" in res["content"]

@pytest.mark.asyncio
async def test_unknown_scheme():
    """Verify that looking up a fictional scheme XYZ returns a NOT_FOUND code."""
    res = await lookup_scheme_db("XYZ Financial Support Scheme", "overview")
    assert res["success"] is False
    assert res["error_type"] == "NOT_FOUND"

@pytest.mark.asyncio
async def test_unknown_information_field():
    """Verify that requesting an unknown field defaults to 'overview' and succeeds."""
    res = await lookup_scheme_db("PMMY", "what papers are needed")
    # "what papers are needed" should resolve to "documents"
    assert res["success"] is True
    assert res["info_type"] == "documents"
    assert "business plan" in res["content"]

@pytest.mark.asyncio
async def test_source_update_date():
    """Verify that source update date matches official publication stamps."""
    res = await lookup_scheme_db("PMMY", "overview")
    assert res["success"] is True
    assert res["source_updated_at"] == "2026-02-05T00:00:00Z"
