import struct, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from nds import load, fat, overlays, blz_decompress

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def fnt_files(rom, h):
    fnt = rom[h['fnt_off']:h['fnt_off']+h['fnt_size']]
    out = {}
    def walk(did, path):
        off, first, _ = struct.unpack_from('<IHH', fnt, (did & 0xFFF)*8)
        fid = first
        while True:
            b = fnt[off]; off += 1
            if b == 0: break
            n = b & 0x7F; name = fnt[off:off+n].decode('latin1'); off += n
            if b & 0x80:
                sub = struct.unpack_from('<H', fnt, off)[0]; off += 2
                walk(sub, path+name+'/')
            else:
                out[path+name] = fid; fid += 1
    walk(0xF000, '')
    return out

def narc_parse(data):
    o = struct.unpack_from('<H', data, 0xC)[0]
    assert data[o:o+4] == b'BTAF'
    sz = struct.unpack_from('<I', data, o+4)[0]; n = struct.unpack_from('<H', data, o+8)[0]
    fat_ = [struct.unpack_from('<II', data, o+12+i*8) for i in range(n)]
    g = o+sz
    btnf = data[g:g+struct.unpack_from('<I', data, g+4)[0]]
    g += len(btnf)
    assert data[g:g+4] == b'GMIF'
    base = g+8
    return [bytes(data[base+s:base+e]) for s, e in fat_], btnf

def narc_build(ents, btnf):
    btaf = bytearray(b'BTAF' + struct.pack('<IHH', 12+8*len(ents), len(ents), 0))
    gmif = bytearray();
    for e in ents:
        s = len(gmif); gmif += e; btaf += struct.pack('<II', s, len(gmif))
        while len(gmif) % 4: gmif += b'\xff'
    gm = b'GMIF' + struct.pack('<I', 8+len(gmif)) + gmif
    body = bytes(btaf) + btnf + gm
    hdr = b'NARC' + struct.pack('<HHIHH', 0xFFFE, 0x0100, 16+len(body), 16, 3)
    return hdr + body

# ---- text ----
_cm = {}; _rcm = {}
for line in open(os.path.join(ROOT, 'ref', 'charmap.txt'), encoding='utf-8', errors='replace'):
    line = line.split('//')[0].rstrip('\n')
    if '=' not in line or len(line) < 5: continue
    k, v = line.split('=', 1)
    try: c = int(k.strip(), 16)
    except ValueError: continue
    if c not in _cm: _cm[c] = v
    if v not in _rcm: _rcm[v] = c

def msg_decode(data):
    n, seed = struct.unpack_from('<HH', data, 0)
    out = []
    for i in range(n):
        k = (seed * 0x2FD) & 0xFFFF
        k = (k * (i+1)) & 0xFFFF; kk = k | (k << 16)
        off, ln = struct.unpack_from('<II', data, 4+i*8)
        off ^= kk; ln ^= kk
        key = (0x91BD3 * (i+1)) & 0xFFFF
        chars = []
        for j in range(ln):
            c = struct.unpack_from('<H', data, off+j*2)[0] ^ key
            key = (key + 0x493D) & 0xFFFF
            chars.append(c)
        out.append(chars)
    return out, seed

def msg_encode(strings, seed):
    n = len(strings)
    hdr = bytearray(struct.pack('<HH', n, seed)); body = bytearray()
    base = 4 + 8*n
    for i, chars in enumerate(strings):
        k = (seed * 0x2FD) & 0xFFFF
        k = (k * (i+1)) & 0xFFFF; kk = k | (k << 16)
        hdr += struct.pack('<II', (base+len(body)) ^ kk, len(chars) ^ kk)
        key = (0x91BD3 * (i+1)) & 0xFFFF
        for c in chars:
            body += struct.pack('<H', c ^ key); key = (key + 0x493D) & 0xFFFF
    return bytes(hdr + body)

def chars_to_str(chars):
    s = []; i = 0
    while i < len(chars):
        c = chars[i]
        if c == 0xFFFF: break
        if c == 0xFFFE:
            cmd = chars[i+1]; na = chars[i+2]; args = chars[i+3:i+3+na]
            s.append('{%04X:%s}' % (cmd, ','.join(str(a) for a in args))); i += 3+na; continue
        if c == 0xF100:
            s.append('{COMP}'); i += 1; continue
        v = _cm.get(c)
        if v is None: s.append('{x%04X}' % c)
        elif v == '\\n': s.append('\\n')
        elif v == '\\r': s.append('\\r')
        elif v == '\\f': s.append('\\f')
        else: s.append(v)
        i += 1
    return ''.join(s)

def str_to_chars(s):
    out = []; i = 0
    while i < len(s):
        if s[i] == '{':
            j = s.index('}', i); tok = s[i+1:j]; i = j+1
            if tok.startswith('x'): out.append(int(tok[1:], 16)); continue
            if tok == 'COMP': out.append(0xF100); continue
            cmd, args = tok.split(':')
            args = [int(a) for a in args.split(',')] if args else []
            out += [0xFFFE, int(cmd, 16), len(args)] + args; continue
        if s[i] == '\\':
            out.append(_rcm['\\' + s[i+1]]); i += 2; continue
        out.append(_rcm[s[i]]); i += 1
    out.append(0xFFFF)
    return out
