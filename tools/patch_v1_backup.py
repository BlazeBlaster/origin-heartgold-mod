# Builds the modded Origin HeartGold ROM.  python tools/patch.py <in.nds> <out.nds>
import sys, os, struct, pickle
sys.path.insert(0, os.path.dirname(__file__))
from ohg import *
from scr import disasm, C
import codepatch, texts

SHINY_OBJ_ID = 0xF3     # object IDs 0xF0-0xF5 are drawn with the shiny palette when param[2] bit 0 is set
F_ASKED, F_APPROVED, F_EGG = 2600, 2601, 2602   # unused event flags for the Ranger quest
VAR_SHINY = 0x8008
OP = {v[0]: int(k) for k, v in C.items()}
log = []

def crc16(data):
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc

class Rom:
    def __init__(self, path):
        self.b = bytearray(open(path, 'rb').read())
        _, self.h = load(path)
        self.files = fnt_files(bytes(self.b), self.h)
    def get(self, fid):
        s, e = struct.unpack_from('<II', self.b, self.h['fat_off'] + fid*8); return bytes(self.b[s:e])
    def put(self, fid, data):
        fo = self.h['fat_off'] + fid*8
        s, e = struct.unpack_from('<II', self.b, fo)
        # room up to the next file start
        starts = sorted(struct.unpack_from('<I', self.b, self.h['fat_off'] + i*8)[0] for i in range(self.h['fat_size']//8))
        nxt = next((x for x in starts if x > s), len(self.b))
        if len(data) <= nxt - s:
            self.b[s:s+len(data)] = data; self.b[s+len(data):nxt] = b'\xff' * (nxt - s - len(data))
            struct.pack_into('<II', self.b, fo, s, s+len(data))
        else:
            used = struct.unpack_from('<I', self.b, 0x80)[0]
            end = max(used, max(struct.unpack_from('<I', self.b, self.h['fat_off'] + i*8 + 4)[0] for i in range(self.h['fat_size']//8)))
            ns = (end + 0x1FF) & ~0x1FF
            if ns + len(data) > len(self.b): self.b += b'\xff' * (ns + len(data) - len(self.b))
            self.b[ns:ns+len(data)] = data
            struct.pack_into('<II', self.b, fo, ns, ns+len(data))
            self.b[s:e] = b'\xff' * (e - s)
            struct.pack_into('<I', self.b, 0x80, ns + len(data))
    def narc(self, name):
        ents, btnf = narc_parse(self.get(self.files[name])); return list(ents), btnf
    def put_narc(self, name, ents, btnf):
        self.put(self.files[name], narc_build(ents, btnf))
    def finish(self, path):
        used = struct.unpack_from('<I', self.b, 0x80)[0]
        cap = 0x20000 << self.b[0x14]
        while cap < len(self.b): self.b[0x14] += 1; cap <<= 1
        struct.pack_into('<H', self.b, 0x15E, crc16(self.b[:0x15E]))
        open(path, 'wb').write(self.b)

# ---------------- script helpers ----------------
class Script:
    def __init__(self, data, fid):
        self.d = bytearray(data); self.fid = fid
        self.ent, self.ins = disasm(bytes(data))
    def at(self, pc, name):
        op, a, n, t = self.ins[pc]
        assert C[op][0] == name, (self.fid, pc, C[op][0], name)
        return op, a
    def set_arg(self, pc, name, argi, value, expect=None):
        op, a = self.at(pc, name)
        sizes = C[op][1]; off = pc + 2 + sum(sizes[:argi])
        if expect is not None: assert a[argi] == expect, (self.fid, pc, a, expect)
        self.d[off:off+sizes[argi]] = value.to_bytes(sizes[argi], 'little')
        log.append('script %d @%d %s arg%d %s -> %s' % (self.fid, pc, name, argi, a[argi], value))
    def replace_buffer_with_setvar(self, pc, var, value):
        op, a = self.at(pc, 'BufferSpeciesName')            # 8 bytes -> SetVar (6) + Noop (2)
        self.d[pc:pc+8] = struct.pack('<HHHH', OP['SetVar'], var, value, OP['Noop'])
        log.append('script %d @%d BufferSpeciesName%s -> SetVar 0x%X=0x%X; Noop' % (self.fid, pc, a, var, value))
    def append_script(self, code_builder):
        """Add a new script entry at the end; returns its 1-based number."""
        n = len(self.ent)
        tbl = 4*n
        assert struct.unpack_from('<H', self.d, tbl)[0] == 0xFD13
        old_code_start = tbl + 2
        # every existing entry gains 4 bytes of table before its target
        newtbl = bytearray()
        for i, e in enumerate(self.ent):
            newtbl += struct.pack('<i', (e + 4) - (4*i + 4))
        body = bytes(self.d[old_code_start:])
        while (len(body) + 4*(n+1) + 2) % 2: body += b'\x00'
        new_start = 4*(n+1) + 2 + len(body)
        newtbl += struct.pack('<i', new_start - (4*n + 4))
        self.d = newtbl + struct.pack('<H', 0xFD13) + body + code_builder(new_start)
        self.ent, self.ins = disasm(bytes(self.d))
        return n + 1

class Code:
    """Tiny script assembler with labels (jump offsets relative to end of instruction)."""
    def __init__(self, base): self.base = base; self.items = []; self.labels = {}
    def label(self, n): self.labels[n] = self.base + sum(len(x) if isinstance(x, bytes) else 6 for x in self.items)
    def op(self, name, *args):
        sizes = C[OP[name]][1]; assert len(sizes) == len(args), name
        self.items.append(struct.pack('<H', OP[name]) + b''.join(int(v).to_bytes(s, 'little', signed=(s == 4 and v < 0)) for v, s in zip(args, sizes)))
    def goto_if(self, cond, label): self.items.append(('GoToIf', cond, label))
    def build(self):
        out = bytearray(); pc = self.base
        for it in self.items:
            if isinstance(it, bytes): out += it; pc += len(it)
            else:
                _, cond, lab = it
                out += struct.pack('<HBi', OP['GoToIf'], cond, self.labels[lab] - (pc + 7)); pc += 7
        return bytes(out)
    # GoToIf is 7 bytes (2 + 1 + 4); fix label math
    def label(self, n):
        self.labels[n] = self.base + sum(len(x) if isinstance(x, bytes) else 7 for x in self.items)

def msg(code, idx):
    code.op('NPCMsg', idx); code.op('WaitButton'); code.op('CloseMsg')

def main(src, dst):
    rom = Rom(src)
    arm9_off, ram = rom.h['arm9_off'], rom.h['arm9_ram']
    # ---------- ARM9 code ----------
    for addr, exp in codepatch.EXPECT.items():
        assert rom.b[arm9_off+addr-ram:arm9_off+addr-ram+len(exp)] == exp, hex(addr)
    orig_scr = bytes(rom.b[arm9_off+codepatch.SCRCMD_GIVEMON-ram:arm9_off+codepatch.SCRCMD_GIVEMON-ram+4])
    assert orig_scr == bytes.fromhex('f0b589b0'), orig_scr.hex()
    patches, _ = codepatch.build()
    for addr, code in patches:
        o = arm9_off + addr - ram; rom.b[o:o+len(code)] = code
        log.append('arm9 0x%X: %d bytes' % (addr, len(code)))

    # ---------- text ----------
    mn, mbtnf = rom.narc('a/0/2/7')
    banks = {}
    def bank(b):
        if b not in banks:
            strs, seed = msg_decode(mn[b]); banks[b] = ([chars_to_str(c) for c in strs], seed)
        return banks[b][0]
    for b, i, old, new in texts.EDITS:
        s = bank(b)[i]; assert old in s, (b, i, old, s)
        bank(b)[i] = s.replace(old, new); log.append('text %d.%d edited' % (b, i))
    mira = {}
    for k, v in texts.MIRA.items(): bank(439).append(v); mira[k] = len(bank(439)) - 1
    theo = {}
    for k, v in texts.THEO.items(): bank(445).append(v); theo[k] = len(bank(445)) - 1
    assert max(theo.values()) < 256 and max(mira.values()) < 256
    for b, (strs, seed) in banks.items():
        mn[b] = msg_encode([str_to_chars(s) for s in strs], seed)
        # round-trip check
        back, _ = msg_decode(mn[b]); assert [chars_to_str(c) for c in back] == strs, b
    rom.put_narc('a/0/2/7', mn, mbtnf)

    # ---------- scripts ----------
    sn, sbtnf = rom.narc('a/0/1/2')
    S = {f: Script(sn[f], f) for f in (738, 733, 751, 183, 179, 170, 739)}
    s = S[738]   # Oak's lab: Pikachu ball -> Latios
    for pc in (2018, 2079): s.set_arg(pc, 'ScrCmd_452', 0, 381, 25)
    for pc in (2024, 2085): s.set_arg(pc, 'PlayCry', 0, 381, 25)
    for pc in (2057, 2118): s.set_arg(pc, 'SetVar', 1, 381, 25)
    for pc in (3876, 4230): s.set_arg(pc, 'CompareVarToValue', 1, 381, 25)
    S[733].set_arg(1086, 'SetVar', 1, 225, 236)            # Light Ball -> Soul Dew
    s = S[751]   # Pewter PC: shiny Charmander
    s.replace_buffer_with_setvar(514, VAR_SHINY, 0x8000 | 4)
    s.set_arg(522, 'GiveMon', 0, VAR_SHINY, 4)
    s.set_arg(501, 'HidePerson', 0, SHINY_OBJ_ID, 13)
    s = S[183]   # Route 5 house: shiny Darkrai
    s.set_arg(149, 'PlayCry', 0, 491, 1)
    s.set_arg(240, 'BufferSpeciesName', 1, 491, 1)
    s.replace_buffer_with_setvar(260, VAR_SHINY, 0x8000 | 491)
    s.set_arg(268, 'GiveMon', 0, VAR_SHINY, 1)
    s.set_arg(236, 'HidePerson', 0, SHINY_OBJ_ID, 7)
    s = S[179]   # Route 5 raid scene
    for pc in (322, 1057, 1315, 1351): s.set_arg(pc, 'PlayCry', 0, 491, 1)
    for pc in (1047, 1080, 1134, 1329, 1341, 2368, 2411): s.set_arg(pc, 'ApplyMovement', 0, SHINY_OBJ_ID, 0)
    for pc in (1405, 2480): s.set_arg(pc, 'HidePerson', 0, SHINY_OBJ_ID, 0)
    s = S[170]   # Route 2 roadside Charmander
    for pc in (829, 845, 901, 966, 1960, 1976, 2032, 2097, 2123, 2139, 2195, 2260):
        s.set_arg(pc, 'ApplyMovement', 0, SHINY_OBJ_ID, 3)

    # Ranger Mira (Pallet Town)
    def mira_code(base):
        c = Code(base)
        c.op('PlaySE', 1500); c.op('LockAll'); c.op('FacePlayer'); c.op('BufferPlayersName', 0)
        c.op('CheckFlag', F_EGG); c.goto_if(1, 'done')
        c.op('CheckFlag', F_APPROVED); c.goto_if(1, 'give')
        c.op('CheckFlag', F_ASKED); c.goto_if(1, 'remind')
        c.op('CheckFlag', 106); c.goto_if(0, 'nostarter')
        msg(c, mira['intro']); c.op('SetFlag', F_ASKED); c.op('ReleaseAll'); c.op('End')
        c.label('remind'); msg(c, mira['remind']); c.op('ReleaseAll'); c.op('End')
        c.label('nostarter'); msg(c, mira['nostarter']); c.op('ReleaseAll'); c.op('End')
        c.label('give')
        c.op('GetPartyCount', 0x8005); c.op('CompareVarToValue', 0x8005, 6); c.goto_if(1, 'full')
        msg(c, mira['give'])
        c.op('GiveEgg', 490, 14); c.op('SetFlag', F_EGG)
        c.op('NPCMsg', mira['received']); c.op('PlayFanfare', 1200); c.op('WaitFanfare'); c.op('WaitButton'); c.op('CloseMsg')
        msg(c, mira['after']); c.op('ReleaseAll'); c.op('End')
        c.label('full'); msg(c, mira['full']); c.op('ReleaseAll'); c.op('End')
        c.label('done'); msg(c, mira['done']); c.op('ReleaseAll'); c.op('End')
        return c.build()
    def theo_code(base):
        c = Code(base)
        c.op('PlaySE', 1500); c.op('LockAll'); c.op('FacePlayer'); c.op('BufferPlayersName', 0)
        c.op('CheckFlag', F_EGG); c.goto_if(1, 'done')
        c.op('CheckFlag', F_APPROVED); c.goto_if(1, 'waiting')
        c.op('CheckFlag', F_ASKED); c.goto_if(0, 'idle')
        msg(c, theo['report']); c.op('SetFlag', F_APPROVED); c.op('ReleaseAll'); c.op('End')
        c.label('waiting'); msg(c, theo['waiting']); c.op('ReleaseAll'); c.op('End')
        c.label('idle'); msg(c, theo['idle']); c.op('ReleaseAll'); c.op('End')
        c.label('done'); msg(c, theo['done']); c.op('ReleaseAll'); c.op('End')
        return c.build()
    mira_scr = S[733].append_script(mira_code)
    theo_scr = S[739].append_script(theo_code)
    log.append('new scripts: Mira = Pallet script %d, Theo = Viridian script %d' % (mira_scr, theo_scr))
    for f, s in S.items(): sn[f] = bytes(s.d)
    rom.put_narc('a/0/1/2', sn, sbtnf)

    # ---------- map objects ----------
    en, ebtnf = rom.narc('a/0/3/2')
    def objs_off(d):
        nbg = struct.unpack_from('<I', d, 0)[0]; o = 4 + nbg*20
        return o, struct.unpack_from('<I', d, o)[0]
    def edit_obj(eb, oid, sprite=None, newid=None, shiny=False):
        d = bytearray(en[eb]); o, n = objs_off(d)
        for i in range(n):
            p = o + 4 + i*32
            if struct.unpack_from('<H', d, p)[0] == oid:
                if sprite is not None: struct.pack_into('<H', d, p+2, sprite)
                if newid is not None: struct.pack_into('<H', d, p, newid)
                if shiny: struct.pack_into('<H', d, p+18, struct.unpack_from('<H', d, p+18)[0] | 1)
                en[eb] = bytes(d); log.append('event %d obj %d -> sprite %s id %s shiny %s' % (eb, oid, sprite, newid, shiny)); return
        raise KeyError((eb, oid))
    edit_obj(370, 3, newid=SHINY_OBJ_ID, shiny=True)                 # Route 2 Charmander
    edit_obj(428, 13, newid=SHINY_OBJ_ID, shiny=True)                # Pewter PC Charmander
    edit_obj(10, 0, sprite=973, newid=SHINY_OBJ_ID, shiny=True)      # Route 5 raid: Darkrai
    edit_obj(469, 7, sprite=973, newid=SHINY_OBJ_ID, shiny=True)     # Route 5 house: Darkrai
    def add_obj(eb, sprite, script, x, z, copy_y_from):
        d = bytearray(en[eb]); o, n = objs_off(d)
        ids = [struct.unpack_from('<H', d, o+4+i*32)[0] for i in range(n)]
        y = None
        for i in range(n):
            if ids[i] == copy_y_from: y = struct.unpack_from('<i', d, o+4+i*32+28)[0]
        newid = max(i for i in ids if i < 0xF0) + 1
        rec = struct.pack('<HHHHHHhHHHhhHHi', newid, sprite, 15, 0, 0, script, 0, 0, 0, 0, 0, 0, x, z, y)
        assert len(rec) == 32
        p = o + 4 + n*32
        d[o:o+4] = struct.pack('<I', n+1); d[p:p] = rec
        en[eb] = bytes(d); log.append('event %d: new object id %d sprite %d script %d at (%d,%d)' % (eb, newid, sprite, script, x, z))
    add_obj(46, 69, mira_scr, 1032, 379, copy_y_from=6)       # Pallet shore, beside the water
    add_obj(47, 345, theo_scr, 1050, 258, copy_y_from=18)     # east Viridian
    rom.put_narc('a/0/3/2', en, ebtnf)

    # ---------- Manaphy egg icon ----------
    old, _ = rom.narc('a/0/2/0')
    icons, ibtnf = rom.narc('data/pokeicon.narc')
    assert len(icons) == 0xB4A
    icons.append(old[502]); rom.put_narc('data/pokeicon.narc', icons, ibtnf)
    log.append('icon 0xB4A = original Manaphy Egg icon')

    rom.finish(dst)
    print('\n'.join(log))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
