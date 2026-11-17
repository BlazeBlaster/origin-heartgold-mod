# Story module: abandoned-Pokemon event (Route 2 -> Pewter PC) on every starter path, and the Route 9 Squirtle quest/gift
# on every path.  Flags used: 2610 (Route 2 Pikachu-costume object hidden), 2611 (Pewter PC Pikachu-costume object hidden),
# 2613 (Pewter PC dumper hidden; was shared with Route 2 object via flag 1367).  Vars: 0x4200 disguise species, 0x4201 object id.
import struct
from patch import Code, msg
from mod_story import (edit_obj, add_obj, objs_off, give_mon_ex, reveal, NATURE, F_SHINY, F_IV31, RANDOM, F_PEWTER_TRUE)

F_ROUTE2_B, F_PEWTER_B, F_DUMPER = 2610, 2611, 2613
V_SP, V_OBJ = 0x4200, 0x4201
ID_A, ID_B = 230, 231            # Charmander-costume object / Pikachu-costume object (shiny clone sprites; ids >= 0xF0 are dropped on map load)
SPR_PIKACHU = 453

T456 = {
    'dump_pika': "My {0100:1} is garbage.\\nIt couldn’t even touch Brock’s Onix,\\fand it just looks creepy. Look at that\\fcolor!\\rThe best way to deal with garbage like\\nthat is to dump it by the road...\\r...and trick it into thinking I’ll come\\nback for it, so it waits there till it\\fdies. Ha ha ha ha!",
    'z_flicker': "...Huh?\\nThe Charmander’s outline is\\fflickering strangely...",
    'z_cry': "???: Zoooo-ruaaa!",
    'z_nurse': "Nurse Joy: Oh my! That’s no Charmander!\\rIt’s a Zorua, the Tricky Fox Pokémon!\\rZorua can cast illusions that make it\\nlook like another Pokémon.\\rIts Trainer only wanted a Charmander,\\nso it kept up the disguise day and night.\\rEven after Brock’s Gym crushed it, it\\nwaited by the road as a Charmander.\\rNurse Joy: But it dropped the illusion\\nfor you, {0103:0}.\\rThat must mean it trusts you. Please\\ntake good care of it!",
    'm_flicker': "...Huh?\\nSomething is stirring beneath the\\fPikachu’s costume...",
    'm_cry': "???: Mi... Mimi... kyuuu!",
    'm_nurse': "Nurse Joy: Oh my... That’s no Pikachu!\\rIt’s a Mimikyu, the Disguise Pokémon.\\rIt wears a rag stitched to look like a\\nPikachu because it wants to be loved.\\rBut its Trainer thought it was creepy,\\nand it couldn’t even touch Brock’s Onix.\\rNurse Joy: It showed you its true self,\\n{0103:0}.\\rAll it ever wanted was to be loved.\\nPlease take good care of it!",
}

def _set_obj_flag(ctx, eb, oid, flag):
    en = ctx.narc('a/0/3/2'); d = bytearray(en[eb]); o, n = objs_off(d)
    for i in range(n):
        p = o + 4 + i*32
        if struct.unpack_from('<H', d, p)[0] == oid:
            struct.pack_into('<H', d, p+8, flag); en[eb] = bytes(d)
            ctx.log.append('event %d obj %d flag -> %d' % (eb, oid, flag)); return
    raise KeyError((eb, oid))

def _disguise(c, tag):
    """Charmander-costume on the Bulbasaur/Shaymin and Pikachu paths, Pikachu-costume on the Charmander path.
    Sets V_SP (species shown) and V_OBJ (map object id)."""
    c.op('CheckFlag', 1288); c.goto_if(1, tag + 'c')
    c.op('CheckFlag', 1289); c.goto_if(1, tag + 'c')
    c.op('SetVar', V_SP, 25); c.op('SetVar', V_OBJ, ID_B); c.goto(tag + 'd')
    c.label(tag + 'c')
    c.op('SetVar', V_SP, 4); c.op('SetVar', V_OBJ, ID_A)
    c.label(tag + 'd')

def _pewter_flag(c, tag, name):
    """SetFlag/ClearFlag on the Pewter PC object's hide flag (1360 for the Charmander costume, 2611 for the Pikachu one)."""
    c.op('CheckFlag', 1288); c.goto_if(1, tag + 'c')
    c.op('CheckFlag', 1289); c.goto_if(1, tag + 'c')
    c.op(name, F_PEWTER_B); c.goto(tag + 'e')
    c.label(tag + 'c'); c.op(name, 1360)
    c.label(tag + 'e')

