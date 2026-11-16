# Route 28 house (script file 224, text bank 365): the Lucario hermit senses the aura of a Riolu/Lucario in your
# party, tells the Aura Guardian legend and teaches it Nasty Plot for free (once). Afterwards (or with no
# Riolu/Lucario) he goes on to his usual Meteor Mash-for-a-Lure-Ball offer.
from patch import Code

SCRIPT, BANK = 224, 365
HOOK = 79                  # PlaySE 1500 / LockAll / FacePlayer (8 bytes), then NPCMsg 6 at 87
NASTY_PLOT = 417
F_TAUGHT = 2616
RIOLU, LUCARIO = 447, 448
V_I, V_SP, V_N, V_MOVE, V_CNT, V_SLOT = 0x8000, 0x8001, 0x8002, 0x8003, 0x8004, 0x8005
V_CHOICE = 0x800C

TEXTS = {
    'sense': "Hm? Wait...\\rThat {0101:0} of yours...\\nI can feel its aura from here.\\rIt is the aura of a true\\nAura Guardian.",
    'legend': "Long ago, a knight and his Lucario\\nguarded a castle with their aura.\\rWhen war came, the Lucario’s master\\nsealed it away to keep it safe,\\fand went alone to stop the fighting.\\rIt’s said the master’s aura still\\nlives on in every Lucario that\\fchooses a Trainer of its own.\\rYour {0101:0} has chosen you.",
    'offer': "A calm mind is the source of aura.\\nLet me teach it Nasty Plot.\\rIt sharpens the will before the\\nstrike. Shall I teach it?",
    'four': "{0101:0} already knows four moves.\\nWhich one should it forget?",
    'learned': "{0101:0} learned Nasty Plot!",
    'after': "Guard your Trainer well,\\n{0101:0}.\\rAnd you, look after it.\\nAura answers aura.",
    'later': "Come back when you are ready.\\nIts aura will not fade.",
}

def apply(ctx):
    s = ctx.script(SCRIPT)
    s.at(HOOK, 'PlaySE'); s.at(HOOK + 8, 'NPCMsg')
    t = {k: ctx.add_text(BANK, v) for k, v in TEXTS.items()}
    assert max(t.values()) < 256

    def build(base):
        c = Code(base)
        c.op('PlaySE', 1500); c.op('LockAll'); c.op('FacePlayer')
        c.op('CheckFlag', F_TAUGHT); c.goto_if(1, 'normal')
        # find the first Riolu/Lucario in the party
        c.op('GetPartyCount', V_N); c.op('SetVar', V_I, 0)
        c.label('loop')
        c.op('CompareVarToVar', V_I, V_N); c.goto_if(4, 'normal')         # i >= count: none
        c.op('GetPartyMonSpecies', V_I, V_SP)
        c.op('CompareVarToValue', V_SP, RIOLU); c.goto_if(1, 'found')
        c.op('CompareVarToValue', V_SP, LUCARIO); c.goto_if(1, 'found')
        c.op('AddVar', V_I, 1); c.goto('loop')
        c.label('found')
        c.op('CopyVar', V_SLOT, V_I)
        c.op('BufferPartyMonNick', 0, V_SLOT)
        c.op('NPCMsg', t['sense']); c.op('WaitButton')
        c.op('PlayCry', LUCARIO, 0); c.op('WaitCry')
        c.op('NPCMsg', t['legend']); c.op('WaitButton')
        c.op('NPCMsg', t['offer']); c.op('TouchscreenMenuHide'); c.op('GetMenuChoice', V_CHOICE)
        c.op('CloseMsg'); c.op('TouchscreenMenuShow')
        c.op('CompareVarToValue', V_CHOICE, 0); c.goto_if(5, 'later')
        c.op('CountMonMoves', V_CNT, V_SLOT)
        c.op('CompareVarToValue', V_CNT, 3); c.goto_if(2, 'full')          # > 3 moves: pick one to forget
        c.op('SetMonMove', V_SLOT, V_CNT, NASTY_PLOT); c.goto('learned')
        c.label('full')
        c.op('NPCMsg', t['four']); c.op('WaitButton'); c.op('CloseMsg')
        c.op('FadeScreen', 6, 1, 0, 0); c.op('WaitFade')
        c.op('PokemonSummaryScreen', 1, V_SLOT, NASTY_PLOT); c.op('GetMoveSelection', 1, V_MOVE)
        c.op('RestoreOverworld'); c.op('FadeScreen', 6, 1, 1, 0); c.op('WaitFade')
        c.op('CompareVarToValue', V_MOVE, 4); c.goto_if(1, 'later')        # cancelled
        c.op('SetMonMove', V_SLOT, V_MOVE, NASTY_PLOT)
        c.label('learned')
        c.op('SetFlag', F_TAUGHT)
        c.op('NPCMsg', t['learned']); c.op('PlayFanfare', 1184); c.op('WaitFanfare')
        c.op('GetPartyMonSpecies', V_SLOT, V_SP); c.op('PlayCry', V_SP, 0); c.op('WaitCry')
        c.op('NPCMsg', t['after']); c.op('WaitButton'); c.op('CloseMsg')
        c.op('ReleaseAll'); c.op('End')
        c.label('later')
        c.op('NPCMsg', t['later']); c.op('WaitButton'); c.op('CloseMsg')
        c.op('ReleaseAll'); c.op('End')
        c.label('normal')
        c.goto_abs(HOOK + 8)
        return c.build()
    s.goto_at(HOOK, 8, s.append_code(build))
    ctx.log.append('hermit: Riolu/Lucario -> Aura Guardian legend + Nasty Plot (script 224 @%d, flag %d)' % (HOOK, F_TAUGHT))
