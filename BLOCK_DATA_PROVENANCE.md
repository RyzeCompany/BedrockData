# Paired block data used by the audit fixes

Source: https://github.com/Amber-PM/BedrockData/tree/436cbbefe62a1cf8eae3d940a339c431d7ba969b

The three 1.26.50 files are copied together without transformation. Palette index links each state to its metadata and signed network ID; do not mix them with the independently ordered 1.26.51 metadata file. The core review branch selects this set for protocol 2193 (1.26.50/1.26.51). Real-client compatibility remains a required staging check.

The 1.26.30 metadata file restores 16,913 values for 16,913 states, removing the extra value which shifted subsequent mappings. Existing 1.26.51 files are retained for comparison.

SHA-256 checksums:

- `canonical_block_states-1.26.50.nbt`: `19e666a3c8b586575cbaeaa45e428139f5470f1e595969f827bf59eb162e1d0c`
- `block_state_meta_map-1.26.50.json`: `ef06f604008de23ce157a819464bb336e5c3152af18bea338ade3de5cf7920c7`
- `block_network_ids-1.26.50.json`: `840c1cb42913290a0785b719db74bd26a0302b1350df2bd84ac9575554766e8d`
- `block_state_meta_map-1.26.30.json`: `2987cbdf1a2ed2291e5130c4817abcdd3c2e1eed483a94370432bba4b13ad101`
