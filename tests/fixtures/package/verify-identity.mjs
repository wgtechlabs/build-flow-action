import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

export function verifyIdentityPermission(method, env = process.env) {
  let forkPullRequest = false;
  if (env.GITHUB_EVENT_NAME === 'pull_request') {
    const event = JSON.parse(readFileSync(env.GITHUB_EVENT_PATH, 'utf8'));
    const head = event.pull_request?.head?.repo?.id;
    const base = event.pull_request?.base?.repo?.id;
    assert.ok(Number.isSafeInteger(head) && head > 0 && Number.isSafeInteger(base) && base > 0,
      'Pull request repository identities must be available');
    forkPullRequest = head !== base;
  }

  // Check availability only. Never request an identity token or print its URL/value.
  const urlAvailable = Boolean(env.ACTIONS_ID_TOKEN_REQUEST_URL);
  const tokenAvailable = Boolean(env.ACTIONS_ID_TOKEN_REQUEST_TOKEN);
  assert.equal(urlAvailable, tokenAvailable, 'Identity-token variables must be available together');
  // Fork PRs normally lose write permissions. Private repositories can opt in to
  // sending write tokens, so either paired state is valid for their dry run.
  if (method !== 'oidc' || !forkPullRequest) {
    assert.equal(urlAvailable, method === 'oidc', 'Identity-token permission availability');
  }
}
