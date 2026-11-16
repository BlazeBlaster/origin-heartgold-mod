import struct, sys
def blz_decompress(data):
    # Nintendo backward LZ (overlay/arm9 compression)
    enc_len_and_hdr, add_len = struct.unpack_from('<II', data, len(data)-8)
    hdr_len = enc_len_and_hdr >> 24; enc_len = enc_len_and_hdr & 0xFFFFFF
    out = bytearray(data) + bytearray(add_len)
    src = len(data) - hdr_len; dst = len(out); end = len(data) - enc_len
    while src > end:
        src -= 1; flags = data[src]
        for _ in range(8):
            if src <= end: break
            if flags & 0x80:
                src -= 2; v = data[src] | (data[src+1] << 8)
                n = ((v >> 12) & 0xF) + 3; disp = (v & 0xFFF) + 3
                for _ in range(n):
                    dst -= 1; out[dst] = out[dst+disp]
            else:
                src -= 1; dst -= 1; out[dst] = data[src]
            flags = (flags << 1) & 0xFF
    return bytes(out)
def load(path):
    rom = open(path,'rb').read()
    h = {}
    (h['arm9_off'],h['arm9_entry'],h['arm9_ram'],h['arm9_size']) = struct.unpack_from('<IIII', rom, 0x20)
    (h['fnt_off'],h['fnt_size'],h['fat_off'],h['fat_size'],h['ovt9_off'],h['ovt9_size']) = struct.unpack_from('<IIIIII', rom, 0x40)
    return rom, h
def fat(rom,h,fid):
    s,e = struct.unpack_from('<II', rom, h['fat_off']+fid*8); return rom[s:e]
def overlays(rom,h):
    res=[]
    for i in range(h['ovt9_size']//32):
        o=struct.unpack_from('<8I', rom, h['ovt9_off']+i*32)
        res.append(dict(id=o[0],ram=o[1],size=o[2],bss=o[3],fid=o[6],flag=o[7]))
    return res
