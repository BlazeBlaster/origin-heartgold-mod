# Species / move / encounter data changes. See patch.py for the ctx API.
#   1. Shadow Lugia in species slot 717 (Yveltal, unobtainable): copy of Lugia (249), Psychic/Dark,
#      Dark Aura / Dark Aura / Shadow Shield, recoloured battle sprites + follower model, Lugia's cry.
#      BST 680 moved into SpA/Spe; Dark moves instead of Aeroblast (saved for a purification quest).
#      Baby form "Lugiling" in slot 716 (Xerneas): BST 300, shrunken big-headed sprites, evolves at Lv 40.
#   2. Charmander line ability slot 2 -> 253 ("Solar Flare", code in mod_code.py).
#   3. Riolu / Lucario ability slot 1 -> 306 ("Aura Guardian"); Riolu learns Flash Cannon at Lv 20.
#   4. Vacuum Wave (410) removed from Hitmonchan / Kartana level-up and Tyrogue / Croagunk egg moves.
#   5. Wild a/0/3/7[83] morning slot 11: Charmander -> Cyndaquil.
import os, sys, struct, runpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LUGIA_DIR = os.path.join(ROOT, 'lugia')

LUGIA, SLOT = 249, 717
PSYCHIC, DARK = 14, 17
DARK_AURA, SHADOW_SHIELD = 186, 231        # bank 711 ability names
DARK_TIDE = 293                            # custom: Dark Aura + own Water moves x1.5 (mod_code.py)
SOLAR_FLARE, AURA_GUARDIAN = 253, 306      # repurposed by mod_code.py
BLAZE, TOUGH_CLAWS = 66, 181
VACUUM_WAVE, FLASH_CANNON, MACH_PUNCH, COMET_PUNCH, LEAFAGE = 410, 430, 183, 4, 670
HITMONCHAN, KARTANA, TYROGUE, CROAGUNK, RIOLU, LUCARIO = 107, 798, 236, 453, 447, 448
CHARMANDER, CYNDAQUIL = 4, 155
LUGIA_MODEL = 579                          # a/0/8/1 follower model (the clones' own models are overwritten with it)
OW_TABLE = 0x020FBE24                      # arm9: 6-byte rows (sprite id, model, flags)
ICON_PAL = 0x020FF7FC                      # arm9: u8 icon palette per species
SHADOW_STATS = (106, 90, 100, 120, 140, 124)  # HP/Atk/Def/Spe/SpA/SpD, BST 680 (Lugia 106/90/130/110/90/154)
BABY, BABY_NAME, BABY_EVO = 716, 'Lugiling', 40   # Xerneas slot (unobtainable); evolves into Shadow Lugia
BABY_STATS = (60, 40, 50, 50, 55, 45)       # BST 300
BABY_HW = (12, 216)                         # 1.2 m, 21.6 kg
PIKA_MODEL = 322                            # a/0/8/1 Pikachu follower: small 32x32 layout
BABY_SHADOW = (0, 0, 1)                     # a/1/8/0: hover 0, shadow centred, small shadow
BABY_MOVES = [(1, 16), (1, 18), (7, 44), (13, 246), (20, 555), (27, 347), (34, 326)]
BABY_MOVE_NAMES = {16: 'Gust', 18: 'Whirlwind', 44: 'Bite', 246: 'AncientPower', 555: 'Snarl', 347: 'Calm Mind', 326: 'Extrasensory'}
BABY_DEX = ('A young Lugia that drifted away from\\n'
            'the deep sea. Darkness crept into its\\n'
            'heart while it was scared and alone.')
BITE, SNARL, DARK_PULSE, CHARGE_BEAM, MIST, SAFEGUARD, AEROBLAST = 44, 555, 399, 451, 54, 219, 177
HYDRO_PUMP, SURF, RECOVER = 56, 57, 105
SHADOW_SWAP = {(9, MIST): BITE, (18, SAFEGUARD): SNARL, (54, AEROBLAST): DARK_PULSE}
SHADOW_NAME = 'ShdwLugia'
SHADOW_DEX = ('A Lugia whose heart was sealed away\\n'
              'by darkness. Its red eyes burn with\\n'
              'rage, and its wings whip up storms.')

