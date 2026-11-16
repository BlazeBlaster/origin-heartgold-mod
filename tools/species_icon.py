# Render Lugia's party icon with each shared icon palette (helps choose an icon palette).
# python tools/species_icon.py <rom> <species> <out.png>
import sys, os, struct
from collections import Counter
sys.path.insert(0, os.path.dirname(__file__))
from lugia_common import Rom, write_png, bgr555, ncgr_info

def icon_pixels(data):
    g = ncgr_info(data); px = g['px']; W, H = 32, len(px) * 2 // 32
    if g['h'] == 0xFFFF or True:  # icons are 4x4-tile objects stacked: decode as 8x8 tiles, 4 tiles per row
        out = [[0]*W for _ in range(H)]
        for t in range(len(px) // 32):
            tx, ty = t % 4, t // 4
            for y in range(8):
                for x in range(8):
                    v = (px[t*32 + y*4 + x//2] >> (4*(x & 1))) & 15
                    out[ty*8+y][tx*8+x] = v
        return out

def palettes(rom):
    d = rom.narc('data/pokeicon.narc')[0]; i = d.find(b'TTLP'); off = struct.unpack_from('<I', d, i+0x14)[0]
    sz = struct.unpack_from('<I', d, i+0x10)[0]; p = i + 8 + off
    return [[bgr555(struct.unpack_from('<H', d, p + 32*k + 2*c)[0]) for c in range(16)] for k in range(sz // 32)]

if __name__ == '__main__':
    rom = Rom(sys.argv[1]); s = int(sys.argv[2])
    h = rom.h; a = h['arm9_off'] + 0x020FF7FC - h['arm9_ram']
    use = Counter(rom.b[a:a+1441]); print('palette use counts:', sorted(use.items()), 'species', s, '->', rom.b[a+s])
    pals = palettes(rom); idx = icon_pixels(rom.narc('data/pokeicon.narc')[7 + 2*s])
    n = max(use) + 1; S = 3; W = n * (32*S + 4) + 4; H = 32*S + 8
    img = [[(255, 255, 255, 255)] * W for _ in range(H)]
    for k in range(n):
        for y in range(32*S):
            for x in range(32*S):
                v = idx[y//S][x//S]
                if v: img[4+y][4 + k*(32*S+4) + x] = pals[k][v] + (255,)
    for k in range(n):
        lum = sum(sum(pals[k][v]) for row in idx for v in row if v) / max(1, sum(1 for row in idx for v in row if v)) / 3
        print('pal', k, 'mean brightness of icon pixels %.0f' % lum)
    write_png(sys.argv[3], W, H, img)
