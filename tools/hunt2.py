import sys, pickle, capstone, struct
bins = pickle.load(open(sys.argv[1],'rb'))
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
ram,d = bins['arm9']
ins=[]; off=0
while off < len(d)-1:
    got=False
    for i in md.disasm(d[off:off+4], ram+off, 1):
        ins.append((i.address,i.mnemonic,i.op_str)); off+=i.size; got=True
    if not got: off+=2
for k in range(len(ins)-20):
    s=[m+' '+o for _,m,o in ins[k:k+20]]
    if s[0]=='movs r1, #0xae' and any(x=='movs r1, #5' for x in s[3:20]):
        print(hex(ins[k][0]), ' | '.join(s[:20]))
