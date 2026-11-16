import sys, pickle, struct
bins = pickle.load(open(sys.argv[1],'rb'))
for name,(ram,d) in bins.items():
    for i in range(0,len(d)-7,4):
        a,b = struct.unpack_from('<II',d,i)
        if (a,b)==(0x59f,0x1ea) or (a==0x59f and 0x1ea in struct.unpack_from('<4I',d,i+4) if i+20<len(d) else False):
            print(name, hex(ram+i))
