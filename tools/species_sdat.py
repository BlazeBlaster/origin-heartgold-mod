# Minimal SDAT reader: symbol names + INFO records for SEQ / BANK / WAVEARC.  Read-only helpers.
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))

def sdat_blocks(d):
    symb, symbs, info, infos, fat_, fats = struct.unpack_from('<6I', d, 0x10)
    return symb, info, fat_

def _names(d, symb, rec):
    if not symb: return None
    off = struct.unpack_from('<I', d, symb + 8 + 4*rec)[0]; b = symb + off
    n = struct.unpack_from('<I', d, b)[0]; out = []
    for i in range(n):
        o = struct.unpack_from('<I', d, b + 4 + 4*i)[0]
        out.append(d[symb+o:d.index(b'\0', symb+o)].decode('latin1') if o else None)
    return out

def info_records(d, rec):
    """rec: 0 SEQ, 1 SEQARC, 2 BANK, 3 WAVEARC. Returns list of absolute offsets (or 0)."""
    _, info, _ = sdat_blocks(d)
    off = struct.unpack_from('<I', d, info + 8 + 4*rec)[0]; b = info + off
    n = struct.unpack_from('<I', d, b)[0]
    return [(info + struct.unpack_from('<I', d, b + 4 + 4*i)[0]) if struct.unpack_from('<I', d, b + 4 + 4*i)[0] else 0 for i in range(n)]

def names(d, rec):
    symb, _, _ = sdat_blocks(d); return _names(d, symb, rec)
