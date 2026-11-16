import os, sys, struct
sys.path.insert(0, os.path.dirname(__file__))
from lugia_common import *
r = Rom()
pg = r.narc('pbr/pokegra.narc'); pm = r.narc('data/pokepic_m.narc')
print('1992==1996', pm[1992]==pm[1996], '1994==1998', pm[1994]==pm[1998], '1992==1994', pm[1992]==pm[1994])
print('pbr normal', nclr_colors(pg[1498])[0]); print('pm normal ', nclr_colors(pm[1993])[0])
print('pbr shiny ', nclr_colors(pg[1499])[0])
def img(x, backward=None):
    info = ncgr_info(x); px = info['px']
    if backward is not None:
        n=len(px)//2; v=list(struct.unpack('<%dH'%n, px)); seed = v[-1] if backward else v[0]
        order = range(n-1,-1,-1) if backward else range(n)
        for k in order:
            v[k] ^= seed & 0xFFFF; seed=(seed*0x41C64E6D+0x6073)&0xFFFFFFFF
        px = struct.pack('<%dH'%n, *v)
    w = info['w']*8; h = info['h']*8
    idx = []
    for b in px: idx += [b & 15, b >> 4]
    return w, h, [idx[y*w:(y+1)*w] for y in range(h)]
def render(path, rows, pal, scale=2):
    cols = [(0,0,0,0)] + [bgr555(c)+(255,) for c in pal[1:]]
    out = []
    for row in rows:
        line = [cols[i] for i in row for _ in range(scale)]
        out += [line]*scale
    write_png(path, len(out[0]), len(out), out)
pal = nclr_colors(pm[1993])[0]
for k in (1992,1994):
    w,h,rows = img(pm[k]); render('lugia/_probe_pm%d.png'%k, rows, pal)
w,h,rows = img(pg[1497], True); render('lugia/_probe_pbr1497_bwd.png', rows, pal)
w,h,rows = img(pg[1495], True); render('lugia/_probe_pbr1495_bwd.png', rows, pal)
print('pbr1497 decoded == pm1994?', img(pg[1497],True)[2]==img(pm[1994])[2], img(pg[1495],True)[2]==img(pm[1992])[2])
# index usage
from collections import Counter
c = Counter(i for row in img(pm[1994])[2]+img(pm[1992])[2] for i in row); print(sorted(c.items()))
