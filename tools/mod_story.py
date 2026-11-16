# Scripts, map objects and dialogue. See patch.py for the ctx API.
import struct
from patch import Code, msg, OP
import texts, os, importlib

# Story sub-modules (each has apply(ctx)), run in this order after the base story edits.
# Set STORY_ONLY=name1,name2 to run only some of them while testing.
SUBMODULES = ('story_comments', 'story_gifts', 'story_darkrai', 'story_seatemple', 'story_ilex', 'story_hermit', 'story_reshiram', 'story_cinnabar')

# Object id for the story's shiny map Pokémon. Ids 0xF0-0xF5 (the old "shiny palette" trick) are
# dropped by the map loader on a real map load (reserved for the hack's wild overworld spawns), so
# shiny objects use an ordinary id and a cloned sprite whose model has the shiny palette baked in.
SHINY_OBJ_ID = 230
OW_TABLE = 0x020FBE24                    # arm9: 1715 rows (sprite id u16, model u16, flags u16)
OV1_OW_TABLE = 0x0220659C                # identical copy in overlay 1 (the one the field map renderer uses)
FREE_SPRITE_ROWS = (1551, 1552, 1553, 1554, 1555)   # sprites 1730-1734: Revavroom (966) Starmobile form slots, dummy model 297
# (rows with model 0 / flags 64996, e.g. sprites 251-257/288-292, are special-cased by the engine and draw as crates)
_shiny_sprites = {}

def shiny_sprite(ctx, sprite):
    """Return a sprite id that draws `sprite`'s follower model with its shiny palette."""
    if sprite in _shiny_sprites: return _shiny_sprites[sprite]
    from lugia_btx import btx_parse
    rows = {}
    for i in range(1715):
        sp, m, fl = struct.unpack('<HHH', ctx.arm9_read(OW_TABLE + i*6, 6)); rows.setdefault(sp, (i, m, fl))
    _, model, flags = rows[sprite]
    ri = FREE_SPRITE_ROWS[len(_shiny_sprites)]
    new_sp, m0, fl0 = struct.unpack('<HHH', ctx.arm9_read(OW_TABLE + ri*6, 6)); assert m0 == 297 and 1730 <= new_sp <= 1734, (ri, new_sp, m0, fl0)
    ow = ctx.narc('a/0/8/1'); m = bytearray(ow[model])
    _, _, pals = btx_parse(bytes(m)); tex = struct.unpack_from('<I', m, 0x10)[0]
    pal = {p['name']: tex + p['off'] for p in pals}
    assert 'tsure_poke0' in pal and 'tsure_poke1' in pal, (sprite, list(pal))
    m[pal['tsure_poke0']:pal['tsure_poke0']+32] = m[pal['tsure_poke1']:pal['tsure_poke1']+32]
    ow.append(bytes(m)); new_model = len(ow) - 1
    row = struct.pack('<HHH', new_sp, new_model, flags)
    ctx.arm9_write(OW_TABLE + ri*6, row)
    ctx.ov_write(1, OV1_OW_TABLE + ri*6, row, expect=struct.pack('<HHH', new_sp, m0, fl0))
    ctx.log.append('shiny sprite %d -> %d (model %d -> %d, row %d)' % (sprite, new_sp, model, new_model, ri))
    _shiny_sprites[sprite] = new_sp
    return new_sp
F_ASKED, F_APPROVED, F_EGG = 2600, 2601, 2602   # unused event flags for the Ranger quest
VAR_SHINY = 0x8008
F_PEWTER_TRUE = 2615   # hides Pewter PC's true-form objects (Zorua/Mimikyu) until their reveal
LAB_HIDE = 1106        # vanilla flag, set during the starter choice: hides the lab's staged flicker objects

# ---------------- map object helpers ----------------
def objs_off(d):
    nbg = struct.unpack_from('<I', d, 0)[0]; o = 4 + nbg*20
    return o, struct.unpack_from('<I', d, o)[0]

def edit_obj(ctx, eb, oid, sprite=None, newid=None, shiny=False):
    en = ctx.narc('a/0/3/2'); d = bytearray(en[eb]); o, n = objs_off(d)
    for i in range(n):
        p = o + 4 + i*32
        if struct.unpack_from('<H', d, p)[0] == oid:
            if shiny: sprite = shiny_sprite(ctx, sprite if sprite is not None else struct.unpack_from('<H', d, p+2)[0])
            if sprite is not None: struct.pack_into('<H', d, p+2, sprite)
            if newid is not None: struct.pack_into('<H', d, p, newid)
            en[eb] = bytes(d); ctx.log.append('event %d obj %d -> sprite %s id %s shiny %s' % (eb, oid, sprite, newid, shiny)); return
    raise KeyError((eb, oid))

