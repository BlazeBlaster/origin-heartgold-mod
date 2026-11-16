# Dump a script (with its texts) from any built ROM: python tools/vdump.py <rom> <script> <bank> [from] [to]
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from patch import Rom
from ohg import narc_parse, msg_decode, chars_to_str
from scr import disasm, C
r = Rom(sys.argv[1]); f, b = int(sys.argv[2]), int(sys.argv[3])
lo = int(sys.argv[4]) if len(sys.argv) > 4 else 0; hi = int(sys.argv[5]) if len(sys.argv) > 5 else 1 << 30
sc = narc_parse(r.get(r.files['a/0/1/2']))[0][f]
txt = [chars_to_str(c) for c in msg_decode(narc_parse(r.get(r.files['a/0/2/7']))[0][b])[0]]
ent, ins = disasm(sc)
for pc in sorted(ins):
    if lo <= pc <= hi:
        op, a, n, t = ins[pc]; name = C[op][0]
        extra = '  <<%s>>' % txt[a[0]][:90] if name == 'NPCMsg' and a[0] < len(txt) else ''
        print('%6d %s %s%s%s' % (pc, name, a, ' -> %d' % t if t is not None else '', extra))
