"""Validate the locked historical 419 snapshot, independently of the current data."""

import hashlib
import json
from pathlib import Path


def validate(root: Path) -> None:
    folder = root / "legacy/1.16.100"
    manifest = json.loads((folder / "manifest.json").read_text())
    assert manifest["protocol"] == 419
    assert manifest["minecraft_version"] == "1.16.100"
    assert manifest["source_commit"] == "14f4a765eba40b2c65c6dcd061cbfea6e1d3d4cc"
    expected = {
        "canonical_block_states.nbt", "required_item_list.json", "recipes.json",
        "item_id_map.json", "r12_to_current_block_map.bin", "biome_definitions.nbt",
        "entity_identifiers.nbt", "entity_id_map.json", "LICENSE",
    }
    assert set(manifest["files"]) == expected
    for name, entry in manifest["files"].items():
        data = (folder / name).read_bytes()
        assert len(data) == entry["size"], f"Size mismatch: {name}"
        assert hashlib.sha256(data).hexdigest() == entry["sha256"], name
        header = f"blob {len(data)}\0".encode()
        assert hashlib.sha1(header + data).hexdigest() == entry["upstream_git_blob"], name
        if name.endswith(".json"):
            json.loads(data)

    items = json.loads((folder / "required_item_list.json").read_text())
    assert len(items) == 914
    ids = []
    for name, entry in items.items():
        assert name.startswith("minecraft:"), name
        assert type(entry["runtime_id"]) is int, name
        assert -32768 <= entry["runtime_id"] <= 32767, name
        assert type(entry["component_based"]) is bool, name
        ids.append(entry["runtime_id"])
    assert len(set(ids)) == len(ids), "Duplicate legacy runtime item ID"
    assert items["minecraft:shield"]["runtime_id"] == 355
    assert items["minecraft:stone"]["runtime_id"] == 1
    assert "minecraft:netherite_sword" in items
    assert "minecraft:deepslate" not in items

    recipes = json.loads((folder / "recipes.json").read_text())
    for category in ("shaped", "shapeless", "smelting", "potion_type"):
        assert isinstance(recipes[category], list) and recipes[category], category
    assert (folder / "canonical_block_states.nbt").read_bytes()[0] == 10
    assert (folder / "entity_identifiers.nbt").read_bytes()[0] == 10
    assert (folder / "biome_definitions.nbt").read_bytes()[0] == 10
    print(f"Verified protocol 419: {len(expected)} original assets, {len(items)} unique items")


if __name__ == "__main__":
    validate(Path(__file__).resolve().parents[1])
