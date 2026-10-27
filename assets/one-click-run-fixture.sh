#!/bin/sh
# Run from this directory. All commands are local; no transport or HTTP.
set +e
python3 --version
printf 'runtime_exit=%s\n' "$?"
python3 make-fixtures.py
printf 'fixture_exit=%s\n' "$?"
python3 -m unittest discover -s . -p 'test_checker.py' -v
printf 'unittest_exit=%s\n' "$?"
for c in valid-a valid-b cross-a-to-b global-a missing-uri-a missing-post-b duplicate-uri-a duplicate-post-b malformed-uri-a malformed-post-b multiple-https-a; do
  out=$(python3 checker.py --case "$c")
  rc=$?
  printf 'case=%s exit=%s stdout=%s\n' "$c" "$rc" "$out"
done
python3 checker.py --case not-declared
printf 'unknown_case_exit=%s\n' "$?"
