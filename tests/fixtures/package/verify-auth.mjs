import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { verifyIdentityPermission } from './verify-identity.mjs';

const method = process.argv[2];
assert.ok(['token', 'oidc'].includes(method), 'Expected an authentication test mode');
assert.equal(process.env.NPM_AUTH_METHOD, method, 'Authentication mode must reach the primitive');
assert.equal(process.env.PUBLISH_ENABLED, 'false', 'Fixture publication must stay disabled');
assert.equal(process.env.DRY_RUN, 'true', 'Fixture dry-run protection must stay enabled');

verifyIdentityPermission(method);

if (method === 'oidc') {
  assert.equal(Boolean(process.env.NPM_TOKEN), false, 'OIDC must not receive an npm token');
  assert.equal(process.version, 'v24.21.0', 'OIDC publishing Node runtime');
  const npm = spawnSync('npm', ['--version'], { encoding: 'utf8' });
  assert.equal(npm.status, 0, 'npm must be available for trusted publishing');
  assert.equal(npm.stdout.trim(), '11.21.0', 'OIDC publishing npm version');
} else {
  assert.equal(process.env.NPM_TOKEN === 'workflow-test-not-a-valid-token', true,
    'Token fixture must receive only its fake credential');
}

console.log(`Package ${method} permissions and build configuration passed; publication is disabled.`);
