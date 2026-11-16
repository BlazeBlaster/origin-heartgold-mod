import sys, os, struct, hashlib
sys.path.insert(0, os.path.dirname(__file__))
from nds import *
rom,h = load(sys.argv[1])
fnt = rom[h['fnt_off']:h['fnt_off']+h['fnt_size']]
def walk(did, path, out):
    off, first, _ = struct.unpack_from('<IHH', fnt, (did&0xFFF)*8)
    fid = first
    while True:
        b = fnt[off]; off += 1
        if b == 0: break
        n = b & 0x7F; name = fnt[off:off+n].decode('latin1'); off += n
        if b & 0x80:
            sub = struct.unpack_from('<H', fnt, off)[0]; off += 2
            walk(sub, path+name+'/', out)
        else:
            out[path+name] = fid; fid += 1
files = {}; walk(0xF000, '', files)
def narc(data):
    # BTAF
    o = struct.unpack_from('<H', data, 0xC)[0]
    assert data[o:o+4] == b'BTAF'
    sz = struct.unpack_from('<I', data, o+4)[0]; n = struct.unpack_from('<H', data, o+8)[0]
    fat_ = [struct.unpack_from('<II', data, o+12+i*8) for i in range(n)]
    g = o+sz; g += struct.unpack_from('<I', data, g+4)[0]  # skip BTNF
    assert data[g:g+4] == b'GMIF'
    base = g+8
    return [data[base+s:base+e] for s,e in fat_]
for want in sys.argv[2:]:
    fid = files[want]; ents = narc(fat(rom,h,fid))
    print(want, 'entries', len(ents))
    yield_ = None
    globals()['E_'+str(len(globals()))] = ents
    if 'otherpoke' in want:
        for i in (0x84,0x85,0xE6,0xE7):
            print(' ', hex(i), len(ents[i]), hashlib.md5(ents[i]).hexdigest()[:10])
    if 'icon' in want:
        for i in range(0xB45, min(len(ents),0xB50)):
            print(' ', hex(i), len(ents[i]), hashlib.md5(ents[i]).hexdigest()[:10])
