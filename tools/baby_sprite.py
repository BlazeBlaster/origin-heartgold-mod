# Lugiling (baby Shadow Lugia) battle sprites from the user's pixel art (lugia/baby_front.png, lugia/baby_back.png:
# cleaned, native-resolution cut-outs of lugia/baby_sheet_src.webp, transparent background).
# Output: one 16-colour palette (index 0 = transparent) shared by both, and 160x80 index grids (two 80x80 frames).
# Frame 2 is frame 1 one pixel lower (a small bob for the entry animation). Sprites sit centred, feet at y = FEET.
import os
from PIL import Image

LUGIA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lugia')
FEET = 76

def _to555(c):
    r, g, b = (v >> 3 for v in c[:3]); return r | g << 5 | b << 10

def load():
    ims = [Image.open(os.path.join(LUGIA_DIR, 'baby_%s.png' % n)).convert('RGBA') for n in ('front', 'back')]
    solid = [p[:3] for im in ims for p in im.getdata() if p[3]]
    strip = Image.new('RGB', (len(solid), 1)); strip.putdata(solid)
    q = strip.quantize(13, method=Image.Quantize.MEDIANCUT)
    pal = [tuple(q.getpalette()[3*i:3*i+3]) for i in range(13)]
    pal += [max(solid, key=sum), min(solid, key=sum)]          # keep the eye white and the outline black exact
    cols = [(0, 200, 0)] + pal                                  # index 0: transparent (colour unused)
    def near(c):
        return 1 + min(range(15), key=lambda i: sum((a - b)**2 for a, b in zip(c, pal[i])))
    grids = []
    for im in ims:
        w, h = im.size; g = [[0]*160 for _ in range(80)]
        x0, y0 = 40 - w//2, FEET - h
        for y in range(h):
            for x in range(w):
                p = im.getpixel((x, y))
                if p[3]:
                    v = near(p[:3]); g[y0+y][x0+x] = v
                    if y0 + y + 1 < 80: g[y0+y+1][80+x0+x] = v
        grids.append(g)
    palb = b''.join(_to555(c).to_bytes(2, 'little') for c in cols)
    return palb, grids[0], grids[1]

# ---- follower (overworld) sprite: 8 textures of 32x32, 4bpp, colour 0 transparent (small-follower layout, as Pikachu's):
# 0-1 back, 2-3 front, 4-5 facing left, 6-7 = 4-5 mirrored (facing right). Feet at y 29, centred.
OW_ORDER = ('back1', 'back2', 'front1', 'front2', 'side1', 'side2', 'side1', 'side2')
OW_FEET = 29

def _fill_holes(im):
    px = im.load(); w, h = im.size
    for y in range(1, h-1):
        for x in range(1, w-1):
            if px[x, y][3]: continue
            nb = [px[x+dx, y+dy] for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)) if px[x+dx, y+dy][3]]
            if len(nb) >= 3: px[x, y] = nb[0]
    return im

def load_follower():
    ims = {k: _fill_holes(Image.open(os.path.join(LUGIA_DIR, 'baby_ow_%s.png' % k)).convert('RGBA'))
           for k in set(OW_ORDER)}
    solid = [p[:3] for im in ims.values() for p in im.getdata() if p[3]]
    strip = Image.new('RGB', (len(solid), 1)); strip.putdata(solid)
    q = strip.quantize(13, method=Image.Quantize.MEDIANCUT)
    pal = [tuple(q.getpalette()[3*i:3*i+3]) for i in range(13)] + [max(solid, key=sum), min(solid, key=sum)]
    near = lambda c: 1 + min(range(15), key=lambda i: sum((a - b)**2 for a, b in zip(c, pal[i])))
    texs = []
    for n, k in enumerate(OW_ORDER):
        im = ims[k]
        if n >= 6: im = im.transpose(Image.FLIP_LEFT_RIGHT)
        w, h = im.size; assert w <= 32 and h <= OW_FEET + 1, (k, w, h)
        g = [[0]*32 for _ in range(32)]; x0, y0 = 16 - w//2, OW_FEET + 1 - h
        for y in range(h):
            for x in range(w):
                p = im.getpixel((x, y))
                if p[3]: g[y0+y][x0+x] = near(p[:3])
        texs.append(bytes(g[y][x] | g[y][x+1] << 4 for y in range(32) for x in range(0, 32, 2)))
    palb = b''.join(_to555(c).to_bytes(2, 'little') for c in [(0, 200, 0)] + pal)
    return palb, texs
