# Darkrai questline "The Shadow of Route 5" + Riolu questline "A Heart That Can Be Seen".
# Flags 2620-2639: 2620 Darkrai joined, 2622 Hypno dealt with (reward given), 2623 Riolu joined,
#                  2629 = never set (used to disable the old Growlithe branch).
# Scripts: 179 (Route 5 raid, bank 322), 183 (shelter house, bank 326), 197 (Route 11, bank 339).
#
# Every starter path now runs the Bulbasaur-branch objects/flags (Darkrai); the Growlithe branch is dead code:
#  - raid: a prefix block un-hides the Darkrai object (obj 0 / flag 1037) and hides the Growlithe one (obj 3 / flag 1038)
#  - every `CheckFlag 1288` in 183/197 is rewritten to flag 106 (always set after the starter)
import re
from patch import Code, msg, OP
from scr import C
from mod_story import (edit_obj, give_mon_ex, NATURE, F_SHINY, F_IV31, SHINY_OBJ_ID)

F_JOINED, F_HYPNO, F_RIOLU, F_NEVER = 2620, 2622, 2623, 2629
DARKRAI, RIOLU, HYPNO = 491, 447, 97
RIOLU_SPRITE = 921          # pokemon_overworld_info[447] + 428
SWABLU_SPRITE = 794
DUSK_BALL = 13

def T(s):
    return s.replace('|', '\\n').replace('#', '\\r').replace('~', '\\f')

def check(t):
    for seg in re.split(r'\\[nrf]', t):
        assert len(seg.replace('{0103:0}', '12345678')) <= 42, (len(seg), seg)
    return t

def sweep(ctx, banks):
    for b in banks:
        strs = ctx.bank(b)
        for i, s in enumerate(strs):
            n = s.replace('Swablu', 'Riolu').replace('Bulbasaur', 'Darkrai').replace('Growlithe', 'Darkrai')
            if n != s: strs[i] = n

def replace_args(ctx, f, name, argi, old, new):
    s = ctx.script(f)
    for pc, v in sorted(s.ins.items()):
        if C[v[0]][0] == name and v[1][argi] == old:
            s.set_arg(pc, name, argi, new, old)

# ---------------- texts ----------------
B322 = {   # Route 5 raid
    0: "Little lady, do you have any idea how|rare that Riolu next to you is?",
    2: "What Pokémon doesn’t get hurt in|battle?#Hand it over and I’ll train it right.#It’ll learn to fight without ever|flinching at pain.",
    3: "If you want a Riolu, find your own.|Stop eyeing the Pokémon here!",
    4: "No can do. A Riolu that senses Auras|is a rare find.#Not putting it to work for Team Rocket|would be a total waste.",
    5: "Darkrai steps forward, eyes glowing.#Darkrai: Kraaai!",
    7: "A shadow with glowing eyes? Ha! You’ve|got guts. I’ll take you too.#All right, Mightyena. Knock all these|Pokémon flat!",
    9: "Riolu! Run! Run as far away as you|can! Don’t let these crooks catch you!",
    10: "Riolu: Rio...",
    11: "This is no time for hesitating or|goodbyes! Run!",
    12: "Aw, shit! It bolted?!#The Riolu I had in the bag, just|gone?!#Damn troublemaking woman.#That shadow put Mightyena in a|nightmare, but it looks worn out too.#Mightyena, snap out of it and bite it|till it drops!",
    14: "Darkrai: Krai...",
    16: "Heh heh, the shadow’s done for.|Go, Poké Ball!",
    18: "Darkrai!",
    21: "Riolu...#Darkrai...#Sob... sob...",
    29: "Thank you for stepping in. I don’t even|want to think what would’ve happened...#Darkrai only wanted to protect us. But|the town will blame it for this...#I’m taking the little ones back inside|now. Drop by if you have time.",
    33: "Riolu: Ri-o!",
    35: "Darkrai: Dark-raaai!",
    37: "It showed up one night, all alone, and|never left.#Now it stays up till dawn, guarding the|other Pokémon.#Folks in town say it gives them|nightmares. I don’t believe it.",
}
NIGHTMARE = "Mightyena: Migh-ye...!#Darkrai’s eyes flash! Mightyena|collapses, lost in a nightmare!"

