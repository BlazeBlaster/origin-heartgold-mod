# Charmander path (flag 1287): Reshiram, the late payoff.
#  1. Lavender (script 769, bank 471): after Mr. Fuji gives the Mystery Stone, he also gives the Light Stone.
#     If the lead is the Charmander line, its tail flame flickers at the stone first.
#  2. Cerulean Cave lake bottom (script 912, bank 599), after the Charizardite moment (every Charmander-path
#     player reaches pc 5554): with the Light Stone, the follower steps forward, the stone burns, Reshiram rises
#     and tests you in a Lv 95 battle that can't be caught (a one-Pokemon "trainer" like the hack's Articuno, #505).
#     Lose -> the white flame restores your team and it battles again. Win -> it joins (shiny, IVs 31, Modest,
#     Turboblaze, Blue Flare / Dragon Pulse / Earth Power / Extrasensory). Party full -> it goes back into the
#     Light Stone and Mr. Fuji calls it out later.
import struct
from patch import Code, msg
from mod_story import give_mon_ex, NATURE, F_SHINY, F_IV31

F_CHAR = 1287
RESHIRAM, LEVEL = 643, 95
LIGHT_STONE = 750
TRAINER = 1024                 # appended trainer id (defeat flag 1360 + 1024 = 2384, unused)
TEMPLATE = 505                 # the hack's Articuno legend battle
MOVES = (551, 406, 414, 326)   # Blue Flare, Dragon Pulse, Earth Power, Extrasensory
F_DONE, F_PENDING = 2617, 2618
V_T, V_SLOT = 0x8008, 0x8009
FADE_WHITE = 0x7FFF

FUJI, FUJI_BANK = 769, 471
FUJI_START, FUJI_END = 701, 769     # 701 PlaySE/LockAll/FacePlayer (8 bytes); 769 CloseMsg + SetFlag 1571 (6)
LAKE, LAKE_BANK = 912, 599
LAKE_HOOK = 5554                    # ApplyMovement [255 -> 5800] (8 bytes), then WaitMovement at 5562
LAKE_PLAYER_MV = 5800
FOLLOWER_STEP = 7396                # the follower movement the lake scene uses before the Mystery Stone reacts

FUJI_T = {
    'lead': "Mr. Fuji: Oh? {0101:2}’s tail flame\\nflickered when it saw this stone...",
    'give': "Mr. Fuji: Then you should have this\\none as well. It’s an old white stone\\fthat has never once felt warm.\\rPerhaps your {0100:1}’s flame can\\nwake whatever sleeps inside it.",
    'give_any': "Mr. Fuji: Then you should have this\\none as well. It’s an old white stone\\fthat has never once felt warm.\\rPerhaps your partner’s flame can\\nwake whatever sleeps inside it.",
    'full': "Mr. Fuji: The Light Stone is calling\\nout... but you have no room in your\\fparty for what’s inside right now.",
    'release': "Mr. Fuji: The white flame inside the\\nLight Stone wants to come out...\\rLet me help it.",
    'joined': "{0103:0} received Reshiram!",
}
LAKE_T = {
    'hot': "The Light Stone in the Bag is\\nburning hot!",
    'flame': "{0101:1}’s tail flame is\\nburning white!",
    'rise': "Something huge is rising from the\\ndepths, drawn to the white flame!",
    'cry': "???: Rrrrshi-raaaam!",
    'reveal': "It’s Reshiram! The white dragon\\nof truth!\\rIt’s staring straight at you...\\nIt wants to test your bond!",
    'lose': "Reshiram’s flames die down...\\nIt is still waiting for you.\\rThe white flame restored your\\nPokémon!",
    'win': "Reshiram folds its great wings...\\rIt has seen the truth in your\\nheart and accepted you!",
    'joined': "{0103:0} received Reshiram!",
    'full': "Your party is full...\\rReshiram returned into the Light\\nStone. Mr. Fuji might know how to\\fcall it out again.",
}

def give_reshiram(c, t):
    give_mon_ex(c, RESHIRAM, LEVEL, nature=NATURE['Modest'], flags=F_SHINY | F_IV31, ability_slot=0)
    c.op('GetPartyCount', V_SLOT); c.op('SubVar', V_SLOT, 1)
    for i, mv in enumerate(MOVES): c.op('SetMonMove', V_SLOT, i, mv)
    c.op('TakeItem', LIGHT_STONE, 1, V_T)
    c.op('BufferPlayersName', 0)
    c.op('NPCMsg', t['joined']); c.op('PlayFanfare', 1189); c.op('WaitFanfare'); c.op('WaitButton'); c.op('CloseMsg')

