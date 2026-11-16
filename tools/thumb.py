# Minimal Thumb (ARMv5) assembler for the handful of forms the patch needs.
import struct

def R(r): return int(r[1:])

class Asm:
    def __init__(self, base):
        self.base = base; self.items = []; self.labels = {}
    def pc(self): return self.base + sum(4 if i[0] in ('bl', 'w32') else 2 for i in self.items)
    def label(self, name): self.labels[name] = self.pc()
    def h(self, v): self.items.append(('h', v & 0xFFFF))
    def bl(self, target): self.items.append(('bl', target))
    def bcond(self, cond, label): self.items.append(('b', cond, label))
    # encoders
    def push_r4_r7_lr(self): self.h(0xB5F0)
    def pop_r4_r7_pc(self): self.h(0xBDF0)
    def sub_sp(self, imm): assert imm % 4 == 0 and imm < 512; self.h(0xB080 | imm//4)
    def add_sp(self, imm): assert imm % 4 == 0 and imm < 512; self.h(0xB000 | imm//4)
    def adds3(self, rd, rn, imm): assert imm < 8; self.h(0x1C00 | imm << 6 | R(rn) << 3 | R(rd))
    def mov(self, rd, rn): self.adds3(rd, rn, 0)
    def adds8(self, rd, imm): assert imm < 256; self.h(0x3000 | R(rd) << 8 | imm)
    def movs(self, rd, imm): assert imm < 256; self.h(0x2000 | R(rd) << 8 | imm)
    def cmp(self, rn, imm): assert imm < 256; self.h(0x2800 | R(rn) << 8 | imm)
    def ldr(self, rd, rn, imm): assert imm % 4 == 0 and imm < 128; self.h(0x6800 | (imm//4) << 6 | R(rn) << 3 | R(rd))
    def str_(self, rd, rn, imm): assert imm % 4 == 0 and imm < 128; self.h(0x6000 | (imm//4) << 6 | R(rn) << 3 | R(rd))
    def strh(self, rd, rn, imm): assert imm % 2 == 0 and imm < 64; self.h(0x8000 | (imm//2) << 6 | R(rn) << 3 | R(rd))
    def ldr_sp(self, rd, imm): assert imm % 4 == 0 and imm < 1024; self.h(0x9800 | R(rd) << 8 | imm//4)
    def str_sp(self, rd, imm): assert imm % 4 == 0 and imm < 1024; self.h(0x9000 | R(rd) << 8 | imm//4)
    def add_rd_sp(self, rd, imm): assert imm % 4 == 0 and imm < 1024; self.h(0xA800 | R(rd) << 8 | imm//4)
    def lsls(self, rd, rm, imm): assert 0 <= imm < 32; self.h(0x0000 | imm << 6 | R(rm) << 3 | R(rd))
    def lsrs(self, rd, rm, imm): assert 0 < imm < 32; self.h(0x0800 | imm << 6 | R(rm) << 3 | R(rd))
    def str_reg(self, rd, rn, rm): self.h(0x5000 | R(rm) << 6 | R(rn) << 3 | R(rd))
    def nop(self): self.h(0x46C0)
    def assemble(self):
        out = bytearray(); pc = self.base
        for it in self.items:
            if it[0] == 'h': out += struct.pack('<H', it[1]); pc += 2
            elif it[0] == 'bl':
                off = it[1] - (pc + 4); assert -(1 << 22) <= off < (1 << 22) and off % 2 == 0
                off = (off >> 1) & 0x3FFFFF
                out += struct.pack('<HH', 0xF000 | (off >> 11), 0xF800 | (off & 0x7FF)); pc += 4
            elif it[0] == 'b' and it[1] == 'al':
                off = self.labels[it[2]] - (pc + 4); assert -2048 <= off < 2048 and off % 2 == 0
                out += struct.pack('<H', 0xE000 | ((off >> 1) & 0x7FF)); pc += 2
            elif it[0] == 'b':
                conds = {'eq': 0, 'ne': 1, 'hs': 2, 'lo': 3, 'mi': 4, 'pl': 5, 'hi': 8, 'ls': 9, 'ge': 0xA, 'lt': 0xB}
                off = self.labels[it[2]] - (pc + 4); assert -256 <= off < 256 and off % 2 == 0
                out += struct.pack('<H', 0xD000 | conds[it[1]] << 8 | ((off >> 1) & 0xFF)); pc += 2
        return bytes(out)