def add_obj(ctx, eb, sprite, script, x, z, copy_y_from, move=15, flag=0):
    en = ctx.narc('a/0/3/2'); d = bytearray(en[eb]); o, n = objs_off(d)
    ids = [struct.unpack_from('<H', d, o+4+i*32)[0] for i in range(n)]
    y = None
    for i in range(n):
        if ids[i] == copy_y_from: y = struct.unpack_from('<i', d, o+4+i*32+28)[0]
    newid = max(i for i in ids if i < 0xF0) + 1
    rec = struct.pack('<HHHHHHhHHHhhHHi', newid, sprite, move, 0, flag, script, 0, 0, 0, 0, 0, 0, x, z, y)
    assert len(rec) == 32
    p = o + 4 + n*32
    d[o:o+4] = struct.pack('<I', n+1); d[p:p] = rec
    en[eb] = bytes(d); ctx.log.append('event %d: new object id %d sprite %d script %d at (%d,%d)' % (eb, newid, sprite, script, x, z))
    return newid

# ---------------- ModCmd (script command 62, implemented in mod_code) ----------------
VAR_RESULT = 0x800C
F_SHINY, F_IV31 = 1, 2
RANDOM = 0xFFFF
def give_mon_ex(c, species, level, nature=RANDOM, flags=F_IV31, ability_slot=RANDOM, result=VAR_RESULT):
    c.op('ModCmd', 0, species, level, nature, flags, ability_slot, result)
def set_party_ability(c, slot, ability):
    # ModCmd sub 1 = SetPartyMonData(slot, field, value). Set the hidden-ability flag (0x71) too, so
    # the game's ability recompute keeps it: only use this for the species' hidden ability.
    c.op('ModCmd', 1, slot, 0x71, 1, 0, 0, 0)
    c.op('ModCmd', 1, slot, 0x0A, ability, 0, 0, 0)
NATURE = {'Adamant': 3, 'Timid': 10, 'Jolly': 13, 'Modest': 15}
FADE_WHITE = 0x7FFF

FLICKER = (14, 10, 8, 6, 4, 3, 2, 2, 1, 1)   # frames each form stays up, faster and faster

def reveal(c, t, first, cry_species, cry_text, oak_text, disguise=None, ow=None):
    """Disguise reveal after the 'received X' fanfare.
    ow=(dis_obj, dis_flag, true_obj, true_flag, show_dis_first, end_flags): the overworld sprite flickers between
    two map objects on the same tile (ShowPerson/HidePerson; each object's hide flag is cleared before showing it),
    a white flash leaves the true form, its cry plays on the map, then the picture window is the final shot and the
    true object is removed (end_flags are set again so it stays hidden).
    disguise=species (no ow): the same flicker done with the picture window instead."""
    c.op('BufferPlayersName', 0)
    if ow:
        dis, dflag, tru, tflag, show_first, end_flags = ow
        def show(o, f): c.op('ClearFlag', f); c.op('ShowPerson', o)
        if show_first: show(dis, dflag); c.op('Wait', 20, VAR_RESULT)
        msg(c, t[first])
        for n in FLICKER:
            c.op('HidePerson', dis); show(tru, tflag); c.op('Wait', n, VAR_RESULT)
            c.op('HidePerson', tru); show(dis, dflag); c.op('Wait', n, VAR_RESULT)
        c.op('FadeScreen', 6, 1, 0, FADE_WHITE); c.op('WaitFade')
        c.op('HidePerson', dis); show(tru, tflag)
        c.op('PlayCry', cry_species, 0)
        c.op('FadeScreen', 6, 1, 1, FADE_WHITE); c.op('WaitFade')
        c.op('NPCMsg', t[cry_text]); c.op('WaitCry'); c.op('WaitButton'); c.op('CloseMsg')
        c.op('ScrCmd_452', cry_species, 0)
        msg(c, t[oak_text])
        c.op('ScrCmd_453')
        c.op('HidePerson', tru)
        for f in end_flags: c.op('SetFlag', f)
        return
    if disguise:
        c.op('ScrCmd_452', disguise, 0)
        msg(c, t[first])
        for n in FLICKER:
            c.op('ScrCmd_453'); c.op('ScrCmd_452', cry_species, 0); c.op('Wait', n, VAR_RESULT)
            c.op('ScrCmd_453'); c.op('ScrCmd_452', disguise, 0); c.op('Wait', n, VAR_RESULT)
        c.op('FadeScreen', 6, 1, 0, FADE_WHITE); c.op('WaitFade')
        c.op('ScrCmd_453'); c.op('ScrCmd_452', cry_species, 0)
        c.op('PlayCry', cry_species, 0)
        c.op('FadeScreen', 6, 1, 1, FADE_WHITE); c.op('WaitFade')
    else:
        msg(c, t[first])
        c.op('FadeScreen', 6, 1, 0, FADE_WHITE); c.op('WaitFade')
        c.op('PlayCry', cry_species, 0)
        c.op('FadeScreen', 6, 1, 1, FADE_WHITE); c.op('WaitFade')
        c.op('ScrCmd_452', cry_species, 0)
    c.op('NPCMsg', t[cry_text]); c.op('WaitCry'); c.op('WaitButton'); c.op('CloseMsg')
    msg(c, t[oak_text])
    c.op('ScrCmd_453')