def lead_is_charmander_line(c, no_label):
    c.op('GetPartyMonSpecies', 0, V_T)
    c.op('CompareVarToValue', V_T, 4); c.goto_if(1, 'is_' + no_label)
    c.op('CompareVarToValue', V_T, 5); c.goto_if(1, 'is_' + no_label)
    c.op('CompareVarToValue', V_T, 6); c.goto_if(1, 'is_' + no_label)
    c.goto(no_label)
    c.label('is_' + no_label)

V_N = 0x800A
def find_charmander_line(c, tag, none_label):
    """First Charmander/Charmeleon/Charizard in the party: V_SLOT = its slot, V_T = its species, and its species
    name in buffer 1. Jumps to none_label if the party has none."""
    c.op('GetPartyCount', V_N)
    for i in range(6):
        c.op('CompareVarToValue', V_N, i); c.goto_if(3, none_label)      # count <= i: no more slots
        c.op('GetPartyMonSpecies', i, V_T); c.op('SetVar', V_SLOT, i)
        for sp in (4, 5, 6):
            c.op('CompareVarToValue', V_T, sp); c.goto_if(1, tag + '_found')
    c.goto(none_label)
    c.label(tag + '_found')
    c.op('BufferSpeciesName', 1, V_T, 0, 0)

def flame_if_lead(c, tag, msg_idx):
    """After find_charmander_line: if it's the lead, cry + msg_idx (nickname in buffer 2)."""
    c.op('CompareVarToValue', V_SLOT, 0); c.goto_if(5, tag + '_nolead')
    c.op('BufferPartyMonNick', 2, 0)
    c.op('PlayCry', V_T, 0); msg(c, msg_idx); c.op('WaitCry')
    c.label(tag + '_nolead')

def add_trainer(ctx):
    td, tp = ctx.narc('a/0/5/5'), ctx.narc('a/0/5/6'); names = ctx.bank(719)
    assert len(td) == len(tp) == len(names) == TRAINER, (len(td), len(tp), len(names))
    d = bytearray(td[TEMPLATE]); assert d[3] == 1
    p = bytearray(tp[TEMPLATE]); assert len(p) == 28 and struct.unpack_from('<H', p, 8)[0] == 144
    p[3] = NATURE['Modest']
    struct.pack_into('<HHHH', p, 4, 163, LEVEL, RESHIRAM, 0)       # Turboblaze, level, species, no item
    struct.pack_into('<4H', p, 12, *MOVES)
    td.append(bytes(d)); tp.append(bytes(p)); names.append(compressed('Reshiram'))

def compressed(text):
    # trainer names are stored compressed (0xF100, then 9-bit chars packed 15 bits per u16, ended by 0x1FF;
    # a final word made only of terminator bits is dropped), and the battle intro reads them that way
    from patch import str_to_chars, chars_to_str
    chars = [ch for ch in str_to_chars(text) if ch != 0xFFFF] + [0x1FF]
    bits = n = 0; words = []
    for ch in chars:
        bits |= ch << n; n += 9
        while n >= 15: words.append(bits & 0x7FFF); bits >>= 15; n -= 15
    if n:
        last = (bits | (0x7FFF << n)) & 0x7FFF
        if last != 0x7FFF: words.append(last)
    return chars_to_str([0xF100] + words + [0xFFFF])

