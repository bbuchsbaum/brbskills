"""Small validation helpers shared by the progress commands (standard library only)."""
import json
import os
from pathlib import Path
import re
import tempfile
import struct
import zlib


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', value):
        raise ValueError(f'Invalid identifier: {value!r}')
    return value


def child(root, *parts):
    root = Path(root).resolve()
    candidate = root.joinpath(*parts)
    if not candidate.resolve().is_relative_to(root):
        raise ValueError(f'Path escapes harness: {candidate}')
    return candidate


def config():
    harness = Path(os.environ.get('HARNESS', Path(__file__).resolve().parent.parent)).resolve()
    cfg = json.loads((harness / 'hillclimb.json').read_text(encoding='utf-8'))
    dims, critics, shots = cfg.get('dims'), cfg.get('critics'), cfg.get('shots')
    if (not isinstance(dims, list) or not dims or
        any(not isinstance(d, str) or not d.strip() or d != d.strip() or '|' in d or '\n' in d for d in dims) or
        len(set(dims)) != len(dims) or any(d.lower() in {'mean', 'dimension'} for d in dims)):
        raise ValueError('dims must contain unique nonempty dimension names (not mean/dimension)')
    if not isinstance(critics, dict) or not critics:
        raise ValueError('critics must map identifiers to labels')
    for key, label in critics.items():
        identifier(key)
        if not isinstance(label, str) or not label.strip():
            raise ValueError('Each critic needs a label')
    if not isinstance(shots, list) or not shots:
        raise ValueError('shots must be a nonempty array')
    names = [identifier(s['name']) for s in shots]
    if len(set(names)) != len(names):
        raise ValueError('Shot names must be unique')
    return harness, cfg


def png(path):
    """Check PNG chunk integrity and compressed data, not visual correctness."""
    if not path.is_file():
        raise ValueError(f'Missing PNG: {path}')
    seen, decoder = [], zlib.decompressobj()
    decoded = 0
    with path.open('rb') as stream:
        if stream.read(8) != b'\x89PNG\r\n\x1a\n':
            raise ValueError(f'Invalid PNG signature: {path}')
        while True:
            header = stream.read(8)
            if len(header) != 8:
                raise ValueError(f'Truncated PNG: {path}')
            length, kind = struct.unpack('>I4s', header)
            if length > path.stat().st_size:
                raise ValueError(f'Invalid PNG chunk size: {path}')
            data, crc = stream.read(length), stream.read(4)
            if len(data) != length or len(crc) != 4 or struct.unpack('>I', crc)[0] != zlib.crc32(kind + data):
                raise ValueError(f'Invalid PNG chunk/CRC: {path}')
            if not seen and kind != b'IHDR':
                raise ValueError(f'PNG must start with IHDR: {path}')
            if kind == b'IHDR':
                if seen or len(data) != 13:
                    raise ValueError(f'Invalid PNG header: {path}')
                width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', data)
                depths = {0: (1, 2, 4, 8, 16), 2: (8, 16), 3: (1, 2, 4, 8), 4: (8, 16), 6: (8, 16)}
                if not width or not height or depth not in depths.get(color, ()) or compression or filtering or interlace not in (0, 1):
                    raise ValueError(f'Invalid PNG header fields: {path}')
                channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color]
                passes = [(0, 0, 1, 1)] if not interlace else [(0, 0, 8, 8), (4, 0, 8, 8), (0, 4, 4, 8), (2, 0, 4, 4), (0, 2, 2, 4), (1, 0, 2, 2), (0, 1, 1, 2)]
                expected = 0
                for x, y, dx, dy in passes:
                    w, h = max(0, (width - x + dx - 1) // dx), max(0, (height - y + dy - 1) // dy)
                    if w and h:
                        expected += h * (1 + (w * channels * depth + 7) // 8)
            if kind == b'IDAT':
                # Drain in bounded chunks; a compressed image must form a valid zlib stream.
                try:
                    while data:
                        decoded += len(decoder.decompress(data, 1024 * 1024))
                        if decoded > expected:
                            raise ValueError(f'PNG image exceeds declared dimensions: {path}')
                        data = decoder.unconsumed_tail
                except zlib.error as error:
                    raise ValueError(f'Corrupt PNG image stream: {path}') from error
            seen.append(kind)
            if kind == b'IEND':
                if length or b'IDAT' not in seen or decoded != expected or not decoder.eof or decoder.unused_data or stream.read(1):
                    raise ValueError(f'Incomplete PNG image: {path}')
                return


def image_files(harness, cfg, round_id, base):
    result = []
    for shot in cfg['shots']:
        for kind in ('fold', 'full'):
            file = child(harness, base, round_id, f"{shot['name']}-{kind}.png")
            png(file)
            result.append(file)
    return result


def atomic_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
