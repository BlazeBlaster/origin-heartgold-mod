import sys, os, pickle
sys.path.insert(0, os.path.dirname(__file__))
from ohg import *
rom, h = load(sys.argv[1]); files = fnt_files(rom, h)
ents, _ = narc_parse(fat(rom, h, files['a/0/2/7']))
out = {}
for b, d in enumerate(ents):
    try:
        strs, seed = msg_decode(d); out[b] = [chars_to_str(c) for c in strs]
    except Exception as e: out[b] = ['ERR %s' % e]
pickle.dump(out, open('rom/msgs.pkl', 'wb'))
with open('rom/msgs.txt', 'w', encoding='utf-8') as f:
    for b, ss in out.items():
        for i, s in enumerate(ss): f.write('%d.%d\t%s\n' % (b, i, s))
print(len(ents))