def apply(ctx):
    add_trainer(ctx)
    ft = {k: ctx.add_text(FUJI_BANK, v) for k, v in FUJI_T.items()}
    lt = {k: ctx.add_text(LAKE_BANK, v) for k, v in LAKE_T.items()}
    assert max(ft.values()) < 256 and max(lt.values()) < 256

    # ---- Mr. Fuji: Light Stone (after the Mystery Stone), and releasing a pending Reshiram
    s = ctx.script(FUJI)
    s.at(FUJI_START, 'PlaySE'); s.at(FUJI_START + 8, 'HasItem'); s.at(FUJI_END, 'CloseMsg'); s.at(FUJI_END + 2, 'SetFlag')
    def fuji_start(base):
        c = Code(base)
        c.op('PlaySE', 1500); c.op('LockAll'); c.op('FacePlayer')
        c.op('CheckFlag', F_PENDING); c.goto_if(0, 'normal')
        c.op('GetPartyCount', V_T); c.op('CompareVarToValue', V_T, 6); c.goto_if(1, 'full')
        msg(c, ft['release'])
        c.op('FadeScreen', 6, 1, 0, FADE_WHITE); c.op('WaitFade'); c.op('PlayCry', RESHIRAM, 0)
        c.op('FadeScreen', 6, 1, 1, FADE_WHITE); c.op('WaitFade'); c.op('WaitCry')
        give_reshiram(c, ft)
        c.op('ClearFlag', F_PENDING); c.op('ReleaseAll'); c.op('End')
        c.label('full'); msg(c, ft['full']); c.op('ReleaseAll'); c.op('End')
        c.label('normal'); c.goto_abs(FUJI_START + 8)
        return c.build()
    def fuji_end(base):
        c = Code(base)
        c.op('CloseMsg'); c.op('SetFlag', 1571)
        c.op('CheckFlag', F_CHAR); c.goto_if(0, 'out')
        find_charmander_line(c, 'fj', 'generic')
        flame_if_lead(c, 'fj', ft['lead'])
        c.op('NPCMsg', ft['give']); c.op('WaitButton'); c.goto('stone')
        c.label('generic'); c.op('NPCMsg', ft['give_any']); c.op('WaitButton')
        c.label('stone')
        c.op('SetVar', 0x8004, LIGHT_STONE); c.op('SetVar', 0x8005, 1); c.op('CallStd', 2033); c.op('CloseMsg')
        c.label('out'); c.op('ReleaseAll'); c.op('End')
        return c.build()
    s.goto_at(FUJI_START, 8, s.append_code(fuji_start))
    s.goto_at(FUJI_END, 6, s.append_code(fuji_end))

    # ---- Cerulean Cave lake bottom: Reshiram awakens
    s = ctx.script(LAKE)
    s.at(LAKE_HOOK, 'ApplyMovement'); s.at(LAKE_HOOK + 8, 'WaitMovement')
    def lake(base):
        c = Code(base)
        c.op('CheckFlag', F_CHAR); c.goto_if(0, 'back')
        c.op('CheckFlag', F_DONE); c.goto_if(1, 'back')
        c.op('HasItem', LIGHT_STONE, 1, V_T); c.op('CompareVarToValue', V_T, 0); c.goto_if(1, 'back')
        msg(c, lt['hot'])
        c.op('ApplyMovement', 253, FOLLOWER_STEP - (c.pc() + 8)); c.op('WaitMovement')
        lead_is_charmander_line(c, 'noflame')
        c.op('BufferPartyMonNick', 1, 0)
        c.op('PlayCry', V_T, 0); msg(c, lt['flame']); c.op('WaitCry')
        c.label('noflame')
        for _ in range(3):
            c.op('ScreenShake', 0, 2, 10, 6); c.op('Wait', 12, V_T)
        msg(c, lt['rise'])
        c.op('FadeScreen', 6, 1, 0, FADE_WHITE); c.op('WaitFade')
        c.op('ScrCmd_452', RESHIRAM, 0); c.op('PlayCry', RESHIRAM, 0)
        c.op('FadeScreen', 6, 1, 1, FADE_WHITE); c.op('WaitFade')
        c.op('NPCMsg', lt['cry']); c.op('WaitCry'); c.op('WaitButton'); c.op('CloseMsg')
        msg(c, lt['reveal'])
        c.op('ScrCmd_453')
        c.label('battle')
        c.op('TrainerBattle', TRAINER, 0, 0, 0)
        c.op('CheckBattleWon', V_T); c.op('CompareVarToValue', V_T, 0); c.goto_if(5, 'won')    # != 0: won
        c.op('HealParty'); msg(c, lt['lose']); c.goto('battle')
        c.label('won')
        c.op('SetFlag', F_DONE)
        c.op('ScrCmd_452', RESHIRAM, 0); msg(c, lt['win']); c.op('ScrCmd_453')
        c.op('GetPartyCount', V_T); c.op('CompareVarToValue', V_T, 6); c.goto_if(1, 'full')
        give_reshiram(c, lt); c.goto('back')
        c.label('full'); msg(c, lt['full']); c.op('SetFlag', F_PENDING)
        c.label('back')
        c.op('ApplyMovement', 255, LAKE_PLAYER_MV - (c.pc() + 8))
        c.goto_abs(LAKE_HOOK + 8)
        return c.build()
    s.goto_at(LAKE_HOOK, 8, s.append_code(lake))
    ctx.log.append('reshiram: trainer %d, Fuji Light Stone (769 @%d/@%d), lake scene (912 @%d), flags %d/%d'
                   % (TRAINER, FUJI_START, FUJI_END, LAKE_HOOK, F_DONE, F_PENDING))