def _bin(name):
    return open(os.path.join(LUGIA_DIR, name), 'rb').read()

def _pal_offset(nclr):
    i = nclr.find(b'TTLP'); return i + 8 + struct.unpack_from('<I', nclr, i + 0x14)[0]

def _set_pal(nclr, cols):
    assert len(cols) == 32
    p = _pal_offset(nclr); b = bytearray(nclr); b[p:p+32] = cols; return bytes(b)

def _ncgr_px_offset(ncgr):
    i = ncgr.find(b'RAHC'); return i + 8 + struct.unpack_from('<I', ncgr, i + 0x1C)[0], struct.unpack_from('<H', ncgr, i + 10)[0] * 8

def _learnset(d):
    out = []
    for i in range(0, len(d), 4):
        lv, mv = struct.unpack_from('<HH', d, i)
        if lv == 0xFFFF: return out, d[i:]
        out.append((lv, mv))
    raise ValueError('unterminated learnset')

def _pack_learnset(moves, tail):
    return b''.join(struct.pack('<HH', lv, mv) for lv, mv in moves) + tail

def _u16list(d):
    v = []
    for i in range(0, len(d), 2):
        x = struct.unpack_from('<H', d, i)[0]
        if x == 0xFFFF: return v
        v.append(x)
    raise ValueError('unterminated list')

def _pack_u16list(v, pad4):
    b = struct.pack('<%dH' % (len(v) + 1), *v, 0xFFFF)
    while pad4 and len(b) % 4: b += b'\0\0'
    return b

# ---------------------------------------------------------------- Shadow Lugia
def _add_dark_pulse(ctx, slot):
    T = ctx.narc('data/tutor_moves.narc'); v = _u16list(T[slot]); assert DARK_PULSE not in v
    v.insert(v.index(CHARGE_BEAM) + 1, DARK_PULSE)       # list is alphabetical
    T[slot] = _pack_u16list(v, len(T[slot]) % 4 == 0); ctx.log.append('tutor list %d: + Dark Pulse' % slot)

