# BedrockData 1.0.0-beta.2

Includes the verified, versioned Minecraft Bedrock 1.26.60 palette, item registry, item tags, block network IDs and historic metadata mapping used by RyzeMP protocol 2225. The original Endstone/BDS export provenance is retained: 23,960 block states and 2,080 item IDs.

`python3 tools/validate-12660.py` verifies the original palette/registry checksums, paired array lengths, unique IDs, tags and unresolved-state audit. RyzeMP integration also validates NBT decoding, creative/crafting wire packets, all 64 chorus-plant states and actual PHAR world spawn. The operator has confirmed retail-client world entry; exhaustive gameplay remains beta validation.

Use the `-1.26.60` assets for protocol 2225. Unversioned assets and `protocol_info.json` retain their legacy baseline, preserving existing consumers; they must not be combined with a versioned palette. RyzeMP selects the paired versioned files automatically.

Composer: `ryzemcbe/bedrock-data:1.0.0-beta.2`. Package name and public distribution remain unchanged.
