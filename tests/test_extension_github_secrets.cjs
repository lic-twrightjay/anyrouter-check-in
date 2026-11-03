// Node built-in test runner. No real GitHub token or outbound requests required.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const script = fs.readFileSync(
  path.join(__dirname, '..', 'AnyRouter Cookie Updater', 'background.js'),
  'utf8'
);
const envConfig = {
  githubToken: 'private-token-for-tests',
  repoOwner: 'lic-twrightjay',
  repoName: 'anyrouter-check-in',
  environmentName: 'production'
};

function fakeResponse(status, data = {}) {
  return { ok: status >= 200 && status < 300, status, json: async () => data };
}

function setup(responses) {
  const requests = [];
  const queue = [...responses];
  const ctx = vm.createContext({
    importScripts: () => {},
    URL,
    encodeURIComponent,
    console: { log: () => {} },
    chrome: {
      runtime: {
        onInstalled: { addListener: () => {} },
        onMessage: { addListener: () => {} }
      },
      alarms: { onAlarm: { addListener: () => {} } },
      storage: {
        sync: { get: async () => ({ ...envConfig, accounts: JSON.stringify([{ domain: 'https://agentrouter.org' }]) }) },
        local: { get: async () => ({ customProviders: {} }), set: async () => {} }
      }
    },
    fetch: async (url, options) => {
      requests.push({ url, options });
      const reply = queue.shift();
      if (reply instanceof Error) throw reply;
      if (!reply) throw Error('Unexpected fetch call');
      return reply;
    },
    sodium: {
      ready: Promise.resolve(),
      base64_variants: { ORIGINAL: 1 },
      from_base64: () => 'decoded-public-key',
      from_string: () => 'encoded-secret',
      crypto_box_seal: () => 'sealed-secret',
      to_base64: () => 'encrypted-base64'
    }
  });
  vm.runInContext(script, ctx, { filename: 'background.js' });
  return { requests, ctx, call: name => vm.runInContext(name, ctx) };
}

test('Environment Secret uses the documented owner/repo GET and PUT routes', async () => {
  const { requests, call } = setup([
    fakeResponse(200, { key: 'test-key', key_id: 'test-key-id' }),
    fakeResponse(201)
  ]);
  await call('pushToGitHubSecret')(envConfig, 'ANYROUTER_ACCOUNT_356997_AGENTROUTER', '{"cookies":{"session":"not-for-logs"}}');
  assert.deepEqual(requests.map(x => x.url), [
    'https://api.github.com/repos/lic-twrightjay/anyrouter-check-in/environments/production/secrets/public-key',
    'https://api.github.com/repos/lic-twrightjay/anyrouter-check-in/environments/production/secrets/ANYROUTER_ACCOUNT_356997_AGENTROUTER'
  ]);
  assert.equal(requests[0].options.method, 'GET');
  assert.equal(requests[1].options.method, 'PUT');
  assert.deepEqual(JSON.parse(requests[1].options.body), {
    encrypted_value: 'encrypted-base64',
    key_id: 'test-key-id'
  });
});

test('Repository Secrets are a supported explicit fallback when Environment is blank', async () => {
  const { requests, call } = setup([
    fakeResponse(200, { key: 'test-key', key_id: 'test-key-id' }),
    fakeResponse(204)
  ]);
  await call('pushToGitHubSecret')({ ...envConfig, environmentName: '' }, 'ANYROUTER_ACCOUNT_356997_AGENTROUTER', '{"test":"1"}');
  assert.equal(requests[0].url, 'https://api.github.com/repos/lic-twrightjay/anyrouter-check-in/actions/secrets/public-key');
  assert.equal(requests[1].url, 'https://api.github.com/repos/lic-twrightjay/anyrouter-check-in/actions/secrets/ANYROUTER_ACCOUNT_356997_AGENTROUTER');
});

test('403 on Environment public key advises fine-grained Environments and classic repo', async () => {
  const { call } = setup([fakeResponse(403)]);
  await assert.rejects(
    call('getPublicKey')(envConfig),
    e => e.message.includes('HTTP 403') &&
      e.message.includes('Environments') &&
      e.message.includes('Read and write') &&
      e.message.includes('Classic PAT') &&
      !e.message.includes(envConfig.githubToken)
  );
});

test('403 on Repository Secrets directs users to Secrets permission', async () => {
  const { call } = setup([fakeResponse(403)]);
  await assert.rejects(
    call('getPublicKey')({ ...envConfig, environmentName: '' }),
    e => e.message.includes('Secrets → Read and write') && !e.message.includes('Environments → Read and write')
  );
});

test('403 during Environment PUT reports write permission rather than GET success', async () => {
  const { requests, call } = setup([
    fakeResponse(200, { key: 'test-key', key_id: 'test-key-id' }),
    fakeResponse(403)
  ]);
  await assert.rejects(
    call('pushToGitHubSecret')(envConfig, 'ANYROUTER_ACCOUNT_356997_AGENTROUTER', '{}'),
    e => e.message.includes('写入账号 Secret') &&
      e.message.includes('HTTP 403') &&
      e.message.includes('Environments') &&
      e.message.includes('Read and write')
  );
  assert.equal(requests.length, 2);
  assert.equal(requests[1].options.method, 'PUT');
});

for (const [status, expected] of [
  [401, 'PAT 无效'],
  [404, '核对 Owner'],
  [422, 'env_key_suffix'],
  [429, '限流']
]) {
  test(`HTTP ${status} has a precise, safe error`, async () => {
    const { call } = setup([fakeResponse(status)]);
    await assert.rejects(call('getPublicKey')(envConfig), e =>
      e.message.includes(`HTTP ${status}`) && e.message.includes(expected) &&
      !e.message.includes(envConfig.githubToken)
    );
  });
}

test('network exception does not expose credentials or raw fetch error message', async () => {
  const { call } = setup([new Error('secret private-token-for-tests')]);
  await assert.rejects(call('getPublicKey')(envConfig), e =>
    e.message.includes('无法连接 api.github.com') &&
    !e.message.includes(envConfig.githubToken)
  );
});

test('invalid secret names fail before an API request', async () => {
  const { call, requests } = setup([]);
  await assert.rejects(call('pushToGitHubSecret')(envConfig, 'ANYROUTER-INVALID', '{}'), /env_key_suffix/);
  assert.equal(requests.length, 0);
});

test('sync result contains actionable first account failure', async () => {
  const { ctx, call } = setup([]);
  vm.runInContext(
    "syncProvidersSecret = async () => {}; syncOneAccount = async () => ({success:false,label:'agentrouter.org',error:'GitHub HTTP 403：Environments 权限不足'});",
    ctx
  );
  const result = await call('syncAllAccounts')();
  assert.equal(result.success, false);
  assert.match(result.summary, /0\/1/);
  assert.match(result.error, /Environments 权限不足/);
});
