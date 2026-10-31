#!/usr/bin/env python3
"""Check the published, paired 2225 assets without reimporting or replacing legacy data."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
def read(name):
    return json.loads((root / name).read_text())

provenance = read('docs/endstone-1.26.60-manifest.json')
assert provenance['server_started'] and provenance['export_completed']
assert not provenance['errors']
assert provenance['counts']['block_states'] == 23960
assert provenance['counts']['items'] == 2080
for name, expected in {
    'canonical_block_states-1.26.60.nbt': '88b8c903ac75d46247bed5ff785c0c050068d28440190f7412d697b045d2d51f',
    'item_runtime_ids-1.26.60.json': 'de9e385a0bb6f65ec86a5b1e51e22bfb2ea18a05b3da0e51d4cb5651a8569f4a',
}.items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, name
ids = read('block_network_ids-1.26.60.json')
metas = read('block_state_meta_map-1.26.60.json')
assert len(ids) == len(set(ids)) == len(metas) == 23960
assert all(type(value) is int and -(2**31) <= value < 2**31 for value in ids)
assert all(type(value) is int and value >= 0 for value in metas)
items = read('required_item_list-1.26.60.json')
assert len(items) == 2080
assert all(type(value['runtime_id']) is int and type(value['component_based']) is bool for value in items.values())
assert len({value['runtime_id'] for value in items.values()}) == 2080
assert read('item_tags-1.26.60.json')
audit = read('docs/block-meta-1.26.60-audit.json')
assert audit['new_states'] == 23960
assert not audit['unresolved_names'] and not audit['examples_unresolved']
assert audit['counts']['ambiguous'] == 0
print('PASS: original BDS provenance, paired palette/hashes/metadata (23960), unique item IDs (2080), tags and metadata audit')
