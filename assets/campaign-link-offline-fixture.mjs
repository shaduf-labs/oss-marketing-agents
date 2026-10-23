// Local, no-network fixture. Uses only built-in Node APIs and local JSON input.
import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';

const fixturePath = process.argv[2];
if (!fixturePath) {
  console.error('Usage: node campaign-link-offline-fixture.mjs campaign-link-fixture-cases.json');
  process.exit(2);
}

const { contract, cases } = JSON.parse(readFileSync(fixturePath, 'utf8'));
const required = Object.entries(contract.required_query);
const allowedKeys = new Set(required.map(([key]) => key));
// Deliberately narrow: whole value only, one @, dotted domain-like part.
const emailLike = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function check(input) {
  const findings = [];
  let url;
  try {
    url = new URL(input); // no base: a relative URL is not approved
  } catch {
    return ['invalid_absolute_url'];
  }

  if (url.protocol !== 'https:') findings.push('not_https');
  if (url.origin !== contract.origin) findings.push('origin_mismatch');
  if (url.pathname !== contract.path) findings.push('path_mismatch');
  if (url.username !== '' || url.password !== '') findings.push('embedded_credentials');
  // A bare trailing # has an empty url.hash, so check the serialized delimiter.
  if (!contract.allow_fragment && url.href.includes('#')) findings.push('fragment_not_approved');

  for (const [name, expected] of required) {
    const values = url.searchParams.getAll(name);
    if (values.length === 0) {
      findings.push(`missing:${name}`);
    } else {
      if (values.some(value => value === '')) findings.push(`empty:${name}`);
      if (values.length > 1) findings.push(`duplicate:${name}`);
      if (new Set(values).size > 1) findings.push(`conflicting:${name}`);
      if (values.some(value => value !== expected)) findings.push(`wrong_value:${name}`);
    }
  }
  for (const [name, value] of url.searchParams) {
    if (!contract.allow_other_query_keys && !allowedKeys.has(name) && !findings.includes(`unapproved_parameter:${name}`)) {
      findings.push(`unapproved_parameter:${name}`);
    }
    if (emailLike.test(value) && !findings.includes(`email_like_value:${name}`)) {
      findings.push(`email_like_value:${name}`);
    }
  }
  return findings;
}

console.log(`Node ${process.version}; ${cases.length} fictional cases; no network I/O`);
console.log(`Contract: ${JSON.stringify(contract)}`);
let failures = 0;
for (const item of cases) {
  const actual = check(item.url);
  let match = true;
  try { assert.deepEqual(actual, item.expected); }
  catch { match = false; failures++; }
  console.log(`${item.id}: expected=${JSON.stringify(item.expected)} actual=${JSON.stringify(actual)} ${match ? 'MATCH' : 'MISMATCH'}`);
}
console.log(`Result: ${cases.length - failures}/${cases.length} expected outcomes matched`);
if (failures) process.exitCode = 1;
