# Sea Temple thread: Mira (Cerulean) -> Nugget Bridge ranger -> Route 25 cape, baby Shadow Lugia (Lugiling, 716;
# evolves into Shadow Lugia 717, see mod_species). It joins with its own Lv 15 level-up moves.
# Flags 2640-2659: 2640 legend told, 2641 Manaphy heard the sea, 2643 Lugiling joined (hides the cape object).
import re
from patch import Code, msg
from mod_story import (add_obj, give_mon_ex, set_party_ability, reveal, F_EGG, F_SHINY, F_IV31,
                       FADE_WHITE)

F_LEGEND, F_HEARD, F_JOINED = 2640, 2641, 2643
MANAPHY, SLUGIA = 490, 716
LUGIA_SPRITE = 1216          # pokemon_overworld_info[716] + 428: Lugiling (small follower model, mod_species)
AZURE_SKIN = 318
V_RES, V_MANA, V_LUG, V_TMP = 0x800C, 0x8005, 0x8006, 0x8004

CER = {   # Cerulean City, bank 460
 'noegg': "Mira: Sea patrol never ends. The coast\\nis quiet for now.",
 'unhatched': "Mira: Has the Egg hatched yet? Keep it\\nin your party and keep walking.\\rA Manaphy needs warmth and time.",
 'legend': "Mira: A hatched Manaphy! It looks so\\nhappy with you.\\rThe Sea Temple legend says Manaphy\\nwas born to hear every sea.\\rIt may sense the sea calling it now.\\fGo to Nugget Bridge on Route 24.\\rThen try the cape on Route 25.\\nThe sea is loudest there.",
 'wait': "Mira: Nugget Bridge first, then the\\ncape on Route 25.\\rManaphy knows the way. Trust it.",
 'done': "Mira: You calmed that little Lugia?!\\rIts heart is still healing, so be\\ngentle with it.\\rThe sea will always be there for the\\nthree of you.",
}
R24 = {   # Route 24, bank 355
 'plain': "Ranger: This bridge hears everything,\\neven tides from far away.\\rWe Rangers listen for anything\\nstrange.",
 'scene': "Ranger: Hey, is that a Manaphy?!\\rIt’s staring off to the northeast...",
 'cry': "Manaphy: Phyyy!",
 'heard': "Manaphy hears the sea!\\rIt is gazing toward the cape on\\nRoute 25, ears raised.\\rRanger: The sea is calling it.\\nBe careful out there.",
 'after': "Ranger: Your Manaphy is still\\nlistening... The cape on Route 25\\fis calling it.",
}
R25 = {   # Route 25, bank 356
 'no': "A small, dark Pokémon cowers on the\\ncape. Its red eyes burn...\\rYou cannot make your legs move any\\ncloser. Something must guide you.",
 'full': "A dark shape cowers ahead, but your\\nparty is full!\\rMake room for one more, then come\\nback to the cape.",
 'see': "A small dark shape cowers on the\\ncape. Its eyes burn red...\\rIt has noticed you!",
 'cry': "Young Lugia: Gyaaah!",
 'lash': "The young Lugia lashes out in a panic!\\rThe whole cape trembles!",
 'swap': "Manaphy cries out, glowing pale blue.\\rIt used Heart Swap! Its gentle heart\\nflows into the shadowy Pokémon...",
 'calm': "The red glare softens. The young\\nLugia lowers its head.\\rManaphy’s hidden power awakens!\\rManaphy’s Ability became Azure Skin!",
 'join': "The young Lugia wants to travel with\\n{0103:0}!\\rIts heart is still healing, but it\\ntrusts Manaphy... and you.",
 'got': "{0103:0} received Lugiling!",
 'boom': "Manaphy sings with all its might...\\rManaphy learned Boomburst!\\r(It took the place of its last move.)",
 'mira': "Mira’s voice drifts over the waves:\\r“Be gentle with the little one. Its\\nheart is still healing.”",
}

def check(d):
    for k, s in d.items():
        for seg in re.split(r'\\[nrf]', s):
            assert len(seg) <= 38, (k, len(seg), seg)

def flash(c):
    c.op('FadeScreen', 6, 1, 0, FADE_WHITE); c.op('WaitFade')
    c.op('FadeScreen', 6, 1, 1, FADE_WHITE); c.op('WaitFade')

def shake(c, n=3):
    for _ in range(n):
        c.op('Wait', 2, V_TMP); c.op('ScreenShake', 0, 2, 10, 6); c.op('Wait', 10, V_TMP)

def has_manaphy(c, none_label):     # hatched Manaphy in the party, else jump
    c.op('PlayerHasSpecies', V_RES, MANAPHY); c.op('CompareVarToValue', V_RES, 0); c.goto_if(1, none_label)

