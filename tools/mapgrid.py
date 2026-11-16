import sys,struct,json
sys.path.insert(0,'tools')
from ohg import *
rom,h=load('rom/ohg.nds'); files=fnt_files(rom,h)
mats,_=narc_parse(fat(rom,h,files['a/0/4/1'])); land,_=narc_parse(fat(rom,h,files['a/0/6/5']))
ev,_=narc_parse(fat(rom,h,files['a/0/3/2']))
m=mats[0]; w,hh,hasH,hasA,nl=struct.unpack_from('<5B',m,0); o=5+nl
hdr=struct.unpack_from('<%dH'%(w*hh),m,o) if hasH else None; o+= 2*w*hh if hasH else 0
o+= w*hh if hasA else 0
ld=struct.unpack_from('<%dH'%(w*hh),m,o)
def perm(x,z):
    cx,cz=x//32,z//32; lid=ld[cz*w+cx]
    if lid==0xFFFF: return None
    d=land[lid]; p=struct.unpack_from('<H',d,0x10+((z%32)*32+(x%32))*2)[0]
    return p
def objs(eb):
    d=ev[eb]; nbg=struct.unpack_from('<I',d,0)[0]; o=4+nbg*20; n=struct.unpack_from('<I',d,o)[0]; o+=4
    return [struct.unpack_from('<14H',d,o+i*32) for i in range(n)]
if __name__=='__main__':
    eb=int(sys.argv[1]); x0,x1,z0,z1=map(int,sys.argv[2:6])
    ob={(f[12],f[13]):f[0] for f in objs(eb)}
    print('w,h',w,hh)
    print('     '+''.join('%d'%(x%10) for x in range(x0,x1)))
    for z in range(z0,z1):
        row=''
        for x in range(x0,x1):
            if (x,z) in ob: row+= chr(ord('A')+ob[(x,z)]%26); continue
            p=perm(x,z)
            if p is None: row+=' '; continue
            blocked=p>>8 &0x80; beh=p&0xFF
            row+= '#' if blocked else ('~' if beh in (0x10,0x11,0x12,0x13,0x15,0x16,0x19,0x22) else ('"' if beh in (2,3,4) else '.'))
        print('%4d '%z+row)
