import sys, os, struct, zlib
sys.path.insert(0, os.path.dirname(__file__))
from ohg import fnt_files, narc_parse
from nds import load
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROMP = os.path.join(ROOT, 'rom', 'ohg.nds')
class Rom:
    def __init__(self, path=ROMP):
        self.b, self.h = load(path)
        self.files = fnt_files(self.b, self.h)
    def get(self, fid):
        s, e = struct.unpack_from('<II', self.b, self.h['fat_off'] + fid*8); return self.b[s:e]
    def narc(self, name):
        return narc_parse(self.get(self.files[name]))[0]

def write_png(path, w, h, rgba):
    """rgba: list of rows of (r,g,b,a)"""
    raw = b''.join(b'\0' + bytes(c for px in row for c in px) for row in rgba)
    def chunk(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
                           + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))

def bgr555(v):
    r, g, b = v & 31, (v >> 5) & 31, (v >> 10) & 31
    return (r*255//31, g*255//31, b*255//31)
def to555(rgb):
    r, g, b = (min(31, round(c*31/255)) for c in rgb); return r | (g << 5) | (b << 10)

def find_block(data, magic):
    i = data.find(magic); return i
def nclr_colors(data):
    i = data.find(b'TTLP'); sz = struct.unpack_from('<I', data, i+0x10)[0]; off = struct.unpack_from('<I', data, i+0x14)[0]
    p = i + 8 + off
    return [struct.unpack_from('<H', data, p + 2*k)[0] for k in range(16)], p

def rand_decrypt(px, backward):
    n = len(px)//2; v = list(struct.unpack('<%dH' % n, px))
    if backward:
        seed = v[-1]; idx = range(n-1, -1, -1)
    else:
        seed = v[0]; idx = range(n)
    out = v[:]
    for k in idx:
        out[k] ^= seed & 0xFFFF
        seed = (seed * 0x41C64E6D + 0x6073) & 0xFFFFFFFF
        out[k] ^= 0  # placeholder
    return out

def ncgr_info(data):
    i = data.find(b'RAHC')
    hgt, wid, depth, u1, mapping, mode, size, off = struct.unpack_from('<HHIHHIII', data, i+8)
    px = data[i+8+off: i+8+off+size]
    return dict(h=hgt, w=wid, depth=depth, mode=mode, size=size, px=px, mapping=mapping)
