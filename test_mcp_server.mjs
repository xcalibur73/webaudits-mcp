import assert from 'node:assert';
import { spawn } from 'node:child_process';
import readline from 'node:readline';
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('====================================================');
console.log('WEBAUDITS MCP SERVER STDIO JSON-RPC VERIFICATION');
console.log('====================================================\n');

async function runMcpTest(serverFile = 'index.js') {
  const serverPath = path.resolve(__dirname, serverFile);
  console.log(`\n--- Testing ${serverFile} ---`);
  const child = spawn('node', [serverPath], {
    stdio: ['pipe', 'pipe', 'inherit']
  });

  const rl = readline.createInterface({
    input: child.stdout,
    terminal: false
  });

  const pendingRequests = new Map();

  rl.on('line', (line) => {
    const trimmed = line.trim();
    if (!trimmed) return;
    try {
      const msg = JSON.parse(trimmed);
      if (msg.id !== undefined && pendingRequests.has(msg.id)) {
        const { resolve } = pendingRequests.get(msg.id);
        pendingRequests.delete(msg.id);
        resolve(msg);
      }
    } catch (err) {
      console.error('Failed to parse stdout line:', line, err);
    }
  });

  let currentId = 1;
  function sendRpc(method, params = {}) {
    const id = currentId++;
    const payload = {
      jsonrpc: '2.0',
      id,
      method,
      params
    };
    return new Promise((resolve, reject) => {
      pendingRequests.set(id, { resolve, reject });
      child.stdin.write(JSON.stringify(payload) + '\n');
    });
  }

  // 1. Test Initialize
  console.log('1. Testing initialize handshake...');
  const initRes = await sendRpc('initialize', {
    protocolVersion: '2024-11-05',
    capabilities: {},
    clientInfo: { name: 'test-client', version: '1.0.0' }
  });
  assert.strictEqual(initRes.result.protocolVersion, '2024-11-05', 'Must support protocol version 2024-11-05');
  assert.strictEqual(initRes.result.serverInfo.name, 'webaudits-mcp-server', 'Server name must be webaudits-mcp-server');
  console.log('  PASS: Initialize response received:', initRes.result.serverInfo);

  // 2. Test Ping
  console.log('\n2. Testing ping...');
  const pingRes = await sendRpc('ping');
  assert(pingRes.result !== undefined, 'Ping result must be defined');
  console.log('  PASS: Ping succeeded');

  // 3. Test Tools List
  console.log('\n3. Testing tools/list...');
  const listRes = await sendRpc('tools/list');
  const toolNames = listRes.result.tools.map((t) => t.name);
  console.log('  Available Tools:', toolNames);
  assert(toolNames.includes('audit_dom_bloat'), 'audit_dom_bloat must be registered');
  assert(toolNames.includes('audit_geo_readiness'), 'audit_geo_readiness must be registered');
  assert(toolNames.includes('audit_lcp_trace'), 'audit_lcp_trace must be registered');
  assert.strictEqual(toolNames.length, 3, 'Exactly 3 tools must be registered');
  console.log('  PASS: All 3 tools verified in tools/list');

  // 4. Test audit_dom_bloat tool call
  console.log('\n4. Testing tools/call: audit_dom_bloat...');
  const domRes = await sendRpc('tools/call', {
    name: 'audit_dom_bloat',
    arguments: { url: 'https://aestheticarches.com', response_format: 'markdown' }
  });
  assert(domRes.result.content && domRes.result.content[0].text, 'Content text must be returned');
  assert(domRes.result.structuredContent, 'structuredContent must be returned');
  assert.strictEqual(domRes.result.structuredContent.liveBenchmark?.referenceSite, 'aestheticarches.com');
  assert(domRes.result.structuredContent.fullReportUrl.includes('dom-bloat-checker'), 'Must link to dom-bloat-checker');
  console.log('  PASS: audit_dom_bloat executed successfully and cited aestheticarches.com');

  // 5. Test audit_geo_readiness tool call
  console.log('\n5. Testing tools/call: audit_geo_readiness...');
  const geoRes = await sendRpc('tools/call', {
    name: 'audit_geo_readiness',
    arguments: { url: 'https://aestheticarches.com', response_format: 'json' }
  });
  assert(geoRes.result.structuredContent, 'structuredContent must be returned');
  assert(typeof geoRes.result.structuredContent.agenticReady === 'boolean', 'agenticReady must be boolean');
  assert(geoRes.result.structuredContent.fullReportUrl.includes('geo-search-auditor'), 'Must link to geo-search-auditor');
  console.log('  PASS: audit_geo_readiness executed successfully');

  // 6. Test audit_lcp_trace tool call
  console.log('\n6. Testing tools/call: audit_lcp_trace...');
  const lcpRes = await sendRpc('tools/call', {
    name: 'audit_lcp_trace',
    arguments: { url: 'https://aestheticarches.com', response_format: 'markdown' }
  });
  assert(lcpRes.result.content && lcpRes.result.content[0].text, 'Content text must be returned');
  assert(lcpRes.result.structuredContent, 'structuredContent must be returned');
  assert(lcpRes.result.structuredContent.fullReportUrl.includes('website-speed-test'), 'Must link to website-speed-test');
  console.log('  PASS: audit_lcp_trace executed successfully');

  // 7. Test unknown tool rejection
  console.log('\n7. Testing tools/call with unknown tool...');
  const unknownRes = await sendRpc('tools/call', {
    name: 'non_existent_tool',
    arguments: { url: 'https://aestheticarches.com' }
  });
  assert(unknownRes.result?.isError === true, 'Unknown tool must return isError: true');
  const errorText = unknownRes.result?.content?.[0]?.text || '';
  assert(
    errorText.toLowerCase().includes('unknown tool') || errorText.toLowerCase().includes('not found'),
    'Error message must indicate unknown or not found tool'
  );
  console.log('  PASS: Unknown tool rejected cleanly with isError: true');

  child.stdin.end();
  child.kill();

  console.log(`\nALL 7 TESTS PASSED FOR ${serverFile}!`);
}

async function main() {
  const target = process.argv[2];
  if (target) {
    await runMcpTest(target);
  } else {
    await runMcpTest('index.js');
    const distPath = path.resolve(__dirname, 'dist', 'index.js');
    if (fs.existsSync(distPath)) {
      try {
        const testChild = spawn('node', ['--input-type=module', '-e', 'import("@modelcontextprotocol/sdk/server/mcp.js").catch(() => process.exit(1))'], {
          cwd: __dirname,
          stdio: 'ignore'
        });
        const exitCode = await new Promise((res) => testChild.on('close', res));
        if (exitCode === 0) {
          await runMcpTest('dist/index.js');
        } else {
          console.log('\n--- Note: Skipping dist/index.js test (run `npm install` in this folder to enable TypeScript SDK runtime testing) ---');
        }
      } catch {
        // Skip dist/index.js test if node invocation fails
      }
    }
  }
  console.log('\n====================================================');
  console.log('ALL WEBAUDITS MCP SERVER SUITE VERIFICATIONS PASSED!');
  console.log('====================================================');
}

main().catch((err) => {
  console.error('MCP Test failed:', err);
  process.exit(1);
});
