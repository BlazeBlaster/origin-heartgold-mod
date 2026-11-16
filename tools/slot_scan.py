# Research-only: find species obtainable in Origin HeartGold (reads rom/ohg.nds, never writes it).
# python tools/slot_scan.py  -> writes slot/obtainable.json and slot/unobtainable.txt
import sys, os, struct, pickle, json
sys.path.insert(0, os.path.dirname(__file__))
from lugia_common import Rom, ROOT
from scr import disasm, C
from collections import defaultdict

NSPEC = 1441; NAT = 1025
r = Rom()
msgs = pickle.load(open(os.path.join(ROOT, 'rom', 'msgs.pkl'), 'rb'))
NAMES = msgs[232]
def nm(s): return NAMES[s] if s < len(NAMES) else '#%d' % s
src = defaultdict(set)          # species -> set of source strings
def add(s, why):
    if 0 < s < NSPEC: src[s].add(why)

# 1. wild encounters a/0/3/7 (196 bytes, HGSS layout)
for i, d in enumerate(r.narc('a/0/3/7')):
    w = struct.unpack_from('<88H', d, 20)
    for k in range(36): add(w[k], 'wild%d:%s' % (i, ('morn', 'day', 'night')[k // 12]))
    for k in range(36, 40): add(w[k], 'wild%d:radio' % i)
    for blk, (a, n) in {'surf': (40, 5), 'smash': (50, 2), 'old': (54, 5), 'good': (64, 5), 'super': (74, 5)}.items():
        for j in range(n): add(w[a + 2*j + 1], 'wild%d:%s' % (i, blk))
    for k in range(84, 88): add(w[k], 'wild%d:swarm' % i)
# 2. safari a/2/3/0: 8-byte header then 4-byte (species u16, level u8, x) slots; keep plausible ones
for i, d in enumerate(r.narc('a/2/3/0')):
    for o in range(8, len(d) - 3, 4):
        s, lv, z = struct.unpack_from('<HBB', d, o)
        if 0 < s <= NAT and 1 <= lv <= 100: add(s, 'safari%d' % i)
# 3. headbutt a/2/5/2: u16 n, u16 nspecial, 18 x (u16 species, u8 min, u8 max)
for i, d in enumerate(r.narc('a/2/5/2')):
    if len(d) < 4 + 72: continue
    for j in range(18): add(struct.unpack_from('<H', d, 4 + 4*j)[0], 'headbutt%d' % i)
# 4. bug contest
mu = r.get(r.files['data/mushi/mushi_encount.bin'])
for o in range(0, len(mu), 8): add(struct.unpack_from('<H', mu, o)[0], 'bugcontest')
# 5. in-game trades (offered species = u32 @0)
for i, d in enumerate(r.narc('a/1/1/2')): add(struct.unpack_from('<I', d, 0)[0], 'trade%d' % i)
# 6. scripts
OPN = {v[0]: k for k, v in C.items()}
scripts = pickle.load(open(os.path.join(ROOT, 'rom', 'scripts.pkl'), 'rb'))
SPECARG = {'GiveMon': 0, 'GiveEgg': 0, 'WildBattle': 0}
scriptuse = []
for f, d in enumerate(scripts):
    try: ent, ins = disasm(d)
    except Exception: continue
    setv = defaultdict(set)
    for pc, (op, a, n, t) in ins.items():
        name = C.get(op, ['?'])[0]
        if name in ('SetVar', 'SetOrCopyVar') and len(a) == 2: setv[a[0]].add(a[1])
    for pc, (op, a, n, t) in sorted(ins.items()):
        name = C.get(op, ['?'])[0]
        if name in SPECARG and a:
            s = a[0]
            if s >= 0x4000:
                for v in setv.get(s, ()):
                    add(v, 'script%d:%s(var)' % (f, name)); scriptuse.append((f, pc, name, 'var%X=%d' % (s, v), nm(v)))
            else:
                add(s, 'script%d:%s' % (f, name)); scriptuse.append((f, pc, name, s, nm(s)))
        elif name in ('GiveTogepiEgg', 'GiveSpikyEarPichu', 'CreateRoamer', 'GetFossilPokemon', 'LoadNPCTrade', 'MysteryGift'):
            scriptuse.append((f, pc, name, a, ''))
add(175, 'GiveTogepiEgg'); add(172, 'GiveSpikyEarPichu')

# 7. evolutions a/0/3/4: 10 x (u16 method, u16 param, u16 target)
evo = r.narc('a/0/3/4'); evo_to = defaultdict(set); evo_from = defaultdict(set)
for s, d in enumerate(evo):
    for j in range(10):
        m, p, t = struct.unpack_from('<3H', d, 6*j)
        if m and 0 < t < NSPEC: evo_to[s].add(t); evo_from[t].add(s)
# breeding root table (pms.narc: species -> egg species)
pms = r.get(r.files['poketool/personal/pms.narc'])
baby = [struct.unpack_from('<H', pms, 2*i)[0] for i in range(len(pms) // 2)]

direct = set(src)
obt = set(direct); changed = True
while changed:
    changed = False
    for s in list(obt):
        nxt = set(evo_to[s])
        if s < len(baby) and baby[s]: nxt.add(baby[s])           # breed down to baby
        for t in nxt:
            if t not in obt: obt.add(t); src[t].add('via %s' % nm(s)); changed = True
        # babies obtained by breeding can evolve again - covered by loop

# 8. trainers
td = r.narc('a/0/5/5'); tp = r.narc('a/0/5/6'); trainer = defaultdict(set); hiword = 0
for i, d in enumerate(td):
    n = d[3]
    for j in range(n):
        if 28*j + 10 > len(tp[i]): break
        v = struct.unpack_from("<H", tp[i], 28*j + 8)[0]   # trainer mon: u16 ability @4, level @6, species @8
        if v >= NSPEC: hiword += 1
        trainer[v & 0x7FF].add(i)

out = []
for s in range(1, NAT + 1):
    if s not in obt:
        out.append('%4d %-12s trainers=%d evo_from=%s evo_to=%s' % (s, nm(s), len(trainer[s]),
                   [nm(x) for x in evo_from[s]], [nm(x) for x in evo_to[s]]))
os.makedirs(os.path.join(ROOT, 'slot'), exist_ok=True)
open(os.path.join(ROOT, 'slot', 'unobtainable.txt'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
json.dump({nm(s) + '#%d' % s: sorted(src[s])[:12] for s in sorted(obt)}, open(os.path.join(ROOT, 'slot', 'obtainable.json'), 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
open(os.path.join(ROOT, 'slot', 'script_species.txt'), 'w', encoding='utf-8').write('\n'.join(map(str, scriptuse)) + '\n')
print('direct', len(direct), 'obtainable', len(obt), 'unobtainable natdex', len(out), 'trainer hi-bit species', hiword)
print('\n'.join(out))
