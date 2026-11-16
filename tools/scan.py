import sys, struct, os
sys.path.insert(0, os.path.dirname(__file__))
from nds import *
rom,h = load(sys.argv[1])
print({k:hex(v) for k,v in h.items()}, "title", rom[0:12], rom[0xC:0x10])
arm9 = rom[h['arm9_off']:h['arm9_off']+h['arm9_size']]
print("arm9 size", len(arm9))
ovs = overlays(rom,h); print("overlays", len(ovs))
