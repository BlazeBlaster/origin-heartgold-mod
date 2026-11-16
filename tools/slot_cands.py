# Shortlist slot candidates: unobtainable, not in hack dex list (a/0/7/4[12]), no trainer use, no evo links, no form slots.
import sys, os, struct, pickle, re
sys.path.insert(0, os.path.dirname(__file__))
from lugia_common import Rom, ROOT
r = Rom(); bins = pickle.load(open(os.path.join(ROOT,'rom','bins.pkl'),'rb'))
N = pickle.load(open(os.path.join(ROOT,'rom','msgs.pkl'),'rb'))[232]
dexlist = set(struct.unpack('<781H', r.narc('a/0/7/4')[12]))
formnames = set(N[1026:])
rows = []
for l in open(os.path.join(ROOT,'slot','unobtainable.txt'), encoding='utf-8'):
    s = int(l.split()[0]); t = int(re.search(r'trainers=(\d+)', l).group(1))
    evo = "evo_from=[] evo_to=[]" in l
    rows.append((s, N[s], s in dexlist, t, evo, N[s] in formnames))
def lit(v):
    c32 = c16 = 0
    for n,(ram,d) in bins.items():
        c32 += sum(1 for i in range(0,len(d)-3,4) if struct.unpack_from('<I',d,i)[0]==v)
        c16 += d.count(struct.pack('<H',v))
    return c32, c16
print('NOT in hack dex list, no trainer, no evo, no forms:')
for s,n,inl,t,evo,f in rows:
    if not inl and t==0 and evo and not f:
        print('  %4d %-11s lit32/u16=%s' % (s, n, lit(s)))
print('in dex list but my scan says unobtainable:', [(s,n) for s,n,inl,*_ in rows if inl])
print('not in dex list, with forms or evos:', [(s,n) for s,n,inl,t,evo,f in rows if not inl and (f or not evo)])
