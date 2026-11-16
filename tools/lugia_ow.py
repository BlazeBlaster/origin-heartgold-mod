import os, sys, struct
sys.path.insert(0, os.path.dirname(__file__))
from lugia_common import *
r = Rom()
oi = r.narc('data/pokemon_overworld_info.narc')
print(len(oi), set(len(x) for x in oi))
for k in (0,1,25,249,250,491,492,493,494,495,1020,1025): print(k, oi[k].hex() if k < len(oi) else None)
ow = r.narc('a/0/8/1'); print('a/0/8/1', len(ow))
def btx_info(d):
    tex = struct.unpack_from('<I', d, 0x10)[0]
    t = d[tex:]
    ntex = t[0x3D]; 
    # palette dict
    pinfo = struct.unpack_from('<H', t, 0x34)[0]; npal = t[pinfo+1]
    return ntex, npal
for k in (842, 973):
    if k < len(ow): print(k, len(ow[k]), btx_info(ow[k]))