def apply(ctx):
    for d in (CER, R24, R25): check(d)
    cer = {k: ctx.add_text(460, v) for k, v in CER.items()}
    r24 = {k: ctx.add_text(355, v) for k, v in R24.items()}
    r25 = {k: ctx.add_text(356, v) for k, v in R25.items()}
    assert max(cer.values()) < 256 and max(r24.values()) < 256 and max(r25.values()) < 256

    def mira(base):
        c = Code(base)
        c.op('PlaySE', 1500); c.op('LockAll'); c.op('FacePlayer')
        has_manaphy(c, 'nomana')
        c.op('CheckFlag', F_JOINED); c.goto_if(1, 'done')
        c.op('CheckFlag', F_LEGEND); c.goto_if(1, 'wait')
        msg(c, cer['legend']); c.op('SetFlag', F_LEGEND); c.op('ReleaseAll'); c.op('End')
        c.label('wait'); msg(c, cer['wait']); c.op('ReleaseAll'); c.op('End')
        c.label('done'); msg(c, cer['done']); c.op('ReleaseAll'); c.op('End')
        c.label('nomana'); c.op('CheckFlag', F_EGG); c.goto_if(1, 'egg')
        msg(c, cer['noegg']); c.op('ReleaseAll'); c.op('End')
        c.label('egg'); msg(c, cer['unhatched']); c.op('ReleaseAll'); c.op('End')
        return c.build()

    def ranger(base):
        c = Code(base)
        c.op('LockAll'); c.op('FacePlayer')
        has_manaphy(c, 'plain')
        c.op('CheckFlag', F_LEGEND); c.goto_if(0, 'plain')
        c.op('CheckFlag', F_HEARD); c.goto_if(1, 'after')
        msg(c, r24['scene'])
        c.op('PlayCry', MANAPHY, 0)
        c.op('NPCMsg', r24['cry']); c.op('WaitCry'); c.op('WaitButton'); c.op('CloseMsg')
        msg(c, r24['heard']); c.op('SetFlag', F_HEARD); c.op('ReleaseAll'); c.op('End')
        c.label('after'); msg(c, r24['after']); c.op('ReleaseAll'); c.op('End')
        c.label('plain'); msg(c, r24['plain']); c.op('ReleaseAll'); c.op('End')
        return c.build()

    lugia_obj = []
    def lugia(base):
        c = Code(base)
        c.op('LockAll')
        has_manaphy(c, 'no')
        c.op('CheckFlag', F_HEARD); c.goto_if(0, 'no')
        c.op('GetPartyCount', V_TMP); c.op('CompareVarToValue', V_TMP, 6); c.goto_if(1, 'full')
        c.op('GetPartySlotWithSpecies', V_MANA, MANAPHY)
        c.op('BufferPlayersName', 0)
        msg(c, r25['see'])
        c.op('PlayCry', SLUGIA, 0); c.op('NPCMsg', r25['cry']); c.op('WaitCry'); c.op('WaitButton'); c.op('CloseMsg')
        flash(c); shake(c, 3)
        msg(c, r25['lash'])
        c.op('PlayCry', MANAPHY, 0); c.op('WaitCry')
        msg(c, r25['swap'])
        flash(c)
        set_party_ability(c, V_MANA, AZURE_SKIN)
        msg(c, r25['calm'])
        msg(c, r25['join'])
        give_mon_ex(c, SLUGIA, 15, flags=F_SHINY | F_IV31)
        c.op('NPCMsg', r25['got']); c.op('PlayFanfare', 1200); c.op('WaitFanfare'); c.op('WaitButton'); c.op('CloseMsg')
        c.op('SetMonMove', V_MANA, 3, 586)               # Boomburst replaces Manaphy's 4th move
        msg(c, r25['boom'])
        c.op('SetFlag', F_JOINED); c.op('HidePerson', lugia_obj[0])
        msg(c, r25['mira'])
        c.op('ReleaseAll'); c.op('End')
        c.label('full'); msg(c, r25['full']); c.op('ReleaseAll'); c.op('End')
        c.label('no'); msg(c, r25['no']); c.op('ReleaseAll'); c.op('End')
        return c.build()

    mira_s = ctx.script(756).append_script(mira)
    ranger_s = ctx.script(215).append_script(ranger)
    # the Lugia object must exist first: its id is baked into the script's HidePerson
    n_s = len(ctx.script(216).ent) + 1
    oid = add_obj(ctx, 26, LUGIA_SPRITE, n_s, 1408, 40, copy_y_from=3, move=0, flag=F_JOINED)
    lugia_obj.append(oid)
    got = ctx.script(216).append_script(lugia)
    assert got == n_s, (got, n_s)
    add_obj(ctx, 49, 69, mira_s, 1322, 116, copy_y_from=0)
    add_obj(ctx, 25, 345, ranger_s, 1320, 82, copy_y_from=5)
    ctx.log.append('seatemple: Mira=Cerulean script %d, Ranger=R24 script %d, Lugia=R25 script %d obj %d' % (mira_s, ranger_s, got, oid))
