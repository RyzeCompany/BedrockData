#!/usr/bin/env python3
"""Build 1.26.60 network item dictionary from verified BDS data.

The numeric IDs and new item metadata come from the official BDS Endstone
export. Existing component NBT is preserved from BedrockData 1.26.51 until
the BDS component payload migration has been verified separately.
"""
from __future__ import annotations

import argparse
import gzip
import json
from io import BytesIO
from pathlib import Path
from convert_endstone_12660 import be_string, big_payload, exact

def read_components(path: Path) -> dict:
    stream = BytesIO(gzip.decompress(path.read_bytes()))
    if exact(stream, 1) != b"\x0a" or be_string(stream) != "":
        raise ValueError("Expected named root compound in BDS item components")
    data = big_payload(stream, 10)
    if stream.read():
        raise ValueError("Trailing bytes in BDS item component NBT")
    return data

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("export", type=Path)
    parser.add_argument("--output", type=Path, default=Path("."))
    options = parser.parse_args()
    old = json.loads(Path("required_item_list-1.26.51.json").read_text())
    raw = json.loads((options.export / "data" / "items.json").read_text())
    components = read_components(options.export / "data" / "item_components.nbt")
    if len(raw) != 2080 or len(old) < 2000:
        raise ValueError("Unexpected item dictionary size")
    expected_new = {"minecraft:disc_press", "minecraft:frostbite_spawn_egg", "minecraft:ice_crystal", "minecraft:icicle"}
    new = set(raw) - set(old)
    if new != expected_new or set(old) - set(raw):
        raise ValueError(f"Unexpected newly added or removed items: {new}")
    result = {}
    changed = []
    for name in sorted(raw):
        source = raw[name]
        if not isinstance(source["id"], int):
            raise ValueError(f"Invalid runtime ID for {name}")
        entry = {"runtime_id": source["id"]}
        if name in components:
            t, comp = components[name]
            if t != 10 or set(comp) != {"components", "isComponentBased", "version"}:
                raise ValueError(f"Unrecognized BDS item component structure: {name}")
            component_based = bool(comp["isComponentBased"][1])
            version = comp["version"][1]
            if version not in (0, 1, 2):
                raise ValueError(f"Unexpected BDS item component version: {name} => {version}")
            entry["component_based"] = component_based
            entry["version"] = version
        elif name in old:
            entry["component_based"] = old[name]["component_based"]
            entry["version"] = old[name]["version"]
        else:
            raise ValueError(f"New item {name} has no BDS component metadata")
        prev = old.get(name)
        if prev is not None:
            if (prev["component_based"], prev["version"]) != (entry["component_based"], entry["version"]):
                changed.append(name)
            # Component NBT comes from the earlier authoritative network
            # registry; do not replace it with a guess from BDS metadata.
            if "component_nbt" in prev:
                entry["component_nbt"] = prev["component_nbt"]
        elif entry["component_based"] or entry["version"] != 2:
            raise ValueError(f"New {name} needs a verified component NBT payload")
        result[name] = entry
    if len({e["runtime_id"] for e in result.values()}) != len(result):
        raise ValueError("Duplicate item runtime identifiers")
    if changed:
        raise ValueError(
            f"{len(changed)} items changed component flags/version; inspect upstream NBT first: {changed[:25]}"
        )
    dest = options.output / "required_item_list-1.26.60.json"
    dest.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print("Verified network item dictionary:", len(result), "items, 4 official new items")

if __name__ == "__main__":
    main()
