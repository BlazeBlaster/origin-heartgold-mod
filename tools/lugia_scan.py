import os, sys, struct
sys.path.insert(0, os.path.dirname(__file__))
from lugia_common import *
r = Rom()
for name, fid in sorted(r.files.items()):
    d = r.get(fid)
    if d[:4] != b'NARC': 
        if name.startswith('a/0/0/') or len(d) < 16: print('nonnarc', name, len(d))
        continue
    try: e = narc_parse(d)[0]
    except Exception as x: continue
    if len(e) > 1000:
        kinds = {}
        for x in e[:60]: kinds[x[:4]] = kinds.get(x[:4], 0)+1
        print(name, fid, len(e), kinds)
