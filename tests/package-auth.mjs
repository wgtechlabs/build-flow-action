import assert from 'node:assert/strict';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { verifyIdentityPermission } from './fixtures/package/verify-identity.mjs';

const identity = {
  ACTIONS_ID_TOKEN_REQUEST_URL: 'https://example.invalid/identity',
  ACTIONS_ID_TOKEN_REQUEST_TOKEN: 'not-a-real-token',
};

function pullRequest(t, head, base, raw) {
  const directory = mkdtempSync(join(tmpdir(), 'package-auth-'));
  t.after(() => rmSync(directory, { recursive: true, force: true }));
  const path = join(directory, 'event.json');
  writeFileSync(path, raw ?? JSON.stringify({
    pull_request: { head: { repo: head }, base: { repo: base } },
  }));
  return { GITHUB_EVENT_NAME: 'pull_request', GITHUB_EVENT_PATH: path };
}

test('fork OIDC dry runs accept withheld permissions and explicit write-token opt-in', (t) => {
  const env = pullRequest(t, { id: 2, fork: true }, { id: 1 });
  verifyIdentityPermission('oidc', env);
  verifyIdentityPermission('oidc', { ...env, ...identity });
});

test('same-repository PRs still require OIDC, including repositories that are forks', (t) => {
  const env = pullRequest(t, { id: 2, fork: true }, { id: 2, fork: true });
  assert.throws(() => verifyIdentityPermission('oidc', env), /permission availability/);
  verifyIdentityPermission('oidc', { ...env, ...identity });
});

test('manual OIDC runs require permission without needing a PR payload', () => {
  const env = { GITHUB_EVENT_NAME: 'workflow_dispatch' };
  assert.throws(() => verifyIdentityPermission('oidc', env), /permission availability/);
  verifyIdentityPermission('oidc', { ...env, ...identity });
});

test('token fixtures must never receive identity permission, including fork PRs', (t) => {
  const contexts = [
    { GITHUB_EVENT_NAME: 'workflow_dispatch' },
    pullRequest(t, { id: 1 }, { id: 1 }),
    pullRequest(t, { id: 2 }, { id: 1 }),
  ];
  for (const env of contexts) {
    verifyIdentityPermission('token', env);
    assert.throws(() => verifyIdentityPermission('token', { ...env, ...identity }), /permission availability/);
  }
});

test('a partial identity-token environment fails even for fork PRs', (t) => {
  const env = pullRequest(t, { id: 2 }, { id: 1 });
  for (const [key, value] of Object.entries(identity)) {
    assert.throws(() => verifyIdentityPermission('oidc', { ...env, [key]: value }), /available together/);
  }
});

test('missing or invalid PR metadata cannot silently relax permission checks', (t) => {
  for (const raw of ['broken JSON', '{}', '{"pull_request":{"head":{"repo":{"id":2}}}}']) {
    const env = pullRequest(t, undefined, undefined, raw);
    assert.throws(() => verifyIdentityPermission('oidc', env));
  }
  for (const id of [undefined, null, '2', 0]) {
    const env = pullRequest(t, { id }, { id: 1 });
    assert.throws(() => verifyIdentityPermission('oidc', env), /repository identities/);
  }
  assert.throws(() => verifyIdentityPermission('oidc', { GITHUB_EVENT_NAME: 'pull_request' }));
  assert.throws(() => verifyIdentityPermission('oidc', {
    GITHUB_EVENT_NAME: 'pull_request', GITHUB_EVENT_PATH: '/nonexistent/package-auth-event.json',
  }));
});
