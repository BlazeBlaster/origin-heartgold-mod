import os, sys, struct
sys.path.insert(0, os.path.dirname(__file__))
from lugia_common import *
r = Rom()
for nm in ('data/pokepic_m.narc','data/pokepic_f.narc','pbr/pokegra.narc'):
    e = r.narc(nm)
    print(nm, r.files[nm], len(e))
    print(' ', [(i, x[:4], len(x)) for i,x in enumerate(e[:16])])
    print(' 249*4..', [(i, x[:4], len(x)) for i,x in enumerate(e[996:1004], 996)])
