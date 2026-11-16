import os, sys, struct
sys.path.insert(0, os.path.dirname(__file__))
from lugia_common import *
r = Rom()
pg = r.narc('pbr/pokegra.narc'); pm = r.narc('data/pokepic_m.narc'); pf = r.narc('data/pokepic_f.narc')
def dec(px, backward):
    n = len(px)//2; v = list(struct.unpack('<%dH' % n, px))
    if backward: seed = v[-1]; order = range(n-1, -1, -1)
    else: seed = v[0]; order = range(n)
    out = v[:]
    for k in order:
        out[k] ^= seed & 0xFFFF
        seed = (seed * 0x41C64E6D + 0x6073) & 0xFFFFFFFF
    return out
# standard pokeditor: seed=last/first, then xor with (rand>>16) where rand advanced first
def dec2(px, backward):
    n = len(px)//2; v = list(struct.unpack('<%dH' % n, px))
    if backward: seed = v[-1]; order = range(n-1, -1, -1)
    else: seed = v[0]; order = range(n)
    out = v[:]
    for k in order:
        out[k] ^= seed & 0xFFFF
        seed = (seed * 0x41C64E6D + 0x6073) & 0xFFFFFFFF
        seed_hi = seed
    return out
def zero_frac(words):
    # count index-0 nibbles (transparent): clean image should have many
    z = 0
    for w in words:
        for s in (0,4,8,12): z += ((w>>s)&15)==0
    return z/(len(words)*4)
for nm, e, ks in (('pbr', pg, [1495,1497]), ('pm', pm, list(range(1992,2000))), ('pf', pf, list(range(1992,2000)))):
    for k in ks:
        x = e[k]
        if x[:4] != b'RGCN': print(nm, k, x[:4], len(x), x[:4] and nclr_colors(x)[0] if x[:4]==b'RLCN' else ''); continue
        info = ncgr_info(x)
        raw = list(struct.unpack('<%dH' % (len(info['px'])//2), info['px']))
        print(nm, k, {a:b for a,b in info.items() if a!='px'}, 'raw0', round(zero_frac(raw),3),
              'fwd', round(zero_frac(dec(info['px'], False)),3), 'bwd', round(zero_frac(dec(info['px'], True)),3))
