import os, sys, struct
sys.path.insert(0, os.path.dirname(__file__))
from lugia_common import *
from nds import overlays, blz_decompress
r = Rom(); b = r.b; h = r.h
blobs = {'arm9': b[h['arm9_off']:h['arm9_off']+h['arm9_size']]}
for o in overlays(b, h):
    d = r.get(o['fid'])
    if o['flag'] & 0x01000000:
        try: d = blz_decompress(d)
        except Exception: pass
    blobs['ov%d' % o['id']] = d
for nm, d in blobs.items():
    for stride in (4, 6, 8, 12):
        for fmt_off in range(0, stride, 2):
            pass
    # search u16 973 then 842 within 8 bytes
    for i in range(0, len(d)-12, 2):
        if struct.unpack_from('<H', d, i)[0] == 973:
            for j in range(2, 12, 2):
                if struct.unpack_from('<H', d, i+j)[0] == 842:
                    print(nm, hex(i), j, d[i-16:i+24].hex())
d = blobs['arm9']; i = 0xfd0c0
# walk back to table start
s = i
while struct.unpack_from('<H', d, s-2)[0] in (0x4e27,) or True:
    a, m, f = struct.unpack_from('<HHH', d, s-6)
    if a > 2000 or m > 1734: break
    s -= 6
e = i
while True:
    a, m, f = struct.unpack_from('<HHH', d, e)
    if a > 2000 or m > 1734: break
    e += 6
print('table arm9', hex(s), hex(e), (e-s)//6, 'ram', hex(0x2000000+s))
tab = [struct.unpack_from('<HHH', d, k) for k in range(s, e, 6)]
print(tab[:5])
for t in tab:
    if t[0] in (710, 282, 973, 25+428, 25): print(t)
