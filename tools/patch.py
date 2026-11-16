# Builds the modded Origin HeartGold ROM.  python tools/patch.py <in.nds> <out.nds>
#
# Layout: a shared build context (Ctx) plus one module per area. Each module has apply(ctx).
#   mod_code.py    - ARM9 / overlay code: GiveMon shiny hook, ModCmd (script cmd 62), egg icon,
#                    battle ability lists (Azure Skin rain, Solar Flare, Aura Guardian), ability texts.
#   mod_species.py - species/move data: Shadow Lugia in slot 717, ability slots, learnsets,
#                    move data, wild encounters, sprites, cries, Pokedex.
#   mod_story.py   - scripts, map objects and dialogue: starters, gifts, quests.
#   mod_trainers.py - boss trainers: max IVs, fitting natures, smarter AI.
# Modules only touch ROM data through ctx so they never clobber each other's edits.
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
from ohg import *
from nds import overlays
from scr import disasm, C

OP = {v[0]: int(k) for k, v in C.items()}

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
        self.ovl = {o['id']: o for o in overlays(bytes(self.b), self.h)}
    def span(self, fid):
        return struct.unpack_from('<II', self.b, self.h['fat_off'] + fid*8)
    def get(self, fid):
        s, e = self.span(fid); return bytes(self.b[s:e])
    def put(self, fid, data):
        fo = self.h['fat_off'] + fid*8
        s, e = struct.unpack_from('<II', self.b, fo)
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
    def finish(self, path):
        cap = 0x20000 << self.b[0x14]
        while cap < len(self.b): self.b[0x14] += 1; cap <<= 1
        struct.pack_into('<H', self.b, 0x15E, crc16(self.b[:0x15E]))
        open(path, 'wb').write(self.b)

