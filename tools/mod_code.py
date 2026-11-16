# ARM9 / overlay code changes. See patch.py for the ctx API.
#   - GiveMon shiny hook + Manaphy egg icon (codepatch.py)
#   - ModCmd = script command 62 (GiveMonEx / SetPartyMonAbility), arm9 cave 0x2040914 (see MODCMD.md)
#   - Battle abilities (ov14): Solar Flare (253), Aura Guardian (306), Azure Skin (318) + rain
#   - Vacuum Wave power 40 -> 60; ability names/descriptions
import struct
import codepatch
from thumb import Asm, R

# ---------------------------------------------------------------- assembler helpers
class A(Asm):
    CONDS = {'eq': 0, 'ne': 1, 'cs': 2, 'cc': 3, 'mi': 4, 'pl': 5, 'hi': 8, 'ls': 9,
             'ge': 0xA, 'lt': 0xB, 'gt': 0xC, 'le': 0xD}
    def push_r4_lr(self): self.h(0xB510)
    def pop_r4_pc(self): self.h(0xBD10)
    def bx_lr(self): self.h(0x4770)
    def cmpr(self, rn, rm): self.h(0x4280 | R(rm) << 3 | R(rn))
    def addr(self, rd, rn, rm): self.h(0x1800 | R(rm) << 6 | R(rn) << 3 | R(rd))
    def muls(self, rd, rm): self.h(0x4340 | R(rm) << 3 | R(rd))           # rd = rd * rm
    def ldrh(self, rd, rn, imm): assert imm % 2 == 0 and imm < 64; self.h(0x8800 | (imm//2) << 6 | R(rn) << 3 | R(rd))
    def b(self, label): self.items.append(('b', 'al', label))
    def adr(self, rd, label): self.items.append(('adr', rd, label))      # add rd, pc, #imm
    def ldrl(self, rd, label): self.items.append(('ldrl', rd, label))    # ldr rd, [pc, #imm]
    def w32(self, v): self.items.append(('w32', v))
    def hw(self, v): self.h(v)
    def align4(self):
        if self.pc() % 4: self.h(0)
    def assemble(self):
        out = bytearray(); pc = self.base
        for it in self.items:
            k = it[0]
            if k == 'h': out += struct.pack('<H', it[1]); pc += 2
            elif k == 'w32': out += struct.pack('<I', it[1]); pc += 4
            elif k == 'bl':
                off = it[1] - (pc + 4); assert -(1 << 22) <= off < (1 << 22) and off % 2 == 0
                off = (off >> 1) & 0x3FFFFF
                out += struct.pack('<HH', 0xF000 | (off >> 11), 0xF800 | (off & 0x7FF)); pc += 4
            elif k == 'b':
                off = self.labels[it[2]] - (pc + 4); assert off % 2 == 0
                if it[1] == 'al':
                    assert -2048 <= off < 2048; out += struct.pack('<H', 0xE000 | ((off >> 1) & 0x7FF))
                else:
                    assert -256 <= off < 256; out += struct.pack('<H', 0xD000 | self.CONDS[it[1]] << 8 | ((off >> 1) & 0xFF))
                pc += 2
            elif k in ('adr', 'ldrl'):
                off = self.labels[it[2]] - ((pc + 4) & ~3); assert 0 <= off < 1024 and off % 4 == 0, (k, it, off)
                out += struct.pack('<H', (0xA000 if k == 'adr' else 0x4800) | R(it[1]) << 8 | off // 4); pc += 2
            else: raise ValueError(it)
        return bytes(out)

# ---------------------------------------------------------------- ModCmd (script command 62)
SCRCMD_TABLE   = 0x020F793C     # entry 137 = ScrCmd_GiveMon 0x0204C595
MODCMD         = 0x02040914     # old (dead) ScrCmd_062 + its callback; free up to 0x02040A64
MODCMD_END     = 0x02040A64
SCRIPT_READ_HW = codepatch.SCRIPT_READ_HW    # u16 ScriptReadHalfword(ctx)
SCRIPT_GET_VAR = codepatch.SCRIPT_GET_VAR    # u16 VarGet(fieldSys, v): literal if v < 0x4000
SCRIPT_GET_VPTR = codepatch.SCRIPT_GET_VPTR  # u16 *GetVarPointer(fieldSys, v)
MAPSEC_OF_MAP  = codepatch.MAPSEC_OF_MAP
GET_PROFILE    = 0x0202933C     # PlayerProfile *(SaveData*)
GET_PARTY      = 0x0207365C     # Party *(SaveData*)     party: +0 max, +4 count, +8 mons (0xEC each)
ALLOC_MON      = 0x0206CFB4     # Pokemon *(heapId)
ZERO_MON       = 0x0206CF6C
CREATEMON      = codepatch.CREATEMON   # (mon, species, level, ivs (<32 = all IVs), [hasFixedPid, pid, otIdType, otId])
GET_TRAINER_ID = codepatch.GET_TRAINER_ID
GEN_SHINY_PID  = codepatch.GEN_SHINY_PID
SET_MET_DATA   = 0x020712E4     # (mon, profile, ball 4, mapsec, [encType, heapId])
SET_MON_DATA   = 0x0206DF70     # (mon, id, ptr)
SET_ABILITY    = 0x02071524     # recompute ability from fields 0xBC (slot 0/1) / 0x71 (hidden flag)
PERFECT_IVS    = 0x0206D4DC     # (mon, n): n random IVs -> 31, then recalc stats (GiveMon uses n=3)
PARTY_ADD      = 0x0207327C     # BOOL (party, mon)
DEX_REGISTER   = 0x0202EEE8     # (saveData, mon)
FREE           = 0x0201B33C
MON_ABILITY, MON_HIDDEN_AB, MON_AB_SLOT, MON_NATURE = 0x0A, 0x71, 0xBC, 0xBE

def build_modcmd():
    a = A(MODCMD)
    # stack: [sp..sp+0xC] callee args / temp, sp+0x10 sub, sp+0x14..0x28 args 0..5
    a.push_r4_r7_lr(); a.sub_sp(0x30)
    a.mov('r4', 'r0')                                   # ctx
    a.adds8('r0', 0x80); a.ldr('r5', 'r0', 0)           # fieldSystem
    a.movs('r6', 0); a.add_rd_sp('r7', 0x10)
    a.label('rd')
    a.mov('r0', 'r4'); a.bl(SCRIPT_READ_HW)
    a.adds3('r1', 'r0', 1); a.lsrs('r1', 'r1', 16); a.bcond('ne', 'raw')   # 0xFFFF stays literal
    a.cmp('r6', 6); a.bcond('eq', 'raw')                                # arg 5 (result var) stays raw
    a.mov('r1', 'r0'); a.mov('r0', 'r5'); a.bl(SCRIPT_GET_VAR)
    a.label('raw')
    a.lsls('r1', 'r6', 2); a.str_reg('r0', 'r7', 'r1')
    a.adds8('r6', 1); a.cmp('r6', 7); a.bcond('lt', 'rd')
    a.ldr('r0', 'r5', 0xC); a.bl(GET_PARTY); a.mov('r4', 'r0')          # r4 = party
    a.ldr_sp('r0', 0x10)
    a.cmp('r0', 1); a.bcond('eq', 'sub1')
    a.cmp('r0', 0); a.bcond('ne', 'done')
    # ---- sub 0: GiveMonEx(species, level, nature, flags, ability slot, result var)
    a.movs('r6', 0)
    a.ldr('r1', 'r4', 4); a.ldr('r0', 'r4', 0); a.cmpr('r1', 'r0'); a.bcond('ge', 'store')   # party full
    a.movs('r0', 0xB); a.bl(ALLOC_MON); a.mov('r7', 'r0'); a.bl(ZERO_MON)
    a.movs('r0', 0)
    for off in (0, 4, 8, 0xC): a.str_sp('r0', off)
    a.ldr_sp('r0', 0x20); a.lsrs('r0', 'r0', 1); a.bcond('cc', 'noshiny')     # flags bit0
    a.ldr('r0', 'r5', 0xC); a.bl(GET_PROFILE); a.bl(GET_TRAINER_ID)
    a.str_sp('r0', 0xC)                                  # fixedOtId = player's ID
    a.bl(GEN_SHINY_PID); a.str_sp('r0', 4)               # shiny personality for that ID
    a.movs('r0', 1); a.str_sp('r0', 0); a.str_sp('r0', 8)
    a.label('noshiny')
    a.movs('r3', 0x20)
    a.ldr_sp('r0', 0x20); a.lsrs('r0', 'r0', 2); a.bcond('cc', 'noiv')      # flags bit1
    a.movs('r3', 31)
    a.label('noiv')
    a.ldr_sp('r2', 0x18); a.ldr_sp('r1', 0x14); a.mov('r0', 'r7')
    a.bl(CREATEMON)
    a.ldr('r0', 'r5', 0x20); a.ldr('r0', 'r0', 0); a.bl(MAPSEC_OF_MAP); a.mov('r6', 'r0')
    a.ldr('r0', 'r5', 0xC); a.bl(GET_PROFILE); a.mov('r1', 'r0')
    a.movs('r0', 0x18); a.str_sp('r0', 0); a.movs('r0', 0xB); a.str_sp('r0', 4)
    a.mov('r3', 'r6'); a.movs('r2', 4); a.mov('r0', 'r7')
    a.bl(SET_MET_DATA)
    a.ldr_sp('r0', 0x1C); a.cmp('r0', 25); a.bcond('cs', 'nonat')          # nature (0xFFFF = keep PID's)
    a.adds8('r0', 1); a.str_sp('r0', 8)
    a.mov('r0', 'r7'); a.movs('r1', MON_NATURE); a.add_rd_sp('r2', 8); a.bl(SET_MON_DATA)
    a.label('nonat')
    a.ldr_sp('r0', 0x24); a.cmp('r0', 2); a.bcond('hi', 'noab'); a.bcond('ne', 'slot')
    a.movs('r0', 1); a.str_sp('r0', 8)
    a.mov('r0', 'r7'); a.movs('r1', MON_HIDDEN_AB); a.add_rd_sp('r2', 8); a.bl(SET_MON_DATA)
    a.b('recalc')
    a.label('slot')
    a.str_sp('r0', 8)
    a.mov('r0', 'r7'); a.movs('r1', MON_AB_SLOT); a.add_rd_sp('r2', 8); a.bl(SET_MON_DATA)
    a.label('recalc')
    a.mov('r0', 'r7'); a.bl(SET_ABILITY)
    a.label('noab')
    a.mov('r0', 'r7'); a.movs('r1', 3); a.bl(PERFECT_IVS)                 # as GiveMon; recalcs stats
    a.mov('r0', 'r4'); a.mov('r1', 'r7'); a.bl(PARTY_ADD); a.mov('r6', 'r0')
    a.cmp('r0', 0); a.bcond('eq', 'nodex')
    a.ldr('r0', 'r5', 0xC); a.mov('r1', 'r7'); a.bl(DEX_REGISTER)
    a.label('nodex')
    a.mov('r0', 'r7'); a.bl(FREE)
    a.label('store')
    a.ldr_sp('r1', 0x28); a.mov('r0', 'r5'); a.bl(SCRIPT_GET_VPTR)
    a.cmp('r0', 0); a.bcond('eq', 'done')
    a.strh('r6', 'r0', 0)
    a.label('done')
    a.movs('r0', 0); a.add_sp(0x30); a.pop_r4_r7_pc()
    # ---- sub 1: SetPartyMonData(slot, field, value)  (e.g. 0x71 hidden flag, 0x0A ability)
    a.label('sub1')
    a.ldr_sp('r1', 0x14); a.ldr('r2', 'r4', 4); a.cmpr('r1', 'r2'); a.bcond('cs', 'done')
    a.movs('r2', 0xEC); a.muls('r1', 'r2'); a.addr('r0', 'r4', 'r1'); a.adds8('r0', 8)
    a.ldr_sp('r1', 0x18); a.add_rd_sp('r2', 0x1C); a.bl(SET_MON_DATA)
    a.b('done')
    code = a.assemble()
    assert MODCMD + len(code) <= MODCMD_END, hex(len(code))
    return code + b'\x00' * (MODCMD_END - MODCMD - len(code))

# ---------------------------------------------------------------- battle abilities (ov14)
OV = 14
AB_TABLE = 0x0224FF2C           # u32 handler (thumb) per ability id; handler(&count) -> {event, func} list
VAR_ATTACKER, VAR_MOVE = 0x0A, 0x29
EV_GET, EV_MUL = 0x0220FCC0, 0x0220FDD4
SOLAR_FLARE, AURA_GUARDIAN, AZURE_SKIN = 253, 306, 318
DARK_TIDE = 293                 # was Supreme Overlord (unused by any Pokemon or trainer): Dark Aura + Water x1.5
DT_HANDLER = 0x02239A4C         # Supreme Overlord's handler: movs r1,#3; str r1,[r0]; ldr r0,=list; bx lr; .word list
DARK_AURA_LIST = [(0x0A, 0x022360A1), (0x1F, 0x022360A1), (0x71, 0x022360B1)]   # entry message + Dark move power
TYPE_WATER = 11
OLD_HANDLERS = {SOLAR_FLARE: 0x0223817D, AURA_GUARDIAN: 0x0223A181, AZURE_SKIN: 0x0223A55D}
DROUGHT_ON  = 0x02232F05        # events 0x0A / 0x1F (switch-in): set sun
DRIZZLE_ON  = 0x0223147D        # events 0x0A / 0x1F: set rain
SOLAR_BOOST = 0x0223359D        # event 0x75: special attacker in sun (2/9) -> x1.5. (0x14 -> 0x223353D is the HP loss)
HEAL_PULSE  = 0x02235D81        # Mega Launcher's event 0x8B function (Heal Pulse)
AZURE_LIST  = 0x0224F4D8        # Azure Skin's 3 original entries
# Freed space: Supersweet Syrup's handler + switch-in function (0x223A180..0x223A28C), referenced
# only by table[306] and its own list at 0x224EDF8 (which nothing else uses).
CAVE, CAVE_END = 0x0223A180, 0x0223A28C
# Mega Launcher (0x2235D2D) hard-codes its moves (no move-data flag): Water Pulse, Dark Pulse,
# Dragon Pulse, Aura Sphere, Origin Pulse, Heal Pulse. Aura Guardian adds Vacuum Wave, Flash Cannon,
# Terrain Pulse and Aura Wheel.
AURA_MOVES = [352, 396, 399, 406, 410, 430, 618, 783, 805]

def build_battle(azure_old):
    a = A(CAVE)
    def handler(name, n):
        a.align4(); a.label(name + '_h')
        a.h(0x2100 | n); a.h(0x6001); a.ldrl('r0', name + '_lp'); a.bx_lr()
        a.label(name + '_lp'); a.w32(0)          # patched below with the list address
    handler('sf', 3); handler('ag', 2); handler('az', 5)
    lists = {
        'sf': [(0x0A, DROUGHT_ON), (0x1F, DROUGHT_ON), (0x75, SOLAR_BOOST)],
        'ag': [(0x71, None), (0x8B, HEAL_PULSE)],                       # None = our power function
        'az': azure_old + [(0x0A, DRIZZLE_ON), (0x1F, DRIZZLE_ON)],
    }
    for k, ents in lists.items():
        a.align4(); a.label(k + '_list')
        for ev, fn in ents: a.w32(ev); a.w32(fn if fn else 0)
    # Dark Tide: Dark Aura's entries + a Water attack-stat x1.5 (clone of Dragon's Maw 0x2238809, event 0x75)
    a.align4(); a.label('dt_list')
    for ev, fn in DARK_AURA_LIST: a.w32(ev); a.w32(fn)
    a.w32(0x75); a.w32(0)                       # patched with dtf below
    a.label('dtf')
    a.push_r4_lr(); a.movs('r0', VAR_ATTACKER); a.mov('r4', 'r1'); a.bl(EV_GET)
    a.cmpr('r4', 'r0'); a.bcond('ne', 'dtx')
    a.movs('r0', 0x2C); a.bl(EV_GET); a.cmp('r0', TYPE_WATER); a.bcond('ne', 'dtx')
    a.movs('r1', 6); a.lsls('r1', 'r1', 10); a.movs('r0', 0x47); a.bl(EV_MUL)   # x1.5
    a.label('dtx')
    a.pop_r4_pc()
    # Aura Guardian power function (clone of Mega Launcher's, with a move list)
    a.label('agf')
    a.push_r4_lr(); a.movs('r0', VAR_ATTACKER); a.mov('r4', 'r1'); a.bl(EV_GET)
    a.cmpr('r4', 'r0'); a.bcond('ne', 'agx')
    a.movs('r0', VAR_MOVE); a.bl(EV_GET); a.lsls('r0', 'r0', 16); a.lsrs('r0', 'r0', 16)
    a.adr('r1', 'moves')
    a.label('agl')
    a.ldrh('r2', 'r1', 0); a.cmp('r2', 0); a.bcond('eq', 'agx')
    a.adds8('r1', 2); a.cmpr('r2', 'r0'); a.bcond('ne', 'agl')
    a.movs('r1', 6); a.lsls('r1', 'r1', 10); a.movs('r0', 0x1C); a.bl(EV_MUL)   # x0x1800/0x1000 = 1.5
    a.label('agx')
    a.pop_r4_pc()
    a.align4(); a.label('moves')
    for m in AURA_MOVES + [0]: a.hw(m)
    code = bytearray(a.assemble())
    L = a.labels
    for k in lists: struct.pack_into('<I', code, L[k + '_lp'] - CAVE, L[k + '_list'])
    struct.pack_into('<I', code, L['ag_list'] + 4 - CAVE, L['agf'] + 1)
    struct.pack_into('<I', code, L['dt_list'] + 28 - CAVE, L['dtf'] + 1)
    assert CAVE + len(code) <= CAVE_END, hex(len(code))
    code += b'\x00' * (CAVE_END - CAVE - len(code))
    return bytes(code), {SOLAR_FLARE: L['sf_h'] + 1, AURA_GUARDIAN: L['ag_h'] + 1, AZURE_SKIN: L['az_h'] + 1}, L['dt_list']

# ---------------------------------------------------------------- texts
ABILITY_NAMES, ABILITY_DESCS = 711, 712      # a/0/2/7 banks, index = ability id; names <= 12 chars; line break is the 2-char '\n'
NL = chr(92) + 'n'                            # message line break (backslash + n)
TEXTS = {
    SOLAR_FLARE:   ('Perish Body', 'Solar Flare', 'Summons sunlight.' + NL + 'Boosts Sp. Atk in sun.'),
    AURA_GUARDIAN: ('SuprswtSyrup', 'AuraGuardian', 'Powers up aura and' + NL + 'pulse moves.'),
    AZURE_SKIN:    ('Azure Skin', None, 'Summons rain on entry.' + NL + 'Normal moves turn Water.'),
    DARK_TIDE:     ('SuprmOverlrd', 'Dark Tide', 'Ups Dark moves on field' + NL + 'and its own Water moves.'),
}

VACUUM_WAVE = 410

def apply(ctx):
    # GiveMon shiny hook (species | 0x8000 -> shiny) + Manaphy egg icon/palette helpers
    for addr, exp in codepatch.EXPECT.items():
        assert ctx.arm9_read(addr, len(exp)) == exp, hex(addr)
    assert ctx.arm9_read(codepatch.SCRCMD_GIVEMON, 4) == bytes.fromhex('f0b589b0')
    patches, _ = codepatch.build()
    for addr, code in patches: ctx.arm9_write(addr, code)
    # Manaphy egg icon: append the original Manaphy Egg icon as pokeicon entry 0xB4A
    old = ctx.narc('a/0/2/0'); icons = ctx.narc('data/pokeicon.narc')
    assert len(icons) == 0xB4A
    icons.append(old[502]); ctx.log.append('icon 0xB4A = original Manaphy Egg icon')

    # ModCmd: table entry 62 already points at 0x2040915 (the old handler's start); replace the body.
    assert struct.unpack('<I', ctx.arm9_read(SCRCMD_TABLE + 137*4, 4))[0] == codepatch.SCRCMD_GIVEMON + 1
    assert struct.unpack('<I', ctx.arm9_read(SCRCMD_TABLE + 62*4, 4))[0] == MODCMD + 1
    ctx.arm9_write(MODCMD, build_modcmd(), expect=bytes.fromhex('f0b583b0'))

    # Battle abilities
    for ab, h in OLD_HANDLERS.items():
        assert struct.unpack('<I', ctx.ov_read(OV, AB_TABLE + ab*4, 4))[0] == h, ab
    azure = ctx.ov_read(OV, AZURE_LIST, 24)
    azure_old = [struct.unpack_from('<II', azure, 8*i) for i in range(3)]
    assert azure_old == [(0x3B, 0x223A5B1), (0x71, 0x223A5BD), (0xB2, 0x2235BB9)], azure_old
    assert ctx.ov_read(OV, 0x0223A55C, 4) == bytes.fromhex('03210160')         # movs r1,#3; str r1,[r0]
    assert ctx.ov_read(OV, 0x0224EC78, 16) == struct.pack('<4I', 0x14, 0x223353D, 0x75, SOLAR_BOOST)
    assert ctx.ov_read(OV, 0x0224EF48, 16) == struct.pack('<4I', 0x71, 0x2235D2D, 0x8B, HEAL_PULSE)
    assert ctx.ov_read(OV, 0x0224F028, 16) == struct.pack('<4I', 0x0A, DROUGHT_ON, 0x1F, DROUGHT_ON)
    assert ctx.ov_read(OV, 0x0224EEF8, 16) == struct.pack('<4I', 0x0A, DRIZZLE_ON, 0x1F, DRIZZLE_ON)
    assert ctx.ov_read(OV, CAVE, 4) == bytes.fromhex('02210160')
    for ev_fn, want in zip(DARK_AURA_LIST, [0x0224F370 + 8*i for i in range(3)]):
        assert ctx.ov_read(OV, want, 8) == struct.pack('<II', *ev_fn), hex(want)
    assert ctx.ov_read(OV, 0x02238808, 32) == bytes.fromhex('10b50a200c1cd7f757fa844209d12c20d7f752fa102804d1062147208902d7f7d5fa')[:32]
    code, handlers, dt_list = build_battle(azure_old)
    # Dark Tide: reuse Supreme Overlord's handler in place with 4 entries and our list
    ctx.ov_write(OV, DT_HANDLER, bytes.fromhex('04210160004870 47'.replace(' ', '')) + struct.pack('<I', dt_list),
                 expect=bytes.fromhex('032101600048704758f32402'))
    assert struct.unpack('<I', ctx.ov_read(OV, AB_TABLE + DARK_TIDE*4, 4))[0] == DT_HANDLER + 1
    ctx.ov_write(OV, CAVE, code)
    for ab, h in handlers.items():
        ctx.ov_write(OV, AB_TABLE + ab*4, struct.pack('<I', h), expect=struct.pack('<I', OLD_HANDLERS[ab]))

    # Vacuum Wave 40 -> 60 power (byte 3 of its 40-byte entry). Byte 33 bit 0x10 is NOT a pulse flag
    # (it is the Gen 5 long-range flag: Gust, Peck, Fly, Air Slash, ... ) so no flags are changed.
    mv = ctx.narc('extra/new_move_data.narc')
    d = bytearray(mv[VACUUM_WAVE]); assert d[3] == 40, d[3]
    d[3] = 60; mv[VACUUM_WAVE] = bytes(d); ctx.log.append('move 410 Vacuum Wave power 40 -> 60')

    # Ability names / descriptions
    for ab, (old_name, name, desc) in TEXTS.items():
        assert ctx.bank(ABILITY_NAMES)[ab] == old_name, (ab, ctx.bank(ABILITY_NAMES)[ab])
        if name:
            assert len(name) <= 12; ctx.set_text(ABILITY_NAMES, ab, name)
        assert all(len(l) <= 25 for l in desc.split(NL))
        ctx.set_text(ABILITY_DESCS, ab, desc)