B326 = {   # shelter house
    8: "Darkrai is really grateful for your|help that day.#Please don’t be afraid of it.|Every night it guards the Pokémon here~while they sleep.#People in town say it gives them|nightmares, but it can’t help that.#Its dreams spill out when it’s upset.|It never means to hurt anyone.#Since that day, it keeps blaming itself|for not protecting Riolu.#Lately it’s tried to go off alone to look|for Riolu several times.#I’m not a Trainer, so I don’t dare take|it out on a journey.#But you saved it. Would you take it|along on your travels?#And maybe ask around about Riolu, so|Darkrai won’t blame itself so much.",
    28: "Riolu: Ri-o!",
}
H = {
    'intro': "{0103:0}! Thank goodness you came.#The nightmares didn’t stop when|Darkrai left with you.#Now I understand. It was never the|cause. It was keeping something away.#Tonight I can feel it again... a heavy,|sweet mist seeping under the door!",
    'mist': "The mist thickens. Two eyes glint in|the dark...#A Hypno steps out of the shadows,|its pendulum swaying!",
    'cry': "Hypno: Hyp-noooo...",
    'fight': "It feeds on dreams! This is what|Darkrai was fighting off all along!",
    'after': "The mist faded away. The shelter is|quiet and peaceful again.#The Pokémon are sleeping soundly.|No more nightmares tonight.",
    'apology': "I’m so sorry. I let everyone blame|Darkrai, and I feared it too.#Some townsfolk saw it all from the road.|They are on their way to apologise.#Please tell Darkrai thank you from all|of us. And take these, please!",
    'end': "Those are Dusk Balls. They work best|in the dark of night.#Please look after Darkrai, and Riolu|too if you find it.",
    'rv': "Oh! Riolu is with you now?#It looks so happy next to Darkrai.|They really do understand each other.#Thank you. Please keep them both safe.",
}

B339 = {   # Route 11
    4: "Yes, yes! I’ve always dreamed of having|a Riolu, especially one with fur~as soft as this one’s.#As it happens, I’ve got a lively Spearow|right here. How about trading it for~your Riolu?",
    63: "Riolu: Ri-o!",
    64: "Wait, isn’t this the Riolu that belongs|to the girl in the house on Route 5?!#It’s staring at your party. Talk to|the girl about it?",
    91: "Is Riolu doing well? It’s so lonely|playing here by myself...",
}
R = {
    's1': "Please, could you ask that lady if I|can keep looking after Riolu?",
    's2': "Riolu suddenly perks up!#It’s staring at {0103:0}’s party,|trembling as if it feels something.",
    's3': "Riolu dashes over and nuzzles the Poké|Ball that holds Darkrai!",
    's4': "Darkrai: Kraaai...#It sounds gentle and warm.",
    's5': "Riolu has never been this happy with|anyone else!#That’s the shadow the whole town|fears? Darkrai?#But Riolu can feel hearts. It knows|that Pokémon is kind.",
    's6': "{0103:0}: Darkrai only wanted to protect|the shelter.#People blamed it for the nightmares|and for Team Rocket. They were wrong.",
    's7': "Then I’ll tell everyone in town. I’ll|tell them Riolu is never wrong!#Riolu... if you want to go with it, I|understand.",
    'y1': "Go on, Riolu. You and Darkrai are going|to be the best of friends.#Please take good care of it. I’ll be|waiting here, and I’ll tell everyone!",
    'joined': "Riolu joined {0103:0}’s team!",
    'y2': "Riolu... be brave. I’ll never forget|you!",
    'full': "Your party is full! Make room|for Riolu, then come back.",
}

