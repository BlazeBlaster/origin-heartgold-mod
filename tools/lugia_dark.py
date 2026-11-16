import struct, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from lugia_common import to555
H = lambda s: tuple(int(s[i:i+2], 16) for i in (0, 2, 4))
def save(name, cols): open('lugia/'+name, 'wb').write(struct.pack('<16H', *[to555(H(c)) for c in cols]))
# battle: 0 transp,1-5 body light->shadow,6 outline,7-10 belly,11-12 eyes/mouth,13-15 spines
save('battle_shadowC.bin', ['83e68b','6a6280','554d6a','453d58','383048','29223a','101010','3a2f62','2c2450','1f1a3c','141028','ff3a6a','b4103c','2e1e3e','1f1229','140a1a'])
save('battle_shadowD.bin', ['83e68b','4e4862','3d374f','2f2a40','252033','1a1626','101010','2a1f4a','201838','16102a','0e0a1c','ff2050','a00830','3a2458','271640','180c28'])
# follower: 1 body shadow,2 body light,4 accent mid,6 accent darkest,8 accent dark,9 accent light,13 outline,14 body darkest,15 body highlight
M = 'ff08ff'
save('follower_shadowC.bin', ['c5bd9c','3d3550','554d6a',M,'24163a',M,'0e0816',M,'1c1029','352a55',M,M,M,'000000','241e30','6a6280'])
save('follower_shadowD.bin', ['c5bd9c','2c2840','3d374f',M,'2a1a48',M,'0c0612',M,'1c1030','3a2458',M,M,M,'000000','1a1626','4e4862'])
# E: matches the user's reference - navy body, pale grey-blue plates/fins, red-orange eyes
save('battle_shadowE.bin', ['83e68b','6a6aa8','52528e','404078','31315f','22224a','101010','c5cde6','a4b4d5','8394b4','62738b','ff4a20','c0101a','c5cde6','94a4c5','6a7b9c'])
save('follower_shadowE.bin', ['c5bd9c','31315f','4a4a85',M,'a4b4d5',M,'62738b',M,'8394b4','d5deee',M,M,M,'000000','202045','6a6aa8'])
# F: colors sampled directly from the user's reference image
save('battle_shadowF.bin', ['83e68b','585893','4f4f87','46467a','363660','272749','0b0b0b','9c1010','d9e4f9','b6c5e1','899bbc','f72b27','d24400','d9e4f9','b6c5e1','a1b1d1'])
save('follower_shadowF.bin', ['c5bd9c','363660','46467a',M,'a1b1d1',M,'566889',M,'899bbc','cddaf2',M,M,M,'000000','272749','585893'])
