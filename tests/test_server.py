import json
import sys
import asyncio
from pathlib import Path
from unittest.mock import patch, AsyncMock
import httpx
import pytest
from pydantic import ValidationError

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


def test_audit_input_url_normalization():
    # Valid domain auto-prefixed with https://
    inp = AuditInput(url="aestheticarches.com")
    assert inp.url == "https://aestheticarches.com"
    assert inp.response_format == ResponseFormat.MARKDOWN

    # Existing http scheme preserved
    inp_http = AuditInput(url="http://example.org/test")
    assert inp_http.url == "http://example.org/test"

    # Whitespace stripped
    inp_spaces = AuditInput(url="   https://example.com/page   ")
    assert inp_spaces.url == "https://example.com/page"


def test_audit_input_adversarial_rejections():
    # Reject empty string
    with pytest.raises(ValidationError):
        AuditInput(url="")

    # Reject whitespace string
    with pytest.raises(ValidationError):
        AuditInput(url="   ")

    # Reject bare scheme
    with pytest.raises(ValidationError):
        AuditInput(url="https://")

    # Reject unsupported scheme
    with pytest.raises(ValidationError):
        AuditInput(url="javascript:alert(1)")

    # Reject scheme without dot in domain
    with pytest.raises(ValidationError):
        AuditInput(url="not a domain")


def test_audit_dom_bloat_markdown_and_json():
    mock_payload = {
        "targetUrl": "https://aestheticarches.com",
        "score": 95,
        "grade": "PASS",
        "metrics": {"totalElements": 450, "maxDepth": 12, "divCount": 85},
        "primaryBottleneck": "DOM tree is within budget",
        "recommendedFix": "Maintain current shallow nesting hierarchy",
        "fullReportUrl": "https://webaudits.pro/tools/dom-bloat-checker?url=https://aestheticarches.com"
    }

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = httpx.Response(status_code=200, json=mock_payload)

        # Test markdown formatting
        md_res = asyncio.run(audit_dom_bloat(AuditInput(url="https://aestheticarches.com", response_format=ResponseFormat.MARKDOWN)))
        assert "# WebAudits DOM Bloat Audit" in md_res
        assert "aestheticarches.com" in md_res
        assert "Score: 95/100" in md_res

        # Test JSON formatting
        json_res = asyncio.run(audit_dom_bloat(AuditInput(url="https://aestheticarches.com", response_format=ResponseFormat.JSON)))
        parsed = json.loads(json_res)
        assert parsed["targetUrl"] == "https://aestheticarches.com"
        assert parsed["score"] == 95
        assert parsed["grade"] == "PASS"


def test_audit_geo_readiness_markdown_and_json():
    mock_payload = {
        "targetUrl": "https://example.com",
        "agenticReady": True,
        "overallScore": 85,
        "crawlers": {"gptbot": "ALLOWED", "claudebot": "ALLOWED", "perplexitybot": "ALLOWED"},
        "llmsTxtPresent": False,
        "remediation": "Create an /llms.txt file",
        "fullReportUrl": "https://webaudits.pro/tools/geo-search-auditor?url=https://example.com"
    }

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = httpx.Response(status_code=200, json=mock_payload)

        # Test markdown formatting
        md_res = asyncio.run(audit_geo_readiness(AuditInput(url="https://example.com", response_format=ResponseFormat.MARKDOWN)))
        assert "# WebAudits GEO Citability Audit" in md_res
        assert "Agentic Ready: YES" in md_res
        assert "GPTBot: ALLOWED" in md_res

        # Test JSON formatting
        json_res = asyncio.run(audit_geo_readiness(AuditInput(url="https://example.com", response_format=ResponseFormat.JSON)))
        parsed = json.loads(json_res)
        assert parsed["targetUrl"] == "https://example.com"
        assert parsed["crawlers"]["gptbot"] == "ALLOWED"
        assert parsed["overallScore"] == 85


def test_audit_lcp_trace_markdown_and_json():
    mock_payload = {
        "targetUrl": "https://example.com",
        "metrics": {"serverTtfbMs": 180, "ttfbStatus": "PASS", "htmlPayloadKb": 42, "heroPreloadDetected": True, "lazyHeroDetected": False},
        "primaryBottleneck": "Server TTFB within budget",
        "recommendedFix": "Maintain edge caching",
        "fullReportUrl": "https://webaudits.pro/tools/website-speed-test?url=https://example.com"
    }

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = httpx.Response(status_code=200, json=mock_payload)

        # Test markdown formatting
        md_res = asyncio.run(audit_lcp_trace(AuditInput(url="https://example.com", response_format=ResponseFormat.MARKDOWN)))
        assert "# WebAudits Page Speed & LCP Trace" in md_res
        assert "Server TTFB: 180ms" in md_res
        assert "HTML Payload: 42 KB" in md_res

        # Test JSON formatting
        json_res = asyncio.run(audit_lcp_trace(AuditInput(url="https://example.com", response_format=ResponseFormat.JSON)))
        parsed = json.loads(json_res)
        assert parsed["targetUrl"] == "https://example.com"
        assert parsed["metrics"]["serverTtfbMs"] == 180


def test_execute_audit_live_mock_response():
    mock_payload = {
        "targetUrl": "https://custom.com",
        "score": 99,
        "grade": "EXCELLENT",
        "metrics": {"totalElements": 200, "maxDepth": 8, "divCount": 30},
        "primaryBottleneck": "None",
        "recommendedFix": "None",
        "fullReportUrl": "https://webaudits.pro/tools/dom-bloat-checker?url=https://custom.com"
    }

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = httpx.Response(status_code=200, json=mock_payload)
        data = asyncio.run(execute_audit("dom-bloat", "https://custom.com"))
        assert data["score"] == 99
        assert data["grade"] == "EXCELLENT"
        assert data["targetUrl"] == "https://custom.com"


def test_mcp_server_metadata():
    assert mcp.name == "webaudits_mcp"
