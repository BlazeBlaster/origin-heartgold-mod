import sys, struct, os
sys.path.insert(0, os.path.dirname(__file__))
from nds import *
rom,h = load(sys.argv[1])
bins = {'arm9': (h['arm9_ram'], rom[h['arm9_off']:h['arm9_off']+h['arm9_size']])}
for o in overlays(rom,h):
    d = fat(rom,h,o['fid'])
    if (o['flag']>>24)&1:
        try: d = blz_decompress(d)
        except Exception as e: print('ov',o['id'],'decomp fail',e); continue
    bins['ov%d'%o['id']] = (o['ram'], d)
import pickle; pickle.dump(bins, open(sys.argv[2],'wb'))
def words(d):
    return {i: struct.unpack_from('<I',d,i)[0] for i in range(0,len(d)-3,4)}
for name,(ram,d) in bins.items():
    w = words(d)
    for i,v in w.items():
        if v == 0x1EA:  # SPECIES_MANAPHY literal
            near = [ (j, w.get(j)) for j in range(i-40,i+44,4) if w.get(j) in (0x1F5,0x1F6,0x1EE,0x1EB,0x1EC,0x1ED,0x1EF)]
            if near: print(name, hex(ram+i), [(hex(ram+j),hex(v2)) for j,v2 in near])
