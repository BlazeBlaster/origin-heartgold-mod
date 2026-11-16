# Ilex Forest (script 52, bank 81): on the Shaymin path (flag 1289) the shrine Shaymin is your
# starter's family; instead of joining it gives you a Gracidea.
from patch import Code

F_SHAYMIN = 1289
GRACIDEA = 466
SCRIPT, BANK = 52, 81
HOOK = 2645            # PlayCry [492, 0] (6 bytes), right before NPCMsg 110 at 2651

TEXT = ("Shaymin: Shaaa-min!\\rYour Shaymin and the wild Shaymin\\n"
        "touch noses happily.\\fIt seems they’re from the same\\n"
        "flower field!\\rShaymin wants to stay in the forest,\\n"
        "but it brought you a gift.")

def apply(ctx):
    s = ctx.script(SCRIPT)
    s.at(HOOK, 'PlayCry'); s.at(HOOK + 6, 'NPCMsg')
    t = ctx.add_text(BANK, TEXT); assert t < 256
    def build(base):
        c = Code(base)
        c.op('PlayCry', 492, 0)
        c.op('CheckFlag', F_SHAYMIN)
        c.goto_if(1, 'reunion')
        c.goto_abs(HOOK + 6)
        c.label('reunion')
        c.op('NPCMsg', t); c.op('WaitButton'); c.op('CloseMsg')
        c.op('SetVar', 0x8004, GRACIDEA); c.op('SetVar', 0x8005, 1)
        c.op('CallStd', 2033); c.op('WaitButton'); c.op('CloseMsg')
        c.op('SetFlag', 1366); c.op('SetFlag', 2296)
        c.op('HidePerson', 13)
        c.op('ReleaseAll'); c.op('End')
        return c.build()
    s.goto_at(HOOK, 6, s.append_code(build))
    ctx.log.append('ilex: Shaymin path -> Gracidea reunion (script 52 @%d, text 81.%d)' % (HOOK, t))
