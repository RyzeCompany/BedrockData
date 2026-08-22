# Minecraft Bedrock 26.40 data audit

The `allay-bds-1.26.40.zip` export was compared with the existing BedrockData
formats before adopting any values. Its files are supporting evidence, not
drop-in replacements for PocketMine's own data files.

## Items and runtime IDs

The modern `required_item_list.json` contains 1,976 item identifiers. Its names
exactly match `exported/items.json`, and all 1,976 existing `runtime_id` values
match the corresponding export's `id` values **for this specific snapshot**.
This equality was checked against the existing modern dictionary; it must not
be assumed for unrelated versions or exports.

The `required_item_list-1.26.30.json` snapshot contains 1,934 identifiers. Of
its 1,933 names shared with the export, 586 have different runtime IDs. For
example, `minecraft:acacia_boat` is runtime ID 411 in 26.30 and 382 in 26.40.
The legacy-only `minecraft:debug_stick` uses runtime ID 632; in the modern
dictionary, ID 632 belongs to `minecraft:warped_fungus_on_a_stick`. Therefore,
the legacy snapshot must remain separate and must retain `debug_stick`.

## Blocks, biomes, and tags

The modern block-state map and the export both contain 17,499 block states;
the preserved 26.30 map contains 16,914. The block-properties table and the
export contain 1,379 block identifiers.

All 88 exported biome IDs match the existing biome map after removing the
export's `minecraft:` namespace prefix. The existing map also includes
`dappled_forest` (ID 195), which is not present in the export and is preserved
because absence from one export does not prove the existing entry is invalid.

The modern item-tag map contains all 77 exported tags with matching memberships.
Verified Poplar memberships were completed in the `boat`, `boats`, `door`,
`hanging_sign`, `sign`, and `wooden_slabs` tags. The old 76-tag map is retained
as `item_tags-1.26.30.json`; it does not expose modern experimental tags or
items to legacy clients.

## Creative inventory and recipes

The export contains 123 creative groups. Existing BedrockData contains 127
because it preserves additional education/chemistry groups and full
block-state-aware group icons. The exported `creative_items.nbt` contains no
Poplar, cushion, or straw-bed entries, so none were added to creative inventory
solely because they appear in the item or block registries.

The existing recipe data matches the exported category counts:

| Category | Entries |
| --- | ---: |
| Shaped crafting | 1,118 |
| Shapeless crafting | 1,431 |
| User-data shapeless | 1,084 |
| Potion mixes | 210 |
| Special/multi | 14 |
| Smithing transform | 12 |
| Smithing trim | 1 |
| Container mixes | 2 |

PocketMine filters recipes and potion mixes whose outputs cannot be represented
by its implemented item registry. The integration suite verifies that all four
target client versions can encode and decode the resulting 2,258 recipes and
195 potion mixes.

## NBT and experimental content

The export's `block_palette.nbt`, `creative_items.nbt`, and
`item_components.nbt` are gzip-compressed big-endian NBT. PocketMine consumes
its own uncompressed little-endian canonical block-state data and structured
creative JSON. These NBT exports were inspected but not copied over the
existing files.

Poplar wood, cushions, straw beds, and related entries are associated with the
experimental third game drop described in Mojang's
[Minecraft Bedrock 26.40 release notes](https://www.minecraft.net/en-us/article/minecraft-bedrock-edition-26-40).
They remain present where verified by existing modern item/block registries;
their presence does not imply they are enabled in the stable creative menu.

The 26.44/26.45 hotfix is documented by Mojang in the
[Bedrock Edition 26.44/45 hotfix changelog](https://feedback.minecraft.net/hc/en-us/articles/48149564061965-Minecraft-Bedrock-Edition-26-44-45-Hotfix-Changelog).
No new runtime IDs are inferred solely from the hotfix version numbers.