def clone_lugia(ctx, slot, old_name, name, dex, category, hw=None):
    """Copy Lugia (249) into an unobtainable species slot as a shadow variant: Psychic/Dark, Dark Aura x2 /
    Shadow Shield, recoloured battle sprites (+ red eyes), follower model, Lugia's cry, name, Pokedex entry.
    hw = (height dm, weight hg) for the Pokedex, Lugia's when None."""
    log = ctx.log.append
    P = ctx.narc('a/0/0/2'); e = bytearray(P[LUGIA]); assert len(e) == 52
    e[6], e[7] = PSYCHIC, DARK
    struct.pack_into('<3H', e, 0x16, DARK_TIDE, DARK_TIDE, SHADOW_SHIELD)
    P[slot] = bytes(e); log('personal %d <- %d, Psychic/Dark, abilities %d/%d/%d' % (slot, LUGIA, DARK_TIDE, DARK_TIDE, SHADOW_SHIELD))
    # learnset, evolutions, egg moves (both tables), tutor moves
    for nm in ('a/0/3/3', 'a/0/3/4', 'a/2/2/9', 'data/egg_moves.narc', 'data/tutor_moves.narc'):
        n = ctx.narc(nm); n[slot] = n[LUGIA]
    log('learnset/evolution/egg/tutor tables [%d] <- [%d]' % (slot, LUGIA))
    # battle sprites: 8 entries per species, both pokepic narcs (Lugia's female entries are empty placeholders)
    shadow = _bin('battle_shadowF.bin')
    edits = runpy.run_path(os.path.join(LUGIA_DIR, 'eye_edits.py'))['EDITS']
    for nm in ('data/pokepic_m.narc', 'data/pokepic_f.narc'):
        n = ctx.narc(nm)
        for k in range(8):
            d = n[LUGIA*8 + k]
            if k & 1: d = _set_pal(d, shadow)                       # +1/+3 normal, +5/+7 shiny: all shadowF
            elif nm.endswith('_m.narc'):
                src = LUGIA*8 + (k & 2)                             # +4 / +6 are copies of +0 / +2
                assert n[LUGIA*8 + k] == n[src]
                off, W = _ncgr_px_offset(d); b = bytearray(d)
                for (ent, x, y), v in edits.items():
                    if ent != src: continue
                    i = off + (y*W + x)//2; sh = 4*(x & 1)
                    b[i] = (b[i] & ~(15 << sh) & 0xFF) | (v << sh)
                d = bytes(b)
            n[slot*8 + k] = d
    log('pokepic_m/f %d..%d <- Lugia, palettes = battle_shadowF, red eyes' % (slot*8, slot*8 + 7))
    # sprite anim/offset/shadow record (89 bytes per species)
    a = ctx.narc('a/1/8/0'); d = bytearray(a[0])
    d[slot*89:(slot+1)*89] = d[LUGIA*89:(LUGIA+1)*89]; a[0] = bytes(d)
    # party icon + palette index
    ic = ctx.narc('data/pokeicon.narc')
    for k in (7, 8): ic[k + 2*slot] = ic[k + 2*LUGIA]
    ctx.arm9_write(ICON_PAL + slot, ctx.arm9_read(ICON_PAL + LUGIA, 1))
    # follower: pokemon_overworld_info[slot] -> sprite id +428 -> arm9 row -> model; overwrite with Lugia's model
    oi = ctx.narc('data/pokemon_overworld_info.narc')
    sprite = struct.unpack_from('<H', oi[slot])[0] + 428
    rows = {}
    for i in range(0, 1715*6, 6):
        sp, m, fl = struct.unpack('<HHH', ctx.arm9_read(OW_TABLE + i, 6)); rows.setdefault(sp, (m, fl))
    lug_sprite = struct.unpack_from('<H', oi[LUGIA])[0] + 428
    assert rows[lug_sprite][0] == LUGIA_MODEL and rows[lug_sprite][1] == rows[sprite][1], (sprite, rows.get(sprite))
    model = rows[sprite][0]
    ow = ctx.narc('a/0/8/1'); m = bytearray(ow[LUGIA_MODEL]); fol = _bin('follower_shadowF.bin'); assert len(fol) == 32
    from lugia_btx import btx_parse
    _, _, pals = btx_parse(bytes(m)); tex = struct.unpack_from('<I', m, 0x10)[0]
    offs = sorted(tex + p['off'] for p in pals)
    assert offs == [0x4180, 0x41A0], [hex(x) for x in offs]       # tsure_poke0 (normal) / tsure_poke1 (shiny)
    for o in offs: m[o:o+32] = fol
    ow[model] = bytes(m); log('a/0/8/1[%d] <- [%d] recoloured follower_shadowF (overworld sprite id %d)' % (model, LUGIA_MODEL, sprite))
    # cry: point WAVE_ARC_PV<slot> at Lugia's wave archive file
    from species_sdat import names, info_records
    fid = ctx.rom.files['data/sound/gs_sound_data.sdat']; base = ctx.rom.span(fid)[0]; sd = ctx.rom.get(fid)
    nm, rec = names(sd, 3), info_records(sd, 3)
    i249, isl = nm.index('WAVE_ARC_PV249'), nm.index('WAVE_ARC_PV%d' % slot)
    src = struct.unpack_from('<I', sd, rec[i249])[0]; dst = struct.unpack_from('<I', sd, rec[isl])[0]
    struct.pack_into('<I', ctx.rom.b, base + rec[isl], (dst & 0xFF000000) | (src & 0xFFFFFF))
    log('sdat WAVE_ARC_PV%d (#%d) file %d -> %d (Lugia cry)' % (slot, isl, dst & 0xFFFFFF, src & 0xFFFFFF))
    # names / Pokedex
    assert ctx.bank(232)[slot] == old_name and len(name) <= 10
    ctx.set_text(232, slot, name)
    ctx.set_text(791, slot, dex)
    ctx.set_text(803, slot, category)
    for b in (801, 799): ctx.set_text(b, slot, ctx.bank(b)[LUGIA])
    z = ctx.narc('a/0/7/4')
    for t in (0, 1):
        d = bytearray(z[t]); d[slot*4:slot*4+4] = d[LUGIA*4:LUGIA*4+4]
        if hw: struct.pack_into('<I', d, slot*4, hw[t])
        z[t] = bytes(d)
    for t in range(3, 11):
        d = bytearray(z[t]); d[slot*2:slot*2+2] = d[LUGIA*2:LUGIA*2+2]; z[t] = bytes(d)
    # regional dex: append as the last entry ([12] = regional order; a/1/3/8 = species -> regional no., 0 = '???'),
    # and insert into the weight/height orders ([14] weight desc, [15] weight asc, [16] height desc, [17] height asc).
    # [13]/[18..43] are Japanese name-order lists that already hold the slot (under the Gen 6 kana); left alone.
    def u16s(b): return list(struct.unpack('<%dH' % (len(b) // 2), b))
    reg = u16s(z[12]); assert slot not in reg
    reg.append(slot); z[12] = struct.pack('<%dH' % len(reg), *reg)
    rn = ctx.narc('a/1/3/8'); m = bytearray(rn[0]); assert struct.unpack_from('<H', m, slot*2)[0] == 0
    struct.pack_into('<H', m, slot*2, len(reg)); rn[0] = bytes(m)
    H = struct.unpack('<%dI' % (len(z[0]) // 4), z[0]); Wt = struct.unpack('<%dI' % (len(z[1]) // 4), z[1])
    for t, key, desc in ((14, Wt, True), (15, Wt, False), (16, H, True), (17, H, False)):
        l = u16s(z[t]); assert slot not in l
        v = key[slot]; i = 0
        while i < len(l) and ((key[l[i]] >= v) if desc else (key[l[i]] <= v)): i += 1
        l.insert(i, slot); z[t] = struct.pack('<%dH' % len(l), *l)
    log('%s (%d): regional #%d, Pokedex height/weight %s' % (name, slot, len(reg), (H[slot], Wt[slot])))

def shadow_lugia(ctx):
    log = ctx.log.append
    clone_lugia(ctx, SLOT, 'Yveltal', SHADOW_NAME, SHADOW_DEX, 'Shadow Pokémon')
    # Offense over bulk: same BST as Lugia (680), moved from Def/SpD into SpA/Spe
    P = ctx.narc('a/0/0/2'); e = bytearray(P[SLOT]); e[:6] = bytes(SHADOW_STATS); P[SLOT] = bytes(e)
    log('personal %d stats HP/Atk/Def/Spe/SpA/SpD %s (BST %d)' % (SLOT, SHADOW_STATS, sum(SHADOW_STATS)))
    # Level-up: Dark moves for Dark Aura; Aeroblast is held back for the purification quest
    L = ctx.narc('a/0/3/3'); mv, tail = _learnset(L[SLOT])
    new = [(lv, SHADOW_SWAP.get((lv, m), m)) for lv, m in mv]
    assert sum(1 for a, b in zip(mv, new) if a != b) == len(SHADOW_SWAP)
    assert new.count((72, HYDRO_PUMP)) == 1; new.remove((72, HYDRO_PUMP))     # Surf at 45 instead (water moves get Dark Tide's boost)
    new.insert(new.index((45, RECOVER)) + 1, (45, SURF))
    L[SLOT] = _pack_learnset(new, tail); log('learnset %d: %s, Hydro Pump 72 -> Surf 45' % (SLOT, SHADOW_SWAP))
    # TM/tutor list: + Dark Pulse (TM79). Personal TM bits are unused in this hack; this list decides.
    _add_dark_pulse(ctx, SLOT)

def baby_lugia(ctx):
    """Baby Shadow Lugia (slot 716, Xerneas: unobtainable): BST 300, evolves into Shadow Lugia at Lv BABY_EVO.
    Sprites: shrunken, big-headed copies of the shadow sprites."""
    log = ctx.log.append
    clone_lugia(ctx, BABY, 'Xerneas', BABY_NAME, BABY_DEX, 'Shadow Pokémon', hw=BABY_HW)
    P = ctx.narc('a/0/0/2'); e = bytearray(P[BABY]); e[:6] = bytes(BABY_STATS); P[BABY] = bytes(e)
    log('personal %d stats HP/Atk/Def/Spe/SpA/SpD %s (BST %d)' % (BABY, BABY_STATS, sum(BABY_STATS)))
    mn = ctx.bank(739)
    for lv, m in BABY_MOVES: assert mn[m] == BABY_MOVE_NAMES[m], (m, mn[m])
    L = ctx.narc('a/0/3/3'); _, tail = _learnset(L[BABY]); L[BABY] = _pack_learnset(BABY_MOVES, tail)
    log('learnset %d: %s' % (BABY, ', '.join('%d %s' % (lv, mn[m]) for lv, m in BABY_MOVES)))
    _add_dark_pulse(ctx, BABY)
    E = ctx.narc('a/0/3/4'); d = bytearray(len(E[BABY])); struct.pack_into('<3H', d, 0, 4, BABY_EVO, SLOT); E[BABY] = bytes(d)
    log('evolution %d -> %d at Lv %d' % (BABY, SLOT, BABY_EVO))
    import baby_sprite
    pal, front, back = baby_sprite.load()
    for nm in ('data/pokepic_m.narc', 'data/pokepic_f.narc'):
        n = ctx.narc(nm)
        for k in (1, 3, 5, 7): n[BABY*8 + k] = _set_pal(n[BABY*8 + k], pal)   # normal + shiny: same (the gift is shiny)
    n = ctx.narc('data/pokepic_m.narc')
    for k, g in ((0, front), (2, back), (4, front), (6, back)):
        d = n[BABY*8 + k]; off, W = _ncgr_px_offset(d); assert W == 160
        px = bytearray(80*80)
        for y in range(80):
            for x in range(0, 160, 2): px[(y*160 + x)//2] = g[y][x] | (g[y][x+1] << 4)
        n[BABY*8 + k] = d[:off] + bytes(px) + d[off + 80*80:]
    log('pokepic_m/f %d: Lugiling sprites + palette from lugia/baby_front.png / baby_back.png' % (BABY*8))
    # follower: a small (32x32) model built from Pikachu's (322) with the user's walk frames; the sprite row for
    # pokemon_overworld_info[716] gets the small-follower flags in both tables (arm9 + overlay 1).
    pal, texs = baby_sprite.load_follower()
    from lugia_btx import btx_parse
    from mod_story import OV1_OW_TABLE
    ow = ctx.narc('a/0/8/1'); m = bytearray(ow[PIKA_MODEL])
    _, tl, pl = btx_parse(bytes(m)); tex = struct.unpack_from('<I', m, 0x10)[0]
    tl.sort(key=lambda x: x['off']); assert [(x['w'], x['h'], x['fmt']) for x in tl] == [(32, 32, 3)] * 8
    for x, data in zip(tl, texs): m[tex + x['off']:tex + x['off'] + 512] = data
    for p in pl: m[tex + p['off']:tex + p['off'] + 32] = pal
    oi = ctx.narc('data/pokemon_overworld_info.narc'); sprite = struct.unpack_from('<H', oi[BABY])[0] + 428
    for i in range(1715):
        sp, model, fl = struct.unpack('<HHH', ctx.arm9_read(OW_TABLE + i*6, 6))
        if sp == sprite: break
    else: raise AssertionError(sprite)
    pika_fl = next(struct.unpack('<HHH', ctx.arm9_read(OW_TABLE + j*6, 6))[2] for j in range(1715)
                   if struct.unpack('<HHH', ctx.arm9_read(OW_TABLE + j*6, 6))[1] == PIKA_MODEL)
    ow[model] = bytes(m)
    row = struct.pack('<HHH', sp, model, pika_fl)
    ctx.ov_write(1, OV1_OW_TABLE + i*6, row, expect=struct.pack('<HHH', sp, model, fl)); ctx.arm9_write(OW_TABLE + i*6, row)
    log('follower %d: model %d <- Pikachu %d + baby_ow_*.png frames, row %d flags %d -> %d' % (sprite, model, PIKA_MODEL, i, fl, pika_fl))
    # a/1/8/0 record tail (+86 hover height, +87 shadow x offset, +88 shadow size): Lugia 8/13/3 (big flier).
    # The baby sits low in its frame: no hover, small shadow under its body.
    a = ctx.narc('a/1/8/0'); d = bytearray(a[0]); r = BABY*89 + 86
    assert d[r:r+3] == bytes((8, 13, 3)); d[r:r+3] = bytes(BABY_SHADOW); a[0] = bytes(d)
    log('a/1/8/0 record %d: hover/shadow x/shadow size %s' % (BABY, BABY_SHADOW))

# ---------------------------------------------------------------- abilities, learnsets, egg moves
def abilities(ctx):
    P = ctx.narc('a/0/0/2')
    for s in (4, 5, 6):
        e = bytearray(P[s]); assert struct.unpack_from('<3H', e, 0x16) == (94, BLAZE, TOUGH_CLAWS), (s, struct.unpack_from('<3H', e, 0x16))
        struct.pack_into('<H', e, 0x18, SOLAR_FLARE); P[s] = bytes(e)
    ctx.log.append('personal 4-6 ability 2: Blaze -> %d (Solar Flare); hidden Tough Claws kept' % SOLAR_FLARE)
    for s in (RIOLU, LUCARIO):
        e = bytearray(P[s]); assert struct.unpack_from('<H', e, 0x16)[0] == 80, s
        struct.pack_into('<H', e, 0x16, AURA_GUARDIAN); P[s] = bytes(e)
    ctx.log.append('personal 447/448 ability 1: Steadfast -> %d (Aura Guardian)' % AURA_GUARDIAN)

def learnsets(ctx):
    L = ctx.narc('a/0/3/3')
    # Riolu: Flash Cannon at Lv 20 (after the existing Lv 20 move)
    mv, tail = _learnset(L[RIOLU]); assert all(m != FLASH_CANNON for _, m in mv)
    pos = max(i for i, (lv, _) in enumerate(mv) if lv <= 20) + 1
    mv.insert(pos, (20, FLASH_CANNON)); L[RIOLU] = _pack_learnset(mv, tail)
    ctx.log.append('learnset 447: + Flash Cannon Lv 20')
    # Vacuum Wave level-up removal
    for s, repl in ((HITMONCHAN, COMET_PUNCH), (KARTANA, LEAFAGE)):
        mv, tail = _learnset(L[s]); have = {m for _, m in mv}
        if s == HITMONCHAN and MACH_PUNCH not in have: repl = MACH_PUNCH
        assert repl not in have and any(m == VACUUM_WAVE for _, m in mv), s
        mv = [(lv, repl if m == VACUUM_WAVE else m) for lv, m in mv]; L[s] = _pack_learnset(mv, tail)
        ctx.log.append('learnset %d: Vacuum Wave -> move %d' % (s, repl))
    # Vacuum Wave egg-move removal, both per-species tables (a/2/2/9 unpadded, egg_moves.narc padded to 4)
    for nm, pad in (('a/2/2/9', False), ('data/egg_moves.narc', True)):
        n = ctx.narc(nm)
        for s in (TYROGUE, CROAGUNK):
            v = _u16list(n[s]); assert VACUUM_WAVE in v, (nm, s)
            n[s] = _pack_u16list([x for x in v if x != VACUUM_WAVE], pad)
        ctx.log.append('%s: Vacuum Wave removed from %d, %d' % (nm, TYROGUE, CROAGUNK))
    # legacy vanilla-format egg table (species+20000 headers); likely unused, kept consistent anyway
    k = ctx.narc('data/kowaza.narc'); v = list(struct.unpack('<%dH' % (len(k[0])//2), k[0])); out = []; cur = None
    for x in v:
        if 20000 < x < 0xFFFF: cur = x - 20000
        elif x == VACUUM_WAVE and cur in (TYROGUE, CROAGUNK): continue
        out.append(x)
    k[0] = struct.pack('<%dH' % len(out), *out); ctx.log.append('data/kowaza.narc: Vacuum Wave removed from %d, %d' % (TYROGUE, CROAGUNK))

def encounters(ctx):
    W = ctx.narc('a/0/3/7'); e = bytearray(W[83])
    assert e[8 + 11] == 5 and struct.unpack_from('<H', e, 20 + 2*11)[0] == CHARMANDER   # walk levels @8, morning species @20
    struct.pack_into('<H', e, 20 + 2*11, CYNDAQUIL); W[83] = bytes(e)
    ctx.log.append('wild a/0/3/7[83] morning slot 11: Charmander -> Cyndaquil Lv 5')

def apply(ctx):
    baby_lugia(ctx)
    shadow_lugia(ctx)
    abilities(ctx)
    learnsets(ctx)
    encounters(ctx)
