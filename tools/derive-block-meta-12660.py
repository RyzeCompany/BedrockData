#!/usr/bin/env python3
"""Check and derive 1.26.60 block metadata without assuming palette index stability.

Network NBT contains repeated unnamed compounds. Each state has name/states/
version; old metadata is mapped by state identity, not by list offset.
Newly introduced names may use meta=0 but are reported separately.
Unknown variants of existing block names are NOT silently mapped to zero.
"""
from __future__ import annotations
from collections import defaultdict
import argparse
import json
import struct
from io import BytesIO
from pathlib import Path

NETWORK_ONLY = frozenset([
    "minecraft:corner", "minecraft:connection_north", "minecraft:connection_south",
    "minecraft:connection_east", "minecraft:connection_west"
])

def exact(stream, size):
    raw = stream.read(size)
    if len(raw) != size:
        raise ValueError("Truncated network NBT")
    return raw

def unsigned(stream, maxbytes=10):
    value = 0
    for i in range(maxbytes):
        byte = exact(stream, 1)[0]
        if i == maxbytes - 1 and byte > (1 if maxbytes == 10 else 15):
            raise ValueError("Oversized varint")
        value |= (byte & 0x7f) << (7 * i)
        if byte < 0x80:
            return value
    raise ValueError("Unterminated varint")

def signed(stream, bits):
    value = unsigned(stream, 5 if bits == 32 else 10)
    return (value >> 1) ^ -(value & 1)

def string(stream):
    length = unsigned(stream, 5)
    if length > 2_000_000:
        raise ValueError("Excessive NBT string")
    return exact(stream, length).decode("utf-8")

def payload(stream, tag):
    if tag == 1:
        return struct.unpack("<b", exact(stream, 1))[0]
    if tag == 2:
        return struct.unpack("<h", exact(stream, 2))[0]
    if tag == 3:
        return signed(stream, 32)
    if tag == 4:
        return signed(stream, 64)
    if tag == 5:
        return struct.unpack("<f", exact(stream, 4))[0]
    if tag == 6:
        return struct.unpack("<d", exact(stream, 8))[0]
    if tag == 8:
        return string(stream)
    if tag == 10:
        result = {}
        while (kind := exact(stream, 1)[0]) != 0:
            name = string(stream)
            if name in result:
                raise ValueError("Duplicate NBT property")
            result[name] = (kind, payload(stream, kind))
        return result
    if tag == 9:
        subtype = exact(stream, 1)[0]
        count = signed(stream, 32)
        if count < 0 or count > 100_000:
            raise ValueError("Invalid list count")
        return [payload(stream, subtype) for _ in range(count)]
    if tag in (7, 11, 12):
        count = signed(stream, 32)
        width = {7:1, 11:4, 12:8}[tag]
        if count < 0 or count * width > 16_777_216:
            raise ValueError("Invalid NBT array length")
        return exact(stream, count * width).hex()
    raise ValueError(f"Unexpected NBT tag {tag}")

def load_palette(path):
    stream = BytesIO(path.read_bytes())
    entries = []
    while stream.tell() < len(stream.getbuffer()):
        if exact(stream, 1) != b"\x0a":
            raise ValueError("Network NBT must be a compound")
        if string(stream) != "":
            raise ValueError("Expected unnamed root")
        entry = payload(stream, 10)
        if "name" not in entry or "states" not in entry:
            raise ValueError("Missing state descriptor")
        if entry["name"][0] != 8 or entry["states"][0] != 10:
            raise ValueError("Invalid state name or properties")
        entries.append(entry)
    return entries

def key(entry, strip=False):
    name = entry["name"][1]
    states = entry["states"][1]
    props = {k: v for k, v in states.items() if not strip or k not in NETWORK_ONLY}
    return name, json.dumps(props, sort_keys=True, separators=(",", ":"))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("."))
    args = parser.parse_args()
    old = load_palette(Path("canonical_block_states-1.26.50.nbt"))
    new = load_palette(Path("canonical_block_states-1.26.60.nbt"))
    old_metas = json.loads(Path("block_state_meta_map-1.26.50.json").read_text())
    if len(old) != len(old_metas) or len(new) != 23960:
        raise ValueError("Palette/metadata length mismatch")
    direct = defaultdict(set)
    normalized = defaultdict(set)
    old_names = set()
    for state, meta in zip(old, old_metas):
        direct[key(state)].add(meta)
        normalized[key(state, strip=True)].add(meta)
        old_names.add(state["name"][1])
    computed = []
    stats = {"exact": 0, "normalized": 0, "new_blocks": 0, "ambiguous": 0, "existing_new_variants": 0}
    misses = []
    for entry in new:
        statekey = key(entry)
        possibilities = direct.get(statekey)
        source = "exact"
        if not possibilities:
            possibilities = normalized.get(key(entry, strip=True))
            source = "normalized"
        if possibilities and len(possibilities) == 1:
            computed.append(next(iter(possibilities)))
            stats[source] += 1
        elif entry["name"][1] not in old_names:
            # A block which literally did not exist in the previous release
            # cannot inherit legacy metadata.
            computed.append(0)
            stats["new_blocks"] += 1
        else:
            computed.append(None)
            category = "ambiguous" if possibilities else "existing_new_variants"
            stats[category] += 1
            if len(misses) < 30:
                misses.append({"name": entry["name"][1], "properties": entry["states"][1], "possible": sorted(possibilities or [])[:10]})
    report = {"old_states": len(old), "new_states": len(new), "counts": stats, "examples_unresolved": misses}
    (args.output / "docs").mkdir(parents=True, exist_ok=True)
    (args.output / "docs" / "block-meta-1.26.60-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Block mapping audit:", json.dumps(stats))
    if stats["ambiguous"] or stats["existing_new_variants"]:
        print("Unresolved variants need real item-meta mapping; refusing to emit a speculative file")
        return
    (args.output / "block_state_meta_map-1.26.60.json").write_text(json.dumps(computed, separators=(",", ":")) + "\n")
    print("Complete paired metadata generated:", len(computed))

if __name__ == "__main__":
    main()
