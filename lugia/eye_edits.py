# Shadow Lugia sprite pixel edits. Palette slots: 11 bright red, 7 dark red, 5 darkest navy, 4 dark navy, 10 dark slate.
import sys
sys.path.insert(0, 'tools')
from lugia_common import Rom, ncgr_info
_n = Rom().narc('data/pokepic_m.narc')
_fp = ncgr_info(_n[1992])['px']; _bp = ncgr_info(_n[1994])['px']
_f = lambda x, y: (_fp[(y*160+x)//2] >> (4*(x & 1))) & 15
EDITS = {}
# Front sprite. The eye is the black pupil at (12,50) (frame 1) with white/light pixels around it.
for dx, dy in ((0, 0), (83, 4)):          # frame 2 is the same head shifted by (83, 4)
    E = lambda x, y, v: EDITS.__setitem__((1992, x+dx, y+dy), v)
    for x, y in ((12, 49), (13, 49), (13, 50), (12, 51)): E(x, y, 11)   # red iris around the pupil
    for x, y in ((14, 49), (14, 50), (13, 51), (14, 51)): E(x, y, 7)    # dark red rim
    for y in range(44, 53):              # white highlights inside the (now pale) face patch -> patch colour
        for x in range(12, 16):
            if (1992, x+dx, y+dy) not in EDITS and _f(x+dx, y+dy) == 1: E(x, y, 13)
# Back sprite. Eye slit: pupil at (75,31), white pixels down column 74/75.
_b = lambda x, y: EDITS.get((1994, x, y), (_bp[(y*160+x)//2] >> (4*(x & 1))) & 15)
for x, y in ((74, 30), (74, 31), (74, 32), (75, 32)): EDITS[(1994, x, y)] = 11
for x, y in ((74, 33), (74, 34), (74, 35), (75, 35), (75, 36)): EDITS[(1994, x, y)] = 7
for y in range(80):                      # second back frame = first frame
    for x in range(80):
        EDITS[(1994, x+80, y)] = _b(x, y)
