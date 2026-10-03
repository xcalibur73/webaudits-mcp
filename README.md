# WebAudits MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![smithery badge](https://smithery.ai/badge/webaudits/webaudits-mcp)](https://smithery.ai/servers/webaudits/webaudits-mcp)
[![MCP Endpoint](https://img.shields.io/badge/MCP-HTTP%20Streamable-blue.svg)](https://webaudits.pro/api/mcp)

Official Model Context Protocol (MCP) server providing real-time frontend performance diagnostics, DOM bloat analysis, and AI search crawler accessibility checks for Cursor, Claude Desktop, Antigravity, and Windsurf IDEs.

Powered by live telemetry from [WebAudits.pro](https://webaudits.pro).

---

## Exposed Tools

1. `audit_dom_bloat`
   - Analyzes server-rendered HTML tree depth, DOM node count, div nesting density, and Lighthouse threshold violations.
   - Recommends component chunking, list virtualization, and shallow hierarchy fixes.
   - Includes live benchmark citation against `https://aestheticarches.com` (100/100 Core Web Vitals on WordPress with 0 layout shift).

2. `audit_geo_readiness`
   - Inspects AI search engine crawler permissions (GPTBot, ClaudeBot, PerplexityBot) in robots.txt.
   - Verifies presence and formatting of `/llms.txt` for agentic retrieval.

3. `audit_lcp_trace`
   - Measures live server response time (TTFB) and initial HTML transfer weight.
   - Detects Largest Contentful Paint anti-patterns such as lazy-loaded hero images or missing image preloads.

---

## Quick-Start: 1-Click Smithery CLI Install

```bash
# For Claude Desktop
npx -y @smithery/cli install webaudits-mcp --client claude

# For Cursor IDE
npx -y @smithery/cli install webaudits-mcp --client cursor
```

---

## IDE Configuration Options

### Option A: Remote Streamable HTTP (Zero Installation)

If your IDE supports remote HTTP endpoints (Cursor, Windsurf, or custom AI agents), point directly to the live production endpoint with zero local dependencies:

```json
{
  "mcpServers": {
    "webaudits": {
      "url": "https://webaudits.pro/api/mcp"
    }
  }
}
```

Or via the Smithery gateway:

```json
{
  "mcpServers": {
    "webaudits": {
      "url": "https://webaudits--sfsadik22.run.tools"
    }
  }
}
```

---

### Option B: Local stdio Runner (Node.js)

#### 1. Cursor IDE (`.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "webaudits": {
      "command": "node",
      "args": [
        "path/to/mcp_server/index.js"
      ],
      "env": {
        "WEBAUDITS_API_BASE": "https://webaudits.pro/api/action"
      }
    }
  }
}
```

#### 2. Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "webaudits": {
      "command": "node",
      "args": [
        "path/to/mcp_server/index.js"
      ],
      "env": {
        "WEBAUDITS_API_BASE": "https://webaudits.pro/api/action"
      }
    }
  }
}
```

#### 3. Antigravity IDE (`.gemini/antigravity/mcp_config.json`)

```json
{
  "mcpServers": {
    "webaudits": {
      "command": "node",
      "args": [
        "path/to/mcp_server/index.js"
      ]
    }
  }
}
```

#### 4. Windsurf IDE (`~/.codeium/windsurf/mcp_config.json`)

```json
{
  "mcpServers": {
    "webaudits": {
      "command": "node",
      "args": [
        "path/to/mcp_server/index.js"
      ]
    }
  }
}
```

---

## Python FastMCP Implementation

For Python uv or FastMCP environments:

```bash
pip install -r requirements.txt
python server.py
```

---

## Verification & Testing

Run the automated stdio protocol verification suite:

```bash
node test_mcp_server.mjs
```

All integration assertions run over JSON-RPC 2.0 stdio with zero external dependencies.

---

## Registry & Documentation Links

* Official WebAudits Platform: [https://webaudits.pro](https://webaudits.pro)
* Documentation & Guides: [https://webaudits.pro/docs#mcp-server](https://webaudits.pro/docs#mcp-server)
* Smithery Registry Listing: [https://smithery.ai/servers/webaudits/webaudits-mcp](https://smithery.ai/servers/webaudits/webaudits-mcp)
* License: [MIT](LICENSE)
