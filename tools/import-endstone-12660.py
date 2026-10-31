#!/usr/bin/env python3
"""Import verified, lossless 1.26.60 data from the Endstone Linux BDS export.

This imports only assets whose schema is compatible with BedrockData. Do NOT
invent id/meta mappings or use these inputs as a drop-in canonical palette.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

EXPECTED_COMMIT = "9700a4649bc4d6897810a89ee8b6f32bdbbb594b"
EXPECTED_RUN = "40758269886"
REQUIRED_FILES = (
    "biomes.json", "block_palette.nbt", "block_states.json",
    "block_tags.json", "block_types.json", "creative_groups.json",
    "creative_items.nbt", "item_components.nbt", "item_tags.json",
    "items.json", "recipes.json",
)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("export_dir", type=Path, help="Extracted Actions artifact directory")
    parser.add_argument("--output", type=Path, default=Path("."))
    args = parser.parse_args()
    source = args.export_dir
    report = read_json(source / "manifest.json")
    assert report.get("status") == "success" and report.get("errors") == [], "Export was not successful"
    assert report.get("bds_version") in ("26.60", "1.26.60"), "Wrong BDS version"
    assert str(report.get("workflow_run_id")) == EXPECTED_RUN, "Wrong Actions run"
    assert report.get("commit") == EXPECTED_COMMIT, "Wrong Endstone revision"
    assert report.get("server_started") is True and report.get("export_completed") is True
    assert report.get("jigsaw_packet_captured") is False, "Review Jigsaw separately if available"
    manifest_files = report["files"]
    assert set(manifest_files) == set(REQUIRED_FILES), "Unexpected data file set"
    for filename in REQUIRED_FILES:
        data = (source / "data" / filename).read_bytes()
        metadata = manifest_files[filename]
        assert len(data) == metadata["bytes"], f"Size mismatch in {filename}"
        assert hashlib.sha256(data).hexdigest() == metadata["sha256"], f"Hash mismatch in {filename}"

    states = read_json(source / "data" / "block_states.json")
    assert isinstance(states, list) and len(states) == 23960
    hashes: list[int] = []
    for state in states:
        value = state["blockStateHash"]
        assert isinstance(value, int) and 0 <= value <= 0xFFFFFFFF
        hashes.append(value if value < 0x80000000 else value - 0x100000000)
    assert len(set(hashes)) == len(hashes), "Block state hash collision"

    # Endstone exports a gzip-compressed big-endian NBT root with a "blocks"
    # list. This is NOT the PMMP canonical_block_states.nbt wire format.
    palette = gzip.decompress((source / "data" / "block_palette.nbt").read_bytes())
    assert palette.startswith(b"\x0a\x00\x00\x09\x00\x06blocks\x0a"), "Unexpected palette format"
    # The first list element is tag 10 (compound); the four bytes that
    # follow the "blocks" name are the number of list entries.
    count = int.from_bytes(palette[13:17], "big", signed=True)
    assert count == len(states), "Palette and hash list counts differ"

    item_tags = read_json(source / "data" / "item_tags.json")
    assert isinstance(item_tags, dict) and len(item_tags) > 0
    assert all(isinstance(k, str) and isinstance(v, list) for k, v in item_tags.items())

    out = args.output
    write_json(out / "block_network_ids-1.26.60.json", hashes)
    write_json(out / "item_tags-1.26.60.json", item_tags)
    # Retain the exact Endstone manifest for provenance and future converters.
    write_json(out / "docs" / "endstone-1.26.60-manifest.json", report)
    print(f"Validated BDS 26.60: {len(hashes)} block hashes, {len(item_tags)} item tags.")
    print("Remaining before runtime use: canonical palette, metadata maps, item registry,")
    print("codec changes, Jigsaw packet capture and real-client tests.")


if __name__ == "__main__":
    main()