# ---------------- starters (Oak's lab, script 738) ----------------
# var 0x8004 holds the chosen ball's species (1 Bulbasaur, 4 Charmander, 25 Pikachu). Bulbasaur and
# Pikachu share the giving code at 3907..3944 (GiveMon at 3930); Charmander uses 4029..4078 (GiveMon at 4064).
# The ball keeps showing Pikachu/Bulbasaur; the real species is given, revealed, then 0x8004 is switched
# to it so the nickname prompt names it. Later movement checks are moved to the new values.
def starters(ctx):
    t = {k: ctx.add_text(444, v) for k, v in texts.STARTERS.items()}
    assert max(t.values()) < 256
    s = ctx.script(738)
    s.set_arg(4002, 'CompareVarToValue', 1, 492, 1)    # Bulbasaur-ball movement now keyed on Shaymin
    s.set_arg(4230, 'CompareVarToValue', 1, 381, 25)   # Pikachu-ball movement now keyed on Latios
    s.at(3930, 'GiveMon'); s.at(3944, 'BufferSpeciesName'); s.at(4064, 'GiveMon'); s.at(4078, 'BufferSpeciesName')

    # Overworld flicker: hidden objects (flag 1106, set while the starter is chosen) beside the player.
    def ow_sprite(sp): return struct.unpack_from('<H', ctx.narc('data/pokemon_overworld_info.narc')[sp])[0] + 428
    pk = add_obj(ctx, 457, ow_sprite(25), 0, 7, 4, copy_y_from=12, move=0, flag=LAB_HIDE)
    la = add_obj(ctx, 457, ow_sprite(381), 0, 7, 4, copy_y_from=12, move=0, flag=LAB_HIDE)
    bu = add_obj(ctx, 457, ow_sprite(1), 0, 10, 4, copy_y_from=12, move=0, flag=LAB_HIDE)
    sh = add_obj(ctx, 457, ow_sprite(492), 0, 10, 4, copy_y_from=12, move=0, flag=LAB_HIDE)
    def shared_block(base):          # Pikachu or Bulbasaur ball
        c = Code(base)
        c.op('SetFlag', F_PEWTER_TRUE)   # every path passes here or charmander_block: keeps Pewter's true forms hidden
        c.op('CompareVarToValue', 0x8004, 1); c.goto_if(1, 'shaymin')
        give_mon_ex(c, 381, 5)
        reveal(c, t, 'flicker', 381, 'latios_cry', 'latios_oak', ow=(pk, LAB_HIDE, la, LAB_HIDE, True, [LAB_HIDE]))
        c.op('SetVar', 0x8004, 381); c.goto_abs(3944)
        c.label('shaymin')
        give_mon_ex(c, 492, 5)
        reveal(c, t, 'bloom', 492, 'shaymin_cry', 'shaymin_oak', ow=(bu, LAB_HIDE, sh, LAB_HIDE, True, [LAB_HIDE]))
        c.op('SetVar', 0x8004, 492); c.goto_abs(3944)
        return c.build()
    def charmander_block(base):      # special-attacker Charmander: Timid, Solar Flare (ability slot 1), 31 IVs
        c = Code(base)
        c.op('SetFlag', F_PEWTER_TRUE)
        give_mon_ex(c, 4, 5, nature=NATURE['Timid'], ability_slot=1)
        for i, mv in enumerate((871, 406, 108, 45)):   # Torch Song, Dragon Pulse, Smokescreen, Growl
            c.op('SetMonMove', 0, i, mv)
        c.goto_abs(4078)
        return c.build()
    a = s.append_code(shared_block); s.goto_at(3930, 14, a)
    b = s.append_code(charmander_block); s.goto_at(4064, 14, b)
    ctx.log.append('script 738: starter reveal blocks at %d / %d' % (a, b))

