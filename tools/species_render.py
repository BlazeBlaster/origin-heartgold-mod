# Render pokepic sprites (front/back, normal/shiny palette) to PNG for eyeballing.
# python tools/species_render.py <rom> <species> <out.png>
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
from lugia_common import Rom, write_png, bgr555, ncgr_info, nclr_colors

def sprite_idx(data):
    g = ncgr_info(data); px = g['px']; W = g['w']*8; H = g['h']*8
    return [[(px[(y*W+x)//2] >> (4*(x & 1))) & 15 for x in range(W)] for y in range(H)], W, H

def render(rom, s, path, narcs=('data/pokepic_m.narc', 'data/pokepic_f.narc')):
    rows = []
    for nm in narcs:
        n = rom.narc(nm); row = []
        for spr, pal in ((0, 1), (0, 5), (2, 3), (2, 7)):
            idx, W, H = sprite_idx(n[s*8+spr]); cols = [bgr555(c) for c in nclr_colors(n[s*8+pal])[0]]
            row.append([[cols[i] + (255,) if i else (128, 128, 128, 255) for i in r_] for r_ in idx])
        rows.append(row)
    W = len(rows[0][0][0]); H = len(rows[0][0])
    img = [[(40, 40, 40, 255)] * (4*W + 5) for _ in range(len(rows)*H + len(rows) + 1)]
    for ri, row in enumerate(rows):
        for ci, im in enumerate(row):
            for y in range(H):
                for x in range(W): img[1 + ri*(H+1) + y][1 + ci*(W+1) + x] = im[y][x]
    write_png(path, len(img[0]), len(img), img)

if __name__ == '__main__':
    render(Rom(sys.argv[1]), int(sys.argv[2]), sys.argv[3])