RIOLU_MOVES = (410, 399, 98, 203)   # Vacuum Wave, Dark Pulse, Quick Attack, Endure

def apply(ctx):
    for d in (B322, B326, B339, H, R): [check(T(v)) for v in d.values()]
    check(T(NIGHTMARE))

    # ---- texts ----
    sweep(ctx, (322, 326, 339))
    for b, d in ((322, B322), (326, B326), (339, B339)):
        for i, t in d.items(): ctx.set_text(b, i, T(t))
    t_night = ctx.add_text(322, T(NIGHTMARE))
    h = {k: ctx.add_text(326, T(v)) for k, v in H.items()}
    r = {k: ctx.add_text(339, T(v)) for k, v in R.items()}
    assert t_night < 256 and max(h.values()) < 256 and max(r.values()) < 256

    # Rumours: Cerulean City (bank 460) and the Route 5 gatehouse (bank 325)
    ctx.set_text(460, 76, T("I keep having the same nightmare lately.#A dark shape with glowing eyes stares|at me... near the shelter on Route 5.#My neighbours all dream it too. It|can’t be a coincidence..."))
    ctx.set_text(460, 79, T("They say a shadow with glowing eyes|lurks near the Pokémon shelter on Route 5.#Ever since it showed up, half the town|can’t sleep. Stay away from there!"))
    ctx.set_text(325, 0, T("Travelers coming through here all say|the same thing. Nobody’s sleeping well.#They blame a shadow with glowing eyes|near the shelter on Route 5.#I hope it’s only a rumour..."))
    for b, i in ((460, 76), (460, 79), (325, 0)): check(ctx.bank(b)[i])

    # ---- Riolu sprite / cries ----
    for eb, oid in ((10, 7), (10, 10), (16, 0), (469, 4)):
        edit_obj(ctx, eb, oid, sprite=RIOLU_SPRITE)
    for f in (179, 183, 197): replace_args(ctx, f, 'PlayCry', 0, 333, RIOLU)

    # ---- every path -> Darkrai branch ----
    for f in (183, 197): replace_args(ctx, f, 'CheckFlag', 0, 1288, 106)

    # ===== script 179: Route 5 raid =====
    s = ctx.script(179)
    s.set_arg(1036, 'CheckFlag', 0, F_NEVER, 1037)                  # never take the Growlithe branch
    s.set_arg(1123, 'NPCMsg', 0, t_night, 8)                        # Mightyena falls into a nightmare
    mv = s.at(1047, 'ApplyMovement')[1]
    def pre(base):
        c = Code(base)
        c.op('CheckFlag', 1037); c.goto_if(0, 'go')
        c.op('ClearFlag', 1037); c.op('ShowPerson', SHINY_OBJ_ID); c.op('HidePerson', 3); c.op('SetFlag', 1047)
        c.label('go')
        c.op('ApplyMovement', SHINY_OBJ_ID, 1055 + mv[1] - (c.pc() + 8))
        c.goto_abs(1055)
        return c.build()
    s.goto_at(1047, 8, s.append_code(pre))

    # ===== script 183: shelter house =====
    s = ctx.script(183)
    # give shiny, IV31 Darkrai Lv15
    def give(base):
        c = Code(base)
        c.op('GetPartyCount', 0x8005)
        give_mon_ex(c, DARKRAI, 15, flags=F_SHINY | F_IV31)
        c.op('SetFlag', F_JOINED)
        c.goto_abs(282)
        return c.build()
    s.at(268, 'GiveMon')
    s.goto_at(260, 22, s.append_code(give))
    # granddaughter: Hypno event / Riolu-with-you line / original chain
    s.at(79, 'GoToIf'); s.at(86, 'CheckFlag'); s.at(90, 'GoToIf')
    def gd(base):
        c = Code(base)
        c.labels['L647'] = 647; c.labels['L658'] = 658
        c.op('CheckFlag', F_JOINED); c.goto_if(0, 'orig')
        c.op('CheckFlag', F_HYPNO); c.goto_if(1, 'after')
        c.op('BufferPlayersName', 0)
        msg(c, h['intro']); msg(c, h['mist'])
        c.op('PlayCry', HYPNO, 0); c.op('NPCMsg', h['cry']); c.op('WaitCry'); c.op('WaitButton'); c.op('CloseMsg')
        msg(c, h['fight'])
        c.op('WildBattle', HYPNO, 20, 0)
        c.op('CheckBattleWon', 0x800C); c.op('CompareVarToValue', 0x800C, 0); c.goto_if(1, 'lost')
        msg(c, h['after']); msg(c, h['apology'])
        c.op('SetVar', 0x8004, DUSK_BALL); c.op('SetVar', 0x8005, 10); c.op('CallStd', 2033)
        c.op('SetFlag', F_HYPNO)
        msg(c, h['end']); c.op('ReleaseAll'); c.op('End')
        c.label('lost'); c.op('WhiteOut'); c.op('ReleaseAll'); c.op('End')
        c.label('after'); c.op('CheckFlag', F_RIOLU); c.goto_if(0, 'orig')
        msg(c, h['rv']); c.op('ReleaseAll'); c.op('End')
        c.label('orig')
        c.op('CheckFlag', 1451); c.goto_if(1, 'L647')
        c.op('CheckFlag', 1048); c.goto_if(0, 'L658')
        c.goto_abs(97)
        return c.build()
    s.goto_at(79, 18, s.append_code(gd))

    # ===== script 197: Route 11 =====
    s = ctx.script(197)
    s.at(2841, 'GenderMsgBox'); s.at(2849, 'NPCMsg'); s.at(2875, 'ApplyMovement')
    def sense(base):
        c = Code(base)
        c.op('BufferPlayersName', 0)
        msg(c, r['s1']); msg(c, r['s2']); msg(c, r['s3'])
        c.op('PlayCry', RIOLU, 0); c.op('WaitCry')
        c.op('PlayCry', DARKRAI, 0); c.op('NPCMsg', r['s4']); c.op('WaitCry'); c.op('WaitButton'); c.op('CloseMsg')
        msg(c, r['s5']); msg(c, r['s6']); msg(c, r['s7'])
        c.goto_abs(2849)
        return c.build()
    s.goto_at(2841, 8, s.append_code(sense))
    def take(base):
        c = Code(base)
        c.op('BufferPlayersName', 0)
        c.op('GetPartyCount', 0x8005); c.op('CompareVarToValue', 0x8005, 6); c.goto_if(1, 'full')
        msg(c, r['y1'])
        c.op('PlayCry', RIOLU, 0)
        c.op('NPCMsg', r['joined']); c.op('PlayFanfare', 1187); c.op('WaitFanfare'); c.op('WaitButton'); c.op('CloseMsg')
        give_mon_ex(c, RIOLU, 10, NATURE['Timid'], F_IV31, 0)
        c.op('GetPartyCount', 0x8006); c.op('SubVar', 0x8006, 1)
        for i, mvid in enumerate(RIOLU_MOVES): c.op('SetMonMove', 0x8006, i, mvid)
        c.op('SetFlag', 1160); c.op('HidePerson', 0); c.op('SetFlag', 1445); c.op('SetFlag', F_RIOLU)
        msg(c, r['y2']); c.op('ReleaseAll'); c.op('End')
        c.label('full'); msg(c, r['full']); c.op('ReleaseAll'); c.op('End')
        return c.build()
    s.goto_at(2875, 8, s.append_code(take))
    ctx.log.append('story_darkrai: done (flags 2620 joined, 2622 hypno, 2623 riolu, 2629 never)')
