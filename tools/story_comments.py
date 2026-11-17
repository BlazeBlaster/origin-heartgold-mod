# Story comments on the disguised starters (Pikachu-ball = Latios, flag 1288; Bulbasaur-ball = Shaymin, flag 1289).
import struct
from patch import Code
from scr import C

F_LATIOS, F_SHAYMIN = 1288, 1289
JUMP_NAMES = ('GoTo', 'Call', 'GoToIf', 'CallIf', 'ObjectGoTo', 'BGGoTo', 'DirectionGoTo', 'GoToIfTrainerDefeated')
MSG_NAMES = ('NPCMsg', 'GenderMsgBox')


def _find_window(s, pc, targets):
    """Choose even-length (>= 6) window of consecutive non-jump instructions containing pc."""
    order = sorted(s.ins)
    ends = {p: p + s.ins[p][2] for p in order}
    def ok(p, first):
        op, a, n, t = s.ins[p]
        if first and C[op][0] in ('GoToIf', 'CallIf'): return True   # replayed with its original target
        return t is None and C[op][0] not in JUMP_NAMES and (first or p not in targets)
    best = None
    for start in order:
        if start > pc: break
        if not ok(start, True): continue
        e = start; chain = [start]
        while ends[e] in s.ins and ok(ends[e], False) and len(chain) < 12:
            e = ends[e]; chain.append(e)
            if e > pc and 6 <= ends[e] - start and (ends[e] - start) % 2 == 0 and pc in chain:
                end = ends[e]
                nxt = s.ins.get(end)
                last = C[s.ins[e][0]][0]
                if nxt and C[nxt[0]][0] in ('GoToIf', 'CallIf') and last.startswith(('Compare', 'Check')): continue
                if nxt and C[nxt[0]][0] in ('GoToIf', 'CallIf'): continue
                if best is None or end - start < best[1] - best[0]: best = (start, end)
                break
        # single-instruction windows are never enough; the loop above grows them
    assert best, ('no window', s.fid, pc)
    return best


def branch_msg(ctx, script, bank, line, alts):
    """Show a different text for flag-selected paths at every NPCMsg (or GenderMsgBox) using `line`.
    line: int, or (male, female) tuple for a GenderMsgBox. alts: {flag: text} (text is a tuple for gender boxes).
    Original line is used when no flag is set. Returns number of places patched."""
    s = ctx.script(script)
    pair = line if isinstance(line, tuple) else None
    new = {fl: [ctx.add_text(bank, x) for x in (t if isinstance(t, tuple) else (t,))] for fl, t in alts.items()}
    assert all(i < 256 for v in new.values() for i in v), 'bank %d too big' % bank
    sites = [pc for pc in sorted(s.ins) if (C[s.ins[pc][0]][0] == 'NPCMsg' and pair is None and s.ins[pc][1][0] == line)
             or (C[s.ins[pc][0]][0] == 'GenderMsgBox' and pair is not None and tuple(s.ins[pc][1]) == pair)]
    assert sites, ('no site', script, line)
    for pc in sites:
        targets = set(s.ent) | {t for (_, _, _, t) in s.ins.values() if t is not None}
        a, b = _find_window(s, pc, targets)
        displaced = sorted(p for p in s.ins if a <= p < b)
        def build(base, displaced=displaced, pc=pc, a=a, b=b):
            c = Code(base); disp = displaced
            if s.ins[disp[0]][3] is not None:     # leading GoToIf/CallIf must run before CheckFlag clobbers the compare
                p = disp[0]; c.labels['ext'] = s.ins[p][3]
                (c.goto_if if C[s.ins[p][0]][0] == 'GoToIf' else c.call_if)(s.ins[p][1][0], 'ext'); disp = disp[1:]
            for fl in new: c.op('CheckFlag', fl); c.goto_if(1, 'f%d' % fl)
            def replay(msgargs):
                for p in disp:
                    if p == pc and msgargs is not None:
                        c.op('NPCMsg' if pair is None else 'GenderMsgBox', *msgargs)
                    else: c.raw(bytes(s.d[p:p + s.ins[p][2]]))
                c.goto_abs(b)
            replay(None)
            for fl, idx in new.items():
                c.label('f%d' % fl); replay(idx)
            return c.build()
        # fix: Code.items need raw bytes before labels resolve; offsets are computed by Code
        target = s.append_code(build)
        s.goto_at(a, b - a, target)
        ctx.log.append('story_comments: script %d window %d..%d branches line %s -> %d' % (script, a, b, line, target))
    return len(sites)


MOM_REST = "\\rOh, that’s right! The running shoes I\\nbought you have arrived!\\r"
MOM_HEAD = "Mom: What a cute Pokémon you got from\\nthe Professor!\\r"
BLUE_HEAD = "Blue: So you got your Pokémon, and a\\nPokédex from Gramps, same as me.\\r"


def apply(ctx):
    branch_msg(ctx, 842, 537, 13, {
        F_LATIOS: MOM_HEAD + "Oh my! Your “Pikachu” just turned\\nblue and floated right off the floor!" + MOM_REST,
        F_SHAYMIN: MOM_HEAD + "Oh my! The flowers in the garden all\\nbloomed the moment you walked in!" + MOM_REST,
    })
    branch_msg(ctx, 736, 442, 0, {
        F_LATIOS: "Daisy: Hello, {0103:0}!\\rGrandpa called me, all worked up! A\\nLatios was hiding among his Pikachu!\\rHowever exciting your travels get, be\\nsure to come home to Pallet Town often!",
        F_SHAYMIN: "Daisy: Hello, {0103:0}!\\rGrandpa called me, all worked up! A\\nShaymin was hiding among his Bulbasaur!\\rHowever exciting your travels get, be\\nsure to come home to Pallet Town often!",
    })
    def blue(mon):
        a = BLUE_HEAD + "Blue: ...A %s?! Gramps never gave\\nME a legend!\\r" % mon
        return (a + "Blue: Hmph! But how good are you as a\\nTrainer? Only one way to find out!",
                a + "Blue: Hmph! Fine! Let’s do what we’ve\\nalways dreamed of... A Pokémon battle!")
    branch_msg(ctx, 738, 444, (69, 76), {F_LATIOS: blue('Latios'), F_SHAYMIN: blue('Shaymin')})
