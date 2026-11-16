# Charmander path (flag 1287): Blaine's Heat Rock.
# Cinnabar Gym (script 15, bank 51): after the Volcano Badge and the Fire Blast TM, Blaine notices the starter
# draws its fire from the sun and gives a Heat Rock (item 284). Ability sun (Solar Flare uses Drought's
# handler) lasts 5 turns, 8 when the holder has a Heat Rock (ov14 0x223AB80, item id passed by the handler).
# Blaine names the first Charmander-line Pokemon in the party by species; if it is the lead, its flame
# blazes first (cry + line). With none in the party he says "your starter". The badge flow runs once: no new flag.
from patch import Code, msg
from story_reshiram import find_charmander_line, flame_if_lead, F_CHAR

BLAINE, BANK = 15, 51
HOOK = 1517            # SetVar 0x8004 365 / SetVar 0x8005 1 / CallStd 2033 (16 bytes; Fire Blast TM), then 1533
BACK = 1533
HEAT_ROCK = 284

_REST = "\\rThen take this Heat Rock. I dug it\\nout of the crater after the eruption.\\rWhen your partner calls out the sun,\\nthis rock keeps it blazing longer!"
T = {
    'lead': "Blaine: Whoa-ho! Look at {0101:2}!\\nIts tail flame is blazing like a\\ftiny sun!",
    'give': "Blaine: Your {0100:1}’s fire comes\\nstraight from the sun, doesn’t it?" + _REST,
    'give_any': "Blaine: Your starter’s fire comes\\nstraight from the sun, doesn’t it?" + _REST,
}

def apply(ctx):
    t = {k: ctx.add_text(BANK, v) for k, v in T.items()}
    assert max(t.values()) < 256, t
    s = ctx.script(BLAINE)
    s.at(HOOK, 'SetVar'); s.at(HOOK + 6, 'SetVar'); s.at(HOOK + 12, 'CallStd'); s.at(BACK, 'NPCMsg')
    def tail(base):
        c = Code(base)
        c.op('SetVar', 0x8004, 365); c.op('SetVar', 0x8005, 1); c.op('CallStd', 2033)
        c.op('CheckFlag', F_CHAR); c.goto_if(0, 'out')
        c.op('CloseMsg')
        find_charmander_line(c, 'bl', 'generic')
        flame_if_lead(c, 'bl', t['lead'])
        c.op('NPCMsg', t['give']); c.op('WaitButton'); c.goto('rock')
        c.label('generic'); c.op('NPCMsg', t['give_any']); c.op('WaitButton')
        c.label('rock')
        c.op('SetVar', 0x8004, HEAT_ROCK); c.op('SetVar', 0x8005, 1); c.op('CallStd', 2033)
        c.label('out'); c.goto_abs(BACK)
        return c.build()
    s.goto_at(HOOK, 16, s.append_code(tail))
    ctx.log.append('script 15 @%d: Charmander path -> Blaine gives Heat Rock after Fire Blast (texts 51.%d-%d)' % (HOOK, t['lead'], t['give_any']))
