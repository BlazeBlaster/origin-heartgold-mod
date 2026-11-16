import sys, os, struct, json
sys.path.insert(0, os.path.dirname(__file__))
from ohg import *
def parse(d):
    o = 0; nbg = struct.unpack_from('<I', d, o)[0]; o += 4 + nbg*20
    nobj = struct.unpack_from('<I', d, o)[0]; o += 4
    objs = []
    for i in range(nobj):
        f = struct.unpack_from('<14H', d, o)
        objs.append(dict(off=o, id=f[0], sprite=f[1], move=f[2], type=f[3], flag=f[4], script=f[5], dir=f[6]))
        o += 32
    return objs
if __name__ == '__main__':
    rom, h = load(sys.argv[1]); files = fnt_files(rom, h)
    ev, _ = narc_parse(fat(rom, h, files['a/0/3/2']))
    z = json.load(open(os.path.join(ROOT, 'ref/ohgrepo/bank_maps.json'), encoding='utf-8'))['_zones']
    hits = {}
    for zz in z:
        eb = zz['events_bank']
        if eb >= len(ev) or eb in hits: continue
        try: objs = parse(ev[eb])
        except Exception: continue
        for ob in objs:
            if ob['sprite'] in (428, 432, 453, 454, 71):
                print('zone', zz['zone_id'], zz['map_name_en'], zz['vanilla_const'], 'evbank', eb, ob)
        hits[eb] = 1
