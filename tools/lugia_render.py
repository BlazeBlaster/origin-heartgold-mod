import struct, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from lugia_common import Rom, write_png, bgr555, ncgr_info
r = Rom(); n = r.narc('data/pokepic_m.narc')
def pal(f): return [bgr555(v) for v in struct.unpack('<16H', open('lugia/'+f,'rb').read())]
pals = [pal(f) for f in ('battle_normal_orig.bin','battle_shadowE.bin','battle_shadowF.bin','battle_shadowF.bin')]
def idx(e):
    g = ncgr_info(n[e]); px = g['px']; W = 160
    return [[(px[(y*W+x)//2] >> (4*(x & 1))) & 15 for x in range(80)] for y in range(80)]
sprites = [idx(1992), idx(1994)]
S = 2; pad = 8; W = 4*(80*S+pad)+pad; H = 2*(80*S+pad)+pad
img = [[(128,128,128,255)]*W for _ in range(H)]
for row, sp in enumerate(sprites):
    for col, p in enumerate(pals):
        ox = pad + col*(80*S+pad); oy = pad + row*(80*S+pad)
        for y in range(80*S):
            for x in range(80*S):
                i = sp[y//S][x//S]
                if i: img[oy+y][ox+x] = p[i] + (255,)
write_png('lugia/compare_F.png', W, H, img)
