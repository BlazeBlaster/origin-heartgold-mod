import pickle, sys, re
sys.path.insert(0, 'tools')
from scr import *
scr = pickle.load(open('rom/scripts.pkl', 'rb')); msgs = pickle.load(open('rom/msgs.pkl', 'rb'))
f = int(sys.argv[1]); bank = int(sys.argv[2]) if len(sys.argv) > 2 else None
ent, ins = disasm(scr[f]); targets = {t for (_, _, _, t) in ins.values() if t is not None}
for pc in sorted(ins):
    op, a, n, t = ins[pc]
    if pc in ent: print('\n== script %d' % (ent.index(pc)+1))
    elif pc in targets: print('  L%d:' % pc)
    name = C.get(op, ['?%d' % op])[0]
    s = '    %5d %s %s' % (pc, name, a)
    if t is not None: s += ' -> L%d' % t
    if bank is not None and re.search('msg|message|yesno|menu', name, re.I):
        for x in a:
            if isinstance(x, int) and x < len(msgs[bank]):
                s += '  <<%s>>' % msgs[bank][x][:150]; break
    print(s)