# ---------------- story ----------------
def apply(ctx):
    for b, i, old, new in texts.EDITS: ctx.edit_text(b, i, old, new)
    mira = {k: ctx.add_text(439, v) for k, v in texts.MIRA.items()}
    theo = {k: ctx.add_text(445, v) for k, v in texts.THEO.items()}
    assert max(theo.values()) < 256 and max(mira.values()) < 256

    starters(ctx)

    ctx.script(733).set_arg(1086, 'SetVar', 1, 225, 236)   # Light Ball -> Soul Dew
    s = ctx.script(751)   # Pewter PC: shiny Charmander
    s.replace_buffer_with_setvar(514, VAR_SHINY, 0x8000 | 4)
    s.set_arg(522, 'GiveMon', 0, VAR_SHINY, 4)
    s.set_arg(501, 'HidePerson', 0, SHINY_OBJ_ID, 13)
    s = ctx.script(183)   # Route 5 house: shiny Darkrai
    s.set_arg(149, 'PlayCry', 0, 491, 1)
    s.set_arg(240, 'BufferSpeciesName', 1, 491, 1)
    s.replace_buffer_with_setvar(260, VAR_SHINY, 0x8000 | 491)
    s.set_arg(268, 'GiveMon', 0, VAR_SHINY, 1)
    s.set_arg(236, 'HidePerson', 0, SHINY_OBJ_ID, 7)
    s = ctx.script(179)   # Route 5 raid scene
    for pc in (322, 1057, 1315, 1351): s.set_arg(pc, 'PlayCry', 0, 491, 1)
    for pc in (1047, 1080, 1134, 1329, 1341, 2368, 2411): s.set_arg(pc, 'ApplyMovement', 0, SHINY_OBJ_ID, 0)
    for pc in (1405, 2480): s.set_arg(pc, 'HidePerson', 0, SHINY_OBJ_ID, 0)
    s = ctx.script(170)   # Route 2 roadside Charmander
    for pc in (829, 845, 901, 966, 1960, 1976, 2032, 2097, 2123, 2139, 2195, 2260):
        s.set_arg(pc, 'ApplyMovement', 0, SHINY_OBJ_ID, 3)

    # Ranger Mira (Pallet Town) / Theo (Viridian City)
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
    mira_scr = ctx.script(733).append_script(mira_code)
    theo_scr = ctx.script(739).append_script(theo_code)
    ctx.log.append('new scripts: Mira = Pallet script %d, Theo = Viridian script %d' % (mira_scr, theo_scr))

    edit_obj(ctx, 370, 3, newid=SHINY_OBJ_ID, shiny=True)                 # Route 2 Charmander
    edit_obj(ctx, 428, 13, newid=SHINY_OBJ_ID, shiny=True)                # Pewter PC Charmander
    edit_obj(ctx, 10, 0, sprite=973, newid=SHINY_OBJ_ID, shiny=True)      # Route 5 raid: Darkrai
    edit_obj(ctx, 469, 7, sprite=973, newid=SHINY_OBJ_ID, shiny=True)     # Route 5 house: Darkrai
    add_obj(ctx, 46, 69, mira_scr, 1032, 379, copy_y_from=6)       # Pallet shore
    add_obj(ctx, 47, 345, theo_scr, 1050, 258, copy_y_from=18)     # east Viridian

    only = os.environ.get('STORY_ONLY')
    for name in SUBMODULES:
        if only and name not in only.split(','): continue
        try: mod = importlib.import_module(name)
        except ModuleNotFoundError as e:
            if e.name == name: continue
            raise
        mod.apply(ctx)
