import sys, pickle, capstone, struct
bins = pickle.load(open(sys.argv[1],'rb'))
name, start, end = sys.argv[2], int(sys.argv[3],16), int(sys.argv[4],16)
ram, d = bins[name]
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
off = start-ram
for ins in md.disasm(d[off:end-ram], start):
    extra=''
    if ins.mnemonic=='ldr' and '[pc' in ins.op_str:
        imm = int(ins.op_str.split('#')[-1].rstrip(']'),16) if '#' in ins.op_str else 0
        a = ((ins.address+4)&~3)+imm
        extra = '  ; =0x%x' % struct.unpack_from('<I', d, a-ram)[0]
    print('%08x: %-8s %s%s' % (ins.address, ins.mnemonic, ins.op_str, extra))
