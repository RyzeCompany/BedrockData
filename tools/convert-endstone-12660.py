#!/usr/bin/env python3
"""Convert the verified Endstone 1.26.60 BDS palette to network NBT without reordering."""
import argparse
import gzip
import json
import struct
from io import BytesIO
from pathlib import Path


def exact(stream, size):
    value = stream.read(size)
    if len(value) != size:
        raise ValueError('Truncated NBT payload')
    return value


def be_string(stream):
    n = struct.unpack('>H', exact(stream, 2))[0]
    return exact(stream, n).decode('utf-8')


def big_payload(stream, typ):
    if typ in (1, 2, 3, 4):
        return struct.unpack({1: '>b', 2: '>h', 3: '>i', 4: '>q'}[typ], exact(stream, {1: 1, 2: 2, 3: 4, 4: 8}[typ]))[0]
    if typ == 5:
        return struct.unpack(">f", exact(stream, 4))[0]
    if typ == 6:
        return struct.unpack(">d", exact(stream, 8))[0]
    if typ == 7:
        length = struct.unpack(">i", exact(stream, 4))[0]
        if length < 0 or length > 16_777_216:
            raise ValueError("Invalid byte array length")
        return exact(stream, length)
    if typ in (11, 12):
        length = struct.unpack(">i", exact(stream, 4))[0]
        if length < 0 or length > 100_000:
            raise ValueError("Invalid numeric array length")
        pack = ">i" if typ == 11 else ">q"
        width = 4 if typ == 11 else 8
        return [struct.unpack(pack, exact(stream, width))[0] for _ in range(length)]
    if typ == 8:
        return be_string(stream)
    if typ == 10:
        tags = {}
        while (kind := exact(stream, 1)[0]) != 0:
            name = be_string(stream)
            if name in tags:
                raise ValueError('Duplicate NBT property ' + name)
            tags[name] = (kind, big_payload(stream, kind))
        return tags
    if typ == 9:
        kind = exact(stream, 1)[0]
        length = struct.unpack('>i', exact(stream, 4))[0]
        if not 0 <= length <= 100000:
            raise ValueError('Unreasonable NBT list length')
        return (kind, [big_payload(stream, kind) for _ in range(length)])
    raise ValueError(f'Unexpected BDS palette NBT type {typ}')


def varuint(value):
    if not 0 <= value <= 0xFFFFFFFFFFFFFFFF:
        raise ValueError(f'Unsigned varint out of bounds: {value}')
    buf = bytearray()
    while value >= 0x80:
        buf.append((value & 0x7F) | 0x80)
        value >>= 7
    buf.append(value)
    return bytes(buf)


def varint(value, bits):
    return varuint(((value << 1) ^ (value >> (bits - 1))) & ((1 << bits) - 1))


def network_string(value):
    encoded = value.encode('utf-8')
    return varuint(len(encoded)) + encoded


def network_payload(typ, value):
    if typ == 1:
        return struct.pack('b', value)
    if typ == 2:
        return struct.pack('<h', value)
    if typ == 3:
        return varint(value, 32)
    if typ == 4:
        return varint(value, 64)
    if typ == 8:
        return network_string(value)
    if typ == 10:
        return b''.join(bytes((kind,)) + network_string(name) + network_payload(kind, v)
                        for name, (kind, v) in value.items()) + b'\0'
    raise ValueError(f'Unsupported palette tag type {typ}')


def convert(export, output):
    states = json.loads((export / 'data' / 'block_states.json').read_text())
    blob = gzip.decompress((export / 'data' / 'block_palette.nbt').read_bytes())
    reader = BytesIO(blob)
    assert exact(reader, 1) == b'\x0a' and be_string(reader) == ''
    root = big_payload(reader, 10)
    if reader.read() or set(root) != {'blocks'} or root['blocks'][0] != 9:
        raise ValueError('Unrecognized palette root')
    typ, blocks = root['blocks'][1]
    if typ != 10 or len(blocks) != len(states) or len(blocks) != 23960:
        raise ValueError('Palette size mismatch')
    result = bytearray()
    for i, (entry, state) in enumerate(zip(blocks, states)):
        if set(entry) != {'name', 'states', 'version'} or entry['name'][0] != 8 or entry['states'][0] != 10 or entry['version'][0] != 3:
            raise ValueError(f'Unexpected palette compound at index {i}')
        if entry['name'][1] != state['name']:
            raise ValueError(f'Palette ordering mismatch at index {i}')
        result.extend(b'\x0a\x00' + network_payload(10, entry))
    output.mkdir(parents=True, exist_ok=True)
    (output / 'canonical_block_states-1.26.60.nbt').write_bytes(result)
    items = json.loads((export / 'data' / 'items.json').read_text())
    runtime = {name: item['id'] for name, item in items.items()}
    if len(runtime) != 2080 or len(set(runtime.values())) != len(runtime):
        raise ValueError('Invalid item runtime IDs')
    (output / 'item_runtime_ids-1.26.60.json').write_text(json.dumps(runtime, sort_keys=True, separators=(',', ':')) + '\n')
    print('Validated', len(blocks), 'ordered states, network palette bytes', len(result), 'items', len(items))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('export', type=Path)
    parser.add_argument('--output', type=Path, default=Path('.'))
    options = parser.parse_args()
    convert(options.export, options.output)
