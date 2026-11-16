import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from collections import Counter, defaultdict
from PIL import Image
from lugia_common import Rom, ncgr_info
ref = Image.open(sys.argv[1]).convert('RGBA'); W, H = ref.size
r = Rom(); n = r.narc('data/pokepic_m.narc')
results = []
for ent in (1992, 1994):
    px = ncgr_info(n[ent])['px']
    sp = [[(px[(y*160+x)//2] >> (4*(x & 1))) & 15 for x in range(160)] for y in range(80)]
    for fx in (0, 80):
        for s in (1, 2):
            for dx in range(-12, 13):
                for dy in range(-12, 13):
                    hit = tot = 0
                    for y in range(80):
                        for x in range(80):
                            i = sp[y][fx+x]; X, Y = x*s+dx, y*s+dy
                            if not (0 <= X < W and 0 <= Y < H): continue
                            a = ref.getpixel((X, Y))[3] > 128
                            tot += 1; hit += (a == (i != 0))
                    results.append((hit/tot, ent, fx, s, dx, dy))
results.sort(reverse=True); print(results[:3])
_, ent, fx, s, dx, dy = results[0]
px = ncgr_info(n[ent])['px']
m = defaultdict(Counter)
for y in range(80):
    for x in range(80):
        i = (px[(y*160+fx+x)//2] >> (4*((fx+x) & 1))) & 15
        if not i: continue
        for yy in range(s):
            for xx in range(s):
                X, Y = x*s+dx+xx, y*s+dy+yy
                if 0 <= X < W and 0 <= Y < H:
                    p = ref.getpixel((X, Y))
                    if p[3] > 128: m[i]['%02x%02x%02x' % p[:3]] += 1
for i in sorted(m): print(i, m[i].most_common(3))
