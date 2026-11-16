# Trainers: max IVs, natures that fit the Pokemon, smarter AI (to balance the player's buffed gifts).
# Bosses always; regular trainers too while REGULAR is True. Legend battles and Frontier brains are skipped.
# Trainer data (a/0/5/5, 20 bytes): +0 type, +1 class, +3 count, +12 u32 AI flags, +16 u32 battle type.
# Trainer party (a/0/5/6, 28 bytes per Pokemon): +0 IV level (0-255 -> IVs = v*31/255), +3 nature,
# +4 ability, +6 level, +8 species (low 10 bits), +10 item, +12 moves.
# Natures: kept when they already raise the Pokemon's main attacking stat, or raise Speed / a defense
# without lowering the main attacking stat (the hack's deliberate picks, e.g. Bold Venusaur). Otherwise
# replaced by Adamant/Modest, or Jolly/Timid for base Speed >= 95. Main attacking stat = the side most of its
# moves use (physical vs special), base Atk vs SpA on a tie. Nature 255 in the data = unset (random).
# AI flags 0x30F = basic | evaluate attacks | expert | setup | check HP | weather (+0x80 tag strategy in doubles),
# OR'ed onto the existing flags (names from the hack's debug menu, bank 152.163-173).
#
# HP IV: the hack's party builder (arm9 0x0207272C) sets every IV from byte +0, then overwrites the HP IV
# (MON_DATA 0x46, its loop never advances the field) with a level tier: 10 up to Lv 40, 20 for Lv 41-79,
# 31 from Lv 80. Patched at 0x020728E0 (32 bytes, same size): IV byte 255 (every trainer we touch) -> HP IV 31;
# untouched trainers keep the tiers. The entry pointer is r7; r1/r2 are free here, the tier byte goes to sp+0x2C.
import struct
from thumb import Asm

HP_TIER, HP_TIER_ORIG = 0x020728E0, bytes.fromhex('0a210ba80170f988282904d9502902d21421017004e0502902d31f210ba80170')

def build_hp_tier():
    a = Asm(HP_TIER)
    a.h(0x7839)                              # ldrb r1, [r7]       IV byte
    a.cmp('r1', 0xFF); a.bcond('eq', 'max')
    a.movs('r1', 10)
    a.h(0x88FA)                              # ldrh r2, [r7, #6]   level
    a.cmp('r2', 0x28); a.bcond('ls', 'store')
    a.cmp('r2', 0x50); a.bcond('hs', 'max')
    a.movs('r1', 20); a.bcond('al', 'store')
    a.label('max'); a.movs('r1', 31)
    a.label('store'); a.add_rd_sp('r0', 0x2C)
    a.h(0x7001)                              # strb r1, [r0]
    while a.pc() < HP_TIER + 32: a.nop()
    code = a.assemble(); assert len(code) == 32, len(code)
    return code

REGULAR = True       # also give regular trainers the same treatment (levels unchanged)
SKIP_CLASSES = {8, 123,                     # blank-named classes: legend battles (e.g. Articuno 505, Reshiram 1024)
                97, 99, 100, 101, 102}      # Frontier brains (placeholder Lv 5 data)
BOSS_CLASSES = {
    0, 1,                                   # PKMN Trainer (named story characters)
    17, 51, 83, 84, 95, 96, 114, 116, 117, 118,   # Executive
    39, 40, 44, 45, 69,                     # Rocket Elite
    66, 67, 70, 72, 73, 74, 75, 76, 98, 104, 105, 106, 107, 108,   # Leader
    86, 124,                                # Rocket Boss
    87, 88, 89, 112,                        # Elite Four
    90, 110,                                # Rival
    93, 94, 103, 125, 126, 91, 92,          # Cerulean / Viridian / Johto / Hoenn / Sinnoh Trainer
    127, 128,                               # Hoenn / Sinnoh Champion
}
SMART_AI, TAG_AI = 0x30F, 0x80
ATK, DEF, SPE, SPA, SPD = range(5)          # nature stat order
ADAMANT, MODEST, JOLLY, TIMID = 3, 15, 13, 10
FOUL_PLAY = 492                             # uses the target's Attack: doesn't care about the user's nature

def pick_nature(cur, base, moves, M):
    hp, atk, df, spe, spa, spd = base[:6]
    phys = sum(1 for m in moves if 0 < m < len(M) and M[m][2] == 1 and m != FOUL_PLAY)
    spec = sum(1 for m in moves if 0 < m < len(M) and M[m][2] == 2)
    status = sum(1 for m in moves if 0 < m < len(M) and M[m][2] == 0)
    if cur < 25 and cur // 5 != cur % 5 and status >= 2: return cur     # support set: keep the hack's pick
    if phys != spec: main = ATK if phys > spec else SPA
    elif atk != spa: main = ATK if atk > spa else SPA
    else: return cur if cur < 25 else ADAMANT
    up, down = cur // 5, cur % 5
    if cur < 25 and up != down and down != main:
        if up == main or up in (SPE, DEF, SPD):
            return cur
    if spe >= 95: return JOLLY if main == ATK else TIMID
    return ADAMANT if main == ATK else MODEST

def apply(ctx):
    ctx.arm9_write(HP_TIER, build_hp_tier(), expect=HP_TIER_ORIG)
    td, tp, P = ctx.narc('a/0/5/5'), ctx.narc('a/0/5/6'), ctx.narc('a/0/0/2')
    M = ctx.narc('extra/new_move_data.narc')          # +2 category: 0 status, 1 physical, 2 special
    n_tr = n_mon = n_nat = 0
    for t in range(len(td)):
        d = bytearray(td[t])
        if d[3] == 0 or d[1] in SKIP_CLASSES or not (REGULAR or d[1] in BOSS_CLASSES): continue
        p = bytearray(tp[t]); assert len(p) == 28 * d[3], (t, len(p), d[3])
        ai = struct.unpack_from('<I', d, 12)[0] | SMART_AI
        if struct.unpack_from('<I', d, 16)[0]: ai |= TAG_AI
        struct.pack_into('<I', d, 12, ai)
        for i in range(d[3]):
            o = i * 28
            sp = struct.unpack_from('<H', p, o + 8)[0] & 0x3FF
            if sp == 0 or sp >= len(P): continue
            p[o] = 255
            nat = pick_nature(p[o + 3], P[sp], struct.unpack_from('<4H', p, o + 12), M)
            if nat != p[o + 3]: n_nat += 1
            p[o + 3] = nat; n_mon += 1
        td[t], tp[t] = bytes(d), bytes(p); n_tr += 1
    ctx.log.append('trainers: %d trainers (%s) -> IV 255 on %d Pokemon, %d natures changed, AI |= 0x%X' % (n_tr, 'bosses + regular' if REGULAR else 'bosses', n_mon, n_nat, SMART_AI))