# ---------------- script helpers ----------------
class Script:
    def __init__(self, data, fid, log):
        self.d = bytearray(data); self.fid = fid; self.log = log
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
        self.log.append('script %d @%d %s arg%d %s -> %s' % (self.fid, pc, name, argi, a[argi], value))
    def replace_buffer_with_setvar(self, pc, var, value):
        op, a = self.at(pc, 'BufferSpeciesName')            # 8 bytes -> SetVar (6) + Noop (2)
        self.d[pc:pc+8] = struct.pack('<HHHH', OP['SetVar'], var, value, OP['Noop'])
        self.log.append('script %d @%d BufferSpeciesName%s -> SetVar 0x%X=0x%X; Noop' % (self.fid, pc, a, var, value))
    def append_script(self, code_builder):
        """Add a new script entry at the end; returns its 1-based number."""
        n = len(self.ent); tbl = 4*n
        assert struct.unpack_from('<H', self.d, tbl)[0] == 0xFD13
        newtbl = bytearray()
        for i, e in enumerate(self.ent):
            newtbl += struct.pack('<i', (e + 4) - (4*i + 4))
        body = bytes(self.d[tbl + 2:])
        while (len(body) + 4*(n+1) + 2) % 2: body += b'\x00'
        new_start = 4*(n+1) + 2 + len(body)
        newtbl += struct.pack('<i', new_start - (4*n + 4))
        self.d = newtbl + struct.pack('<H', 0xFD13) + body + code_builder(new_start)
        self.ent, self.ins = disasm(bytes(self.d))
        return n + 1
    def append_code(self, code_builder):
        """Append code reachable only by jumps (no new table entry); returns its offset."""
        while len(self.d) % 2: self.d += b'\x00'
        base = len(self.d); self.d += code_builder(base)
        self.ent, self.ins = disasm(bytes(self.d))
        return base
    def goto_at(self, pc, length, target):
        """Overwrite `length` bytes at pc with GoTo target (+Noops). length >= 6."""
        assert length >= 6 and (length - 6) % 2 == 0
        self.d[pc:pc+length] = struct.pack('<Hi', OP['GoTo'], target - (pc + 6)) + struct.pack('<H', OP['Noop']) * ((length - 6)//2)
        self.ent, self.ins = disasm(bytes(self.d))

class Code:
    """Tiny script assembler with labels (jump offsets relative to end of instruction)."""
    JUMP_OPS = {'GoTo': 0, 'Call': 0}
    def __init__(self, base): self.base = base; self.items = []; self.labels = {}
    def _size(self, it): return len(it) if isinstance(it, bytes) else (7 if it[0] in ('GoToIf', 'CallIf') else 6)
    def pc(self): return self.base + sum(self._size(x) for x in self.items)
    def label(self, n): self.labels[n] = self.pc()
    def op(self, name, *args):
        sizes = C[OP[name]][1]; assert len(sizes) == len(args), (name, sizes, args)
        self.items.append(struct.pack('<H', OP[name]) + b''.join(int(v).to_bytes(s, 'little', signed=(v < 0)) for v, s in zip(args, sizes)))
    def goto_if(self, cond, label): self.items.append(('GoToIf', cond, label))
    def call_if(self, cond, label): self.items.append(('CallIf', cond, label))
    def goto(self, label): self.items.append(('GoTo', label))
    def call(self, label): self.items.append(('Call', label))
    def goto_abs(self, target): self.items.append(('GoToAbs', target))
    def raw(self, b): self.items.append(bytes(b))
    def build(self):
        out = bytearray(); pc = self.base
        for it in self.items:
            if isinstance(it, bytes): out += it; pc += len(it); continue
            kind = it[0]
            if kind in ('GoToIf', 'CallIf'):
                out += struct.pack('<HBi', OP[kind], it[1], self.labels[it[2]] - (pc + 7)); pc += 7
            elif kind in ('GoTo', 'Call'):
                out += struct.pack('<Hi', OP[kind], self.labels[it[1]] - (pc + 6)); pc += 6
            elif kind == 'GoToAbs':
                out += struct.pack('<Hi', OP['GoTo'], it[1] - (pc + 6)); pc += 6
        return bytes(out)

def msg(code, idx):
    code.op('NPCMsg', idx); code.op('WaitButton'); code.op('CloseMsg')

# ---------------- build context ----------------
class Ctx:
    def __init__(self, rom):
        self.rom = rom; self.log = []
        self._narcs = {}; self._banks = {}; self._scripts = {}
        self.arm9_off, self.arm9_ram = rom.h['arm9_off'], rom.h['arm9_ram']
    # narcs (cached; written back in flush)
    def narc(self, name):
        if name not in self._narcs: self._narcs[name] = list(narc_parse(self.rom.get(self.rom.files[name])))
        return self._narcs[name][0]
    # text
    def bank(self, b):
        if b not in self._banks:
            strs, seed = msg_decode(self.narc('a/0/2/7')[b]); self._banks[b] = ([chars_to_str(c) for c in strs], seed)
        return self._banks[b][0]
    def add_text(self, b, s):
        self.bank(b).append(s); return len(self.bank(b)) - 1
    def edit_text(self, b, i, old, new):
        s = self.bank(b)[i]; assert old in s, (b, i, old, s)
        self.bank(b)[i] = s.replace(old, new); self.log.append('text %d.%d edited' % (b, i))
    def set_text(self, b, i, new):
        self.bank(b)[i] = new; self.log.append('text %d.%d replaced' % (b, i))
    # scripts
    def script(self, f):
        if f not in self._scripts: self._scripts[f] = Script(self.narc('a/0/1/2')[f], f, self.log)
        return self._scripts[f]
    # code
    def _ov_off(self, n, addr, size):
        o = self.rom.ovl[n]; assert o['flag'] & 1 == 0, 'overlay %d is compressed' % n
        assert o['ram'] <= addr and addr + size <= o['ram'] + o['size'], (n, hex(addr))
        return self.rom.span(o['fid'])[0] + addr - o['ram']
    def arm9_read(self, addr, n):
        o = self.arm9_off + addr - self.arm9_ram; return bytes(self.rom.b[o:o+n])
    def arm9_write(self, addr, data, expect=None):
        o = self.arm9_off + addr - self.arm9_ram
        if expect is not None: assert bytes(self.rom.b[o:o+len(expect)]) == expect, ('arm9', hex(addr), self.rom.b[o:o+len(expect)].hex())
        self.rom.b[o:o+len(data)] = data; self.log.append('arm9 0x%X: %d bytes' % (addr, len(data)))
    def ov_read(self, n, addr, size):
        o = self._ov_off(n, addr, size); return bytes(self.rom.b[o:o+size])
    def ov_write(self, n, addr, data, expect=None):
        o = self._ov_off(n, addr, len(data))
        if expect is not None: assert bytes(self.rom.b[o:o+len(expect)]) == expect, ('ov%d' % n, hex(addr), self.rom.b[o:o+len(expect)].hex())
        self.rom.b[o:o+len(data)] = data; self.log.append('ov%d 0x%X: %d bytes' % (n, addr, len(data)))
    # write everything back
    def flush(self):
        if self._banks:
            mn = self.narc('a/0/2/7')
            for b, (strs, seed) in self._banks.items():
                mn[b] = msg_encode([str_to_chars(s) for s in strs], seed)
                back, _ = msg_decode(mn[b]); assert [chars_to_str(c) for c in back] == strs, b
        if self._scripts:
            sn = self.narc('a/0/1/2')
            for f, s in self._scripts.items(): sn[f] = bytes(s.d)
        for name, (ents, btnf) in self._narcs.items():
            self.rom.put(self.rom.files[name], narc_build(ents, btnf))

def main(src, dst, only=None):
    import mod_code, mod_species, mod_story, mod_trainers
    ctx = Ctx(Rom(src))
    for m in (mod_code, mod_species, mod_story, mod_trainers):
        if only and m.__name__ not in only: continue
        m.apply(ctx)
    ctx.flush()
    ctx.rom.finish(dst)
    print('\n'.join(ctx.log))

if __name__ == '__main__':
    # optional 3rd arg: comma-separated module names to apply (e.g. mod_species) for testing one area
    main(sys.argv[1], sys.argv[2], sys.argv[3].split(',') if len(sys.argv) > 3 else None)
