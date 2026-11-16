import os, sys, struct
sys.path.insert(0, os.path.dirname(__file__))
from lugia_common import *
r = Rom()
pg = r.narc('pbr/pokegra.narc'); pm = r.narc('data/pokepic_m.narc'); pf = r.narc('data/pokepic_f.narc')
idx = {}
for i,x in enumerate(pm): idx.setdefault(x, []).append(i)
idxf = {}
for i,x in enumerate(pf): idxf.setdefault(x, []).append(i)
for k in range(1494, 1500):
    print(k, pg[k][:4], 'in pokepic_m', idx.get(pg[k], [])[:10], 'pokepic_f', idxf.get(pg[k], [])[:10])
for k in range(6, 12):
    print(k, pg[k][:4], 'in pokepic_m', idx.get(pg[k], [])[:10])
# strings
for name in list(r.files):
    pass
b = r.b
for s in (b'pokepic', b'pokegra', b'pbr/'):
    i = b.find(s); print(s, hex(i), b[i-20:i+40] if i>=0 else None)
