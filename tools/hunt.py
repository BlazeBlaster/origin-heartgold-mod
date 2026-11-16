import sys, pickle, capstone, struct
bins = pickle.load(open(sys.argv[1],'rb'))
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
for name in ['arm9']+[k for k in bins if k!='arm9']:
    ram,d = bins[name]
    ins=[]
    off=0
    while off < len(d)-1:
        got=False
        for i in md.disasm(d[off:off+4], ram+off, 1):
            ins.append((i.address,i.mnemonic,i.op_str)); off+=i.size; got=True
        if not got: off+=2
    for k in range(len(ins)-12):
        win = ins[k:k+14]
        s=[m+' '+o for _,m,o in win]
        if 'movs r1, #5' in s and 'movs r1, #0x4c' in s:
            i5=s.index('movs r1, #5'); i4=s.index('movs r1, #0x4c')
            if i5<i4 and i4+2<len(s) and any(x.startswith('bl ') for x in s[i5+1:i5+3]) and any(x.startswith('bl ') for x in s[i4+1:i4+3]):
                print(name, hex(win[0][0]), ' | '.join(s))
