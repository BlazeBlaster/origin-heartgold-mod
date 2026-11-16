import sys, os, struct, json, pickle
sys.path.insert(0, os.path.dirname(__file__))
from ohg import *
C = {int(k): v for k, v in json.load(open(os.path.join(ROOT, 'ref', 'ohgrepo', 'script_cmds.json'))).items()}
JUMPS = {'GoTo': 0, 'Call': 0, 'GoToIf': 1, 'CallIf': 1, 'ObjectGoTo': 1, 'BGGoTo': 1, 'DirectionGoTo': 1, 'GoToIfTrainerDefeated': 0}
def entries(d):
    ent = []; o = 0
    while o+4 <= len(d):
        if struct.unpack_from('<H', d, o)[0] == 0xFD13: break
        v = struct.unpack_from('<i', d, o)[0]; ent.append(o+4+v); o += 4
    return ent, o+2
def disasm(d):
    ent, start = entries(d)
    todo = list(ent); ins = {}
    while todo:
        pc = todo.pop()
        while pc not in ins and pc+2 <= len(d):
            op = struct.unpack_from('<H', d, pc)[0]
            if op not in C: ins[pc] = (op, ['??'], 2, None); break
            name, sizes = C[op]; p = pc+2; args = []
            for sz in sizes:
                if p+sz > len(d): break
                args.append(int.from_bytes(d[p:p+sz], 'little', signed=(sz == 4))); p += sz
            t = None
            if name in JUMPS and len(args) > JUMPS[name]:
                t = p + args[JUMPS[name]]; todo.append(t)
            ins[pc] = (op, args, p-pc, t)
            if name in ('End', 'GoTo', 'Return', 'RestartCurrentScript'): break
            pc = p
    return ent, ins
if __name__ == '__main__':
    rom, h = load(sys.argv[1]); files = fnt_files(rom, h)
    scr, _ = narc_parse(fat(rom, h, files['a/0/1/2']))
    pickle.dump(scr, open(os.path.join(ROOT, 'rom', 'scripts.pkl'), 'wb'))
    print('scripts', len(scr))
    for f, d in enumerate(scr):
        try: ent, ins = disasm(d)
        except Exception as e: continue
        for pc, (op, a, n, t) in sorted(ins.items()):
            if C.get(op, [''])[0] == 'GiveMon':
                print(f, pc, a)

# Mod: ScrCmd 62 (unused by every script in the ROM) is replaced by our multiplexed command.
# Bytes: u16 opcode 62, u16 subcommand, then 6 u16 args (each a literal or a var 0x4000+).
#   sub 0 GiveMonEx(species, level, nature 0-24 or 0xFFFF random, flags bit0 shiny bit1 IVs31, ability slot 0/1/2 or 0xFFFF, result var)
#   sub 1 SetPartyMonAbility(party slot, ability id, 0, 0, 0, 0)
C[62] = ['ModCmd', [2, 2, 2, 2, 2, 2, 2]]
