#!/usr/bin/env python3
"""Local no-send reconciliation diagnostics for fictional records only."""
import argparse
import copy
import json
import sys

LISTS = ('A', 'B')

def normalized(email):
    return email.strip().lower()

def classify(contact, scope):
    source = [row for row in contact['source'] if row['list'] == scope]
    target = [row for row in contact['target'] if row['list'] == scope]
    events = [row for row in contact['events'] if row['scope'] == scope]
    if any(row['scope'] == 'global' and row['state'] == 'hard_bounce' for row in contact['events']):
        return {'decision': 'no_send', 'reason': 'global_hard_bounce'}
    if contact.get('identity_uncertain'):
        return {'decision': 'no_send', 'reason': 'unverified_address_link'}
    emails = [normalized(row['email']) for row in contact['source']]
    if len(set(emails)) == 1 and len(source) > 1:
        latest = max(row['at'] for row in source)
        states = {row['state'] for row in source if row['at'] == latest}
        if len(states) > 1:
            return {'decision': 'no_send', 'reason': 'duplicate_conflict'}
    # A contact with a conflicting duplicate in any scope is held globally until identity resolution.
    for list_name in LISTS:
        matching = [row for row in contact['source'] if row['list'] == list_name]
        if len(set(emails)) == 1 and len(matching) > 1:
            latest = max(row['at'] for row in matching)
            if len({row['state'] for row in matching if row['at'] == latest}) > 1:
                return {'decision': 'no_send', 'reason': 'duplicate_conflict'}
    newest_source = max(source, key=lambda row: row['at']) if source else None
    source_at = newest_source['at'] if newest_source else -1
    if any(row['state'] == 'unsubscribed' and row['at'] > source_at for row in events):
        return {'decision': 'no_send', 'reason': 'cutover_unsubscribe'}
    if any(row['state'] == 'unsubscribed' and row['at'] > source_at for row in target):
        return {'decision': 'no_send', 'reason': 'target_later_unsubscribe'}
    if newest_source is None:
        return {'decision': 'no_send', 'reason': 'absent'}
    if newest_source['state'] == 'unsubscribed':
        return {'decision': 'no_send', 'reason': 'source_unsubscribe'}
    if newest_source['state'] == 'pending':
        return {'decision': 'no_send', 'reason': 'pending_confirmation'}
    if newest_source['state'] == 'confirmed' and not newest_source.get('evidence'):
        return {'decision': 'no_send', 'reason': 'missing_provenance'}
    if newest_source['state'] == 'confirmed':
        return {'decision': 'conditional', 'reason': 'permission_record'}
    raise ValueError('unknown source state: ' + newest_source['state'])

def evaluate(fixture, case):
    proposals = fixture['proposals']
    if case not in proposals:
        raise ValueError('unknown case: ' + case)
    proposal = copy.deepcopy(proposals['baseline'])
    if case != 'baseline':
        for cid, changes in proposals[case]['override'].items():
            proposal[cid].update(changes)
    classifications = []
    failures = []
    for contact in fixture['contacts']:
        cid = contact['id']
        result = {'id': cid}
        for scope in LISTS:
            result[scope] = classify(contact, scope)
        classifications.append(result)
        proposed = proposal[cid]
        if any(row['scope'] == 'global' and row['state'] == 'hard_bounce' for row in contact['events']) and proposed['global'] != 'blocklisted':
            failures.append({'id': cid, 'scope': 'global', 'reason': 'global_hard_bounce', 'proposed': proposed['global']})
        for scope in LISTS:
            if proposed[scope] == 'confirmed' and result[scope]['decision'] == 'no_send':
                failures.append({'id': cid, 'scope': scope, 'reason': result[scope]['reason'], 'proposed': 'confirmed'})
    return {'case': case, 'classifications': classifications, 'failures': failures}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', required=True)
    parser.add_argument('--case', required=True)
    args = parser.parse_args()
    try:
        with open(args.fixture, encoding='utf-8') as stream:
            fixture = json.load(stream)
        result = evaluate(fixture, args.case)
    except (OSError, KeyError, ValueError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(',', ':')))
    return 2 if result['failures'] else 0

if __name__ == '__main__':
    sys.exit(main())
