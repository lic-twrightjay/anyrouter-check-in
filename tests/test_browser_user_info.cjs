const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'utils', 'browser_user_info.js'), 'utf8');

function mockResponse({ status = 200, contentType = 'application/json', body = '{}', url = 'https://agentrouter.org/api/user/self' }) {
  return {
    status, ok: status >= 200 && status < 300, url,
    headers: { get: () => contentType },
    text: async () => body
  };
}

async function callWith(response, requestCallback = () => {}) {
  const context = vm.createContext({
    AbortSignal, JSON,
    fetch: async (url, options) => {
      requestCallback(url, options);
      if (response instanceof Error) throw response;
      return response;
    }
  });
  const evaluate = vm.runInContext('(' + source + ')', context);
  return evaluate(['/api/user/self', 'new-api-user', '356997', 'private-access-token']);
}

test('200 Cloudflare HTML is classified without exposing body or credential', async () => {
  const result = await callWith(mockResponse({
    body: '<!doctype html><html><title>Just a moment...</title><p>Cloudflare</p></html>',
    contentType: 'text/html; charset=utf-8'
  }));
  assert.equal(result.success, false);
  assert.equal(result._fetch_error_type, 'cloudflare_challenge');
  assert.equal(result._http_status, 200);
  assert.doesNotMatch(JSON.stringify(result), /Just a moment|private-access-token|doctype/i);
});

test('403 Cloudflare HTML is reported as challenge, not ordinary JSON failure', async () => {
  const result = await callWith(mockResponse({
    status: 403, contentType: 'text/html',
    body: '<html><body>cf-chl challenge-platform</body></html>'
  }));
  assert.equal(result._fetch_error_type, 'cloudflare_challenge');
  assert.equal(result._http_status, 403);
});

test('HTML redirected to login is distinguished from Cloudflare', async () => {
  const result = await callWith(mockResponse({
    contentType: 'text/html',
    url: 'https://agentrouter.org/login',
    body: '<!doctype html><html><title>Log in</title></html>'
  }));
  assert.equal(result._fetch_error_type, 'login_page');
});

test('unrecognized HTML is classified as unexpected HTML', async () => {
  const result = await callWith(mockResponse({
    contentType: 'text/html',
    body: '<!doctype html><html><title>SPA fallback</title></html>'
  }));
  assert.equal(result._fetch_error_type, 'unexpected_html');
});

test('valid user JSON succeeds regardless of content-type label', async () => {
  const result = await callWith(mockResponse({
    contentType: 'text/plain',
    body: '{"success":true,"data":{"quota":500000,"used_quota":0}}'
  }), (url, options) => {
    assert.equal(url, '/api/user/self');
    assert.equal(options.headers['new-api-user'], '356997');
    assert.equal(options.credentials, 'same-origin');
    assert.equal(options.headers.Authorization, 'private-access-token');
  });
  assert.equal(result.success, true);
  assert.equal(result.data.quota, 500000);
});

test('JSON HTTP 401 returns status and error code without account response body', async () => {
  const result = await callWith(mockResponse({
    status: 401, body: '{"success":false,"message":"private auth failure"}'
  }));
  assert.equal(result._fetch_error_type, 'http_error');
  assert.equal(result._http_status, 401);
  assert.doesNotMatch(JSON.stringify(result), /private auth failure/);
});

test('invalid JSON and network errors are distinguished without echoing them', async () => {
  const invalid = await callWith(mockResponse({ body: '{bad json' }));
  assert.equal(invalid._fetch_error_type, 'invalid_json');
  const network = await callWith(new Error('private credentials in network error'));
  assert.equal(network._fetch_error_type, 'network_error');
  assert.doesNotMatch(JSON.stringify(network), /private credentials/);
});
