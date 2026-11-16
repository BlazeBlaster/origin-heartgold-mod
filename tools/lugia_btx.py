import os, sys, struct
sys.path.insert(0, os.path.dirname(__file__))
from lugia_common import *
def btx_parse(d):
    tex = struct.unpack_from('<I', d, 0x10)[0]; t = d[tex:]
    def dic(off):
        n = t[off+1]; hdr = struct.unpack_from('<H', t, off+6)[0]  # unknown block
        size_unit = struct.unpack_from('<H', t, off+4+hdr)[0] if False else None
        # standard: dict header 8 bytes + 4*(n+1)? use names at end
        p = off + struct.unpack_from('<H', t, off+6)[0]  # skip patricia tree
        unit, sz = struct.unpack_from('<HH', t, p); data = [t[p+4+i*unit:p+4+(i+1)*unit] for i in range(n)]
        names = [t[p+sz+i*16:p+sz+(i+1)*16].rstrip(b'\0').decode('latin1') for i in range(n)]
        return n, data, names
    texdata_off = struct.unpack_from('<I', t, 0x14)[0]
    texdict = struct.unpack_from('<H', t, 0x0E)[0]
    paldata_off = struct.unpack_from('<I', t, 0x38)[0]; paldict = struct.unpack_from('<H', t, 0x34)[0]
    ntex, tdat, tnames = dic(texdict); npal, pdat, pnames = dic(paldict)
    texs = []
    for e, nm in zip(tdat, tnames):
        if len(e) < 4: continue
        o, p = struct.unpack_from('<HH', e, 0); param = o | (p << 16)
        off = (param & 0xFFFF) << 3; w = 8 << ((param >> 20) & 7); h = 8 << ((param >> 23) & 7); fmt = (param >> 26) & 7; c0 = (param >> 29) & 1
        texs.append(dict(name=nm, off=texdata_off+off, w=w, h=h, fmt=fmt, c0=c0))
    pals = []
    for e, nm in zip(pdat, pnames):
        o = struct.unpack_from('<H', e, 0)[0] << 3
        pals.append(dict(name=nm, off=paldata_off+o, cols=[struct.unpack_from('<H', t, paldata_off+o+2*k)[0] for k in range(16)]))
    return t, texs, pals
if __name__ == '__main__':
    r = Rom(); ow = r.narc('a/0/8/1')
    for k in (579, 842):
        t, texs, pals = btx_parse(ow[k])
        print(k, [(x['name'], x['w'], x['h'], x['fmt'], x['c0']) for x in texs])
        for p in pals: print('  pal', p['name'], [hex(c) for c in p['cols']])
