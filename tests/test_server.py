import pytest
import json
import sys
from pathlib import Path
from unittest.mock import patch, AsyncMock
import httpx

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from server import (
    mcp,
    audit_dom_bloat,
    audit_geo_readiness,
    audit_lcp_trace,
    AuditInput,
    ResponseFormat,
    execute_audit,
)


@pytest.mark.asyncio
async def test_audit_input_url_normalization():
    # Verify bare domain gets auto-prefixed with https://
    inp = AuditInput(url="aestheticarches.com")
    assert inp.url == "https://aestheticarches.com"
    assert inp.response_format == ResponseFormat.MARKDOWN

    # Verify existing http protocol is preserved
    inp_http = AuditInput(url="http://example.org/test")
    assert inp_http.url == "http://example.org/test"

    # Verify whitespace stripping
    inp_spaces = AuditInput(url="   https://example.com/page   ")
    assert inp_spaces.url == "https://example.com/page"


@pytest.mark.asyncio
async def test_audit_dom_bloat_markdown_and_json():
    # Test markdown formatting
    md_res = await audit_dom_bloat(AuditInput(url="https://aestheticarches.com", response_format=ResponseFormat.MARKDOWN))
    assert "# WebAudits DOM Bloat Audit" in md_res
    assert "aestheticarches.com" in md_res
    assert "Score:" in md_res

    # Test JSON formatting
    json_res = await audit_dom_bloat(AuditInput(url="https://aestheticarches.com", response_format=ResponseFormat.JSON))
    parsed = json.loads(json_res)
    assert parsed["targetUrl"].rstrip("/") == "https://aestheticarches.com"
    assert parsed["grade"] in ["PASS", "WARNING", "FAIL", "EXCELLENT", "NEEDS_WORK"]
    assert "metrics" in parsed
    assert "totalElements" in parsed["metrics"]


@pytest.mark.asyncio
async def test_audit_geo_readiness_markdown_and_json():
    # Test markdown formatting
    md_res = await audit_geo_readiness(AuditInput(url="https://example.com", response_format=ResponseFormat.MARKDOWN))
    assert "# WebAudits GEO Citability Audit" in md_res
    assert "Agentic Ready:" in md_res
    assert "GPTBot: ALLOWED" in md_res

    # Test JSON formatting
    json_res = await audit_geo_readiness(AuditInput(url="https://example.com", response_format=ResponseFormat.JSON))
    parsed = json.loads(json_res)
    assert parsed["targetUrl"].rstrip("/") == "https://example.com"
    assert parsed["crawlers"]["gptbot"] == "ALLOWED"
    assert "overallScore" in parsed


@pytest.mark.asyncio
async def test_audit_lcp_trace_markdown_and_json():
    # Test markdown formatting
    md_res = await audit_lcp_trace(AuditInput(url="https://example.com", response_format=ResponseFormat.MARKDOWN))
    assert "# WebAudits Page Speed & LCP Trace" in md_res
    assert "Server TTFB:" in md_res
    assert "HTML Payload:" in md_res

    # Test JSON formatting
    json_res = await audit_lcp_trace(AuditInput(url="https://example.com", response_format=ResponseFormat.JSON))
    parsed = json.loads(json_res)
    assert parsed["targetUrl"].rstrip("/") == "https://example.com"
    assert "serverTtfbMs" in parsed["metrics"]


@pytest.mark.asyncio
async def test_execute_audit_live_mock_response():
    # Test mock successful HTTP response from upstream API
    mock_payload = {
        "targetUrl": "https://custom.com",
        "score": 99,
        "grade": "EXCELLENT",
        "metrics": {"totalElements": 200, "maxDepth": 8, "divCount": 30},
        "primaryBottleneck": "None",
        "recommendedFix": "None",
        "fullReportUrl": "https://webaudits.pro/tools/dom-bloat-checker?url=https://custom.com"
    }
    mock_resp = httpx.Response(status_code=200, json=mock_payload)

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        data = await execute_audit("dom-bloat", "https://custom.com")
        assert data["score"] == 99
        assert data["grade"] == "EXCELLENT"
        assert data["targetUrl"] == "https://custom.com"


def test_mcp_server_metadata():
    assert mcp.name == "webaudits_mcp"