def apply(ctx):
    # ---------------- texts ----------------
    b314 = ctx.bank(314)
    for i in (2, 36, 37, 38, 39, 40, 41, 42, 43, 45, 46, 47, 50, 52, 53):
        assert 'Charmander' in b314[i], i
        b314[i] = b314[i].replace('Charmander', '{0100:1}')
    b314[2] = "{0100:1}: ..."
    b314[53] = "{0100:1}: ...!\\r{0100:1} is overjoyed!"
    b314[36] = b314[36].replace("’s scales are an odd\\ngolden color...", "’s coloring is odd and\\nstrangely bright...")
    b314[52] = b314[52].replace("What lovely golden scales...", "What lovely coloring...")
    assert 'golden' not in b314[36] and 'golden' not in b314[52], (b314[36], b314[52])
    b456 = ctx.bank(456)
    for i in (17, 18, 19, 20, 21):
        assert 'Charmander' in b456[i], i
        b456[i] = b456[i].replace('Charmander', '{0100:1}')
    b456[17] = b456[17].replace("Its scales\\nare some freaky gold color, and it\\fcouldn’t", "Its color\\nis some freaky shade, and it\\fcouldn’t")
    b456[18] = b456[18].replace("’s shiny golden scales\\nsparkle.", "’s shiny coloring\\nsparkles.")
    assert 'gold' not in b456[17] and 'gold' not in b456[18], (b456[17], b456[18])
    t = {k: ctx.add_text(456, v) for k, v in T456.items()}
    assert max(t.values()) < 256

    # ---------------- map objects ----------------
    # Route 2 (event 370): Charmander-costume object keeps flag 1367; add the Pikachu-costume object (shown on the Charmander path)
    b = add_obj(ctx, 370, SPR_PIKACHU, 3, 1026, 136, copy_y_from=ID_A, move=17, flag=F_ROUTE2_B)
    edit_obj(ctx, 370, b, newid=ID_B, shiny=True)
    # Pewter PC (event 428): same, plus the dumper gets its own hide flag (it shared 1367 with the Route 2 object)
    b = add_obj(ctx, 428, SPR_PIKACHU, 11, 9, 13, copy_y_from=ID_A, move=15, flag=F_PEWTER_B)
    edit_obj(ctx, 428, b, newid=ID_B, shiny=True)
    _set_obj_flag(ctx, 428, 12, F_DUMPER)
    # true forms for the overworld flicker, same tile, hidden by F_PEWTER_TRUE (set in Oak's lab on every path)
    oi = ctx.narc('data/pokemon_overworld_info.narc')
    z_obj = add_obj(ctx, 428, struct.unpack_from('<H', oi[570])[0] + 428, 11, 9, 13, copy_y_from=ID_A, move=15, flag=F_PEWTER_TRUE)
    edit_obj(ctx, 428, z_obj, shiny=True)
    m_obj = add_obj(ctx, 428, struct.unpack_from('<H', oi[778])[0] + 428, 11, 9, 13, copy_y_from=ID_A, move=15, flag=F_PEWTER_TRUE)
    edit_obj(ctx, 428, m_obj, shiny=True)

    # ---------------- Viridian Forest script 115: event on every path ----------------
    s = ctx.script(115)
    def x_block(base):       # non-Pikachu paths (replaces pcs 5759..5782, then continues at the original GoToIf on flag 1287)
        c = Code(base)
        c.op('SetFlag', 1360); c.op('ClearFlag', 1347); c.op('SetFlag', 1057); c.op('SetFlag', 1349)
        c.op('SetFlag', F_PEWTER_B); c.op('ClearFlag', F_DUMPER)
        c.op('CheckFlag', 1289); c.goto_if(1, 'char')
        c.op('SetFlag', 1367); c.op('ClearFlag', F_ROUTE2_B); c.goto('done')     # Charmander path: Pikachu costume
        c.label('char'); c.op('ClearFlag', 1367); c.op('SetFlag', F_ROUTE2_B)     # Shaymin path: Charmander costume
        c.label('done'); c.op('CheckFlag', 1287); c.goto_abs(5783)
        return c.build()
    def y_block(base):       # Pikachu path (replaces pcs 6988..6995; 6984 already cleared 1367)
        c = Code(base)
        c.op('ClearFlag', 1349); c.op('SetFlag', F_ROUTE2_B); c.op('SetFlag', F_PEWTER_B); c.op('ClearFlag', F_DUMPER)
        c.op('ReleaseAll'); c.op('End')
        return c.build()
    s.at(5759, 'SetFlag'); s.at(5779, 'CheckFlag'); s.at(5783, 'GoToIf'); s.at(6984, 'ClearFlag'); s.at(6988, 'ClearFlag')
    s.goto_at(5759, 24, s.append_code(x_block))
    s.goto_at(6988, 8, s.append_code(y_block))

    # ---------------- Route 2 script 170: the roadside scene + the Pewter PC cutscene ----------------
    s = ctx.script(170)
    ins = dict(s.ins)       # original disassembly (pcs are unchanged by in-place edits)
    for pc in sorted(ins):
        op_a = ins[pc]
        from scr import C
        nm, a = C[op_a[0]][0], op_a[1]
        if not (787 <= pc < 3030): continue
        if nm == 'PlayCry' and a[0] == 4: s.set_arg(pc, 'PlayCry', 0, V_SP)
        elif nm in ('ApplyMovement', 'MovePersonFacing') and a[0] in (3, 13): s.set_arg(pc, nm, 0, V_OBJ)
    s.at(105, 'PlayCry'); s.at(2290, 'ClearFlag'); s.at(2294, 'Warp'); s.at(2330, 'ScrCmd_109')
    s.at(2630, 'SetFlag'); s.at(2634, 'TrainerBattle'); s.at(3013, 'ClearFlag')
    def start_hook(base):    # PlayCry [4] at the start of the Route 2 interaction
        c = Code(base)
        _disguise(c, 'a')
        c.op('BufferSpeciesName', 1, V_SP, 0, 0); c.op('PlayCry', V_SP, 0); c.goto_abs(111)
        return c.build()
    def warp_block(base):    # ClearFlag 1360 + Warp: show the right Pewter object, hide both Route 2 objects
        c = Code(base)
        _pewter_flag(c, 'p', 'ClearFlag')
        c.op('SetFlag', 1367); c.op('SetFlag', F_ROUTE2_B)
        c.raw(bytes(s.d[2294:2306])); c.goto_abs(2306)
        return c.build()
    def battle_block(base):  # SetFlag 1360 + TrainerBattle
        c = Code(base)
        _pewter_flag(c, 'q', 'SetFlag')
        c.raw(bytes(s.d[2634:2642])); c.goto_abs(2642)
        return c.build()
    def end_block(base):     # ClearFlag 1360 + ReleaseAll + End
        c = Code(base)
        _pewter_flag(c, 'r', 'ClearFlag')
        c.op('ReleaseAll'); c.op('End')
        return c.build()
    def rebuffer(base):      # after the warp: make sure buffer 1 still holds the costume species
        c = Code(base)
        c.op('BufferSpeciesName', 1, V_SP, 0, 0); c.raw(bytes(s.d[2330:2336])); c.goto_abs(2336)
        return c.build()
    wb = bytes(s.d[2294:2306]); bb = bytes(s.d[2634:2642]); rb = bytes(s.d[2330:2336])   # copied before overwriting
    s.goto_at(105, 6, s.append_code(start_hook))
    s.goto_at(2290, 16, s.append_code(warp_block))
    s.goto_at(2330, 6, s.append_code(rebuffer))
    s.goto_at(2630, 12, s.append_code(battle_block))
    s.goto_at(3013, 8, s.append_code(end_block))
    ctx.log.append('script 170: costume species/object vars 0x%X/0x%X, Pewter flag branches at 2290/2630/3013' % (V_SP, V_OBJ))

    # ---------------- Pewter PC script 751 ----------------
    s = ctx.script(751)
    s.at(415, 'PlaySE'); s.at(438, 'PlaySE'); s.at(487, 'BufferSpeciesName'); s.at(514, 'BufferSpeciesName'); s.at(522, 'GiveMon'); s.at(536, 'NPCMsg')
    def dumper(base):
        c = Code(base)
        c.op('PlaySE', 1500); c.op('LockAll'); c.op('FacePlayer')
        _disguise(c, 'a')
        c.op('BufferSpeciesName', 1, V_SP, 0, 0)
        c.op('CompareVarToValue', V_SP, 25); c.goto_if(1, 'pika')
        c.op('NPCMsg', 17); c.goto_abs(426)
        c.label('pika'); c.op('NPCMsg', t['dump_pika']); c.goto_abs(426)
        return c.build()
    def talk(base):
        c = Code(base)
        c.op('PlaySE', 1500); c.op('LockAll'); c.op('FacePlayer')
        _disguise(c, 'b')
        c.op('BufferSpeciesName', 1, V_SP, 0, 0); c.goto_abs(446)
        return c.build()
    def blockA(base):        # cry + hide the right object
        c = Code(base)
        c.op('BufferSpeciesName', 1, V_SP, 0, 0); c.op('PlayCry', V_SP, 0)
        c.op('CheckFlag', 1288); c.goto_if(0, 'keep')     # Shaymin/Charmander paths: keep it on the map for the flicker
        c.op('HidePerson', V_OBJ)
        c.label('keep'); c.goto_abs(505)
        return c.build()
    def blockB(base):        # give the real Pokemon (after "X joined your party!"), reveal, then nickname prompt at 536
        c = Code(base)
        c.op('CheckFlag', 1288); c.goto_if(1, 'pika')
        c.op('CheckFlag', 1289); c.goto_if(1, 'zorua')
        give_mon_ex(c, 778, 10, flags=F_SHINY | F_IV31)
        reveal(c, t, 'm_flicker', 778, 'm_cry', 'm_nurse', ow=(ID_B, F_PEWTER_B, m_obj, F_PEWTER_TRUE, False, [F_PEWTER_TRUE]))
        c.op('BufferSpeciesName', 1, 778, 0, 0); c.goto_abs(536)
        c.label('zorua')
        give_mon_ex(c, 570, 10, flags=F_SHINY | F_IV31)
        reveal(c, t, 'z_flicker', 570, 'z_cry', 'z_nurse', ow=(ID_A, 1360, z_obj, F_PEWTER_TRUE, False, [F_PEWTER_TRUE]))
        c.op('BufferSpeciesName', 1, 570, 0, 0); c.goto_abs(536)
        c.label('pika')
        give_mon_ex(c, 4, 10, nature=NATURE['Adamant'], flags=F_SHINY | F_IV31, ability_slot=2)
        for i, mv in enumerate((349, 407, 7, 232)):    # Dragon Dance, Dragon Rush, Fire Punch, Metal Claw
            c.op('SetMonMove', 0x8005, i, mv)          # 0x8005 = party count before the gift = slot of the new Pokemon
        c.op('BufferSpeciesName', 1, 4, 0, 0); c.goto_abs(536)
        return c.build()
    s.goto_at(415, 8, s.append_code(dumper))
    s.goto_at(438, 8, s.append_code(talk))
    s.goto_at(487, 18, s.append_code(blockA))
    s.goto_at(514, 22, s.append_code(blockB))

    # ---------------- Route 9 (script 190): Squirtle quest + gift on every path ----------------
    s = ctx.script(190)
    s.set_arg(120, 'GoToIf', 0, 2, 0)       # 116: was "no Pikachu path -> officer's small talk"; cond '>' never taken
    s.set_arg(168, 'GoToIf', 0, 2, 0)       # 164: was "no Pikachu path -> pick up the item silently"; never taken
    s.set_arg(649, 'GoToIf', 0, 3, 1)       # 645: was "Pikachu path -> offer Squirtle"; cond '<=' always taken (flag result is 0/1)
    ctx.log.append('script 190: 1288 gates at 116/164/645 removed (823 berries/mushrooms shop left as is)')
    # Lum Berry (item 157): vanilla non-Pikachu paths got it from the item ball (pc 1326) and from Squirtle
    # (pc 3284, flag 1542); both are bypassed now, so Squirtle hands it over right after joining (not on the
    # Pikachu path, which never had it). Hook: pc 5800 TouchscreenMenuShow/ReleaseAll/End (6 bytes).
    s.at(5800, 'TouchscreenMenuShow'); s.at(5802, 'ReleaseAll'); s.at(5804, 'End')
    def lum(base):
        c = Code(base)
        c.op('TouchscreenMenuShow')
        c.op('CheckFlag', 1288); c.goto_if(1, 'out')
        c.op('CheckFlag', 1542); c.goto_if(1, 'out')
        c.op('NPCMsg', 68); c.op('WaitButton')          # "Squirtle seems to have something for you."
        c.op('SetVar', 0x8004, 157); c.op('SetVar', 0x8005, 1); c.op('CallStd', 2033); c.op('CloseMsg')
        c.op('SetFlag', 1542)
        c.label('out'); c.op('ReleaseAll'); c.op('End')
        return c.build()
    s.goto_at(5800, 6, s.append_code(lum))
    ctx.log.append('script 190 @5800: Squirtle gives a Lum Berry after joining (non-Pikachu paths, flag 1542)')
