# Builds proposed Shadow-Lugia palettes (.bin BGR555), a role/target JSON, and a palette swatch sheet.
import os, sys, struct, json
sys.path.insert(0, os.path.dirname(__file__))
from lugia_common import *
from lugia_btx import btx_parse
OUT = os.path.join(ROOT, 'lugia'); os.makedirs(OUT, exist_ok=True)
r = Rom()
pm = r.narc('data/pokepic_m.narc'); pg = r.narc('pbr/pokegra.narc'); ow = r.narc('a/0/8/1')
bn = nclr_colors(pm[1993])[0]; bs = nclr_colors(pm[1997])[0]
_, _, fp = btx_parse(ow[579]); fn0, fn1 = fp[0]['cols'], fp[1]['cols']
for k in ():
    _, _, pp = btx_parse(ow[k]); print('model', k, 'pal0', [bgr555(c) for c in pp[0]['cols'][:10]], '\n   pal1', [bgr555(c) for c in pp[1]['cols'][:10]])

BROLES = ['transparent (keep)', 'body highlight (white)', 'body light', 'body main', 'body mid', 'body shadow',
          'outline (keep)', 'belly plates light', 'belly plates', 'belly plates dark', 'belly plates darkest',
          'mouth/eye bright (orange)', 'eye/mouth dark (red-brown)', 'spines/fins/eye patch light',
          'spines/fins/eye patch mid', 'spines/fins/eye patch dark (navy)']
A = {1:(150,142,166),2:(122,114,142),3:(98,90,120),4:(82,74,104),5:(58,50,76),
     7:(84,76,142),8:(62,54,122),9:(44,38,98),10:(28,24,66),11:(255,70,128),12:(206,28,78),
     13:(74,50,92),14:(50,34,66),15:(32,20,42)}
B = {1:(198,190,214),2:(170,162,190),3:(142,134,166),4:(118,110,146),5:(86,78,110),
     7:(122,114,190),8:(98,86,170),9:(74,62,142),10:(50,42,106),11:(255,100,152),12:(226,44,98),
     13:(114,82,142),14:(82,58,110),15:(54,38,74)}
def mk(base, ch): return [to555(ch[i]) if i in ch else base[i] for i in range(16)]
battleA, battleB = mk(bs, A), mk(bs, B)
FROLES = {0:'transparent (keep)', 1:'body shadow', 2:'body light', 3:'unused (magenta)', 4:'accent mid (spines/fins)',
          5:'unused', 6:'accent darkest', 7:'unused', 8:'accent dark', 9:'accent light', 10:'unused', 11:'unused',
          12:'unused', 13:'outline black (keep)', 14:'body darkest/shade', 15:'body highlight'}
FA = {15:(150,142,166),2:(118,110,138),1:(88,80,108),14:(46,40,58),4:(52,34,68),6:(24,16,32),8:(38,26,52),9:(76,62,104)}
FB = {15:(198,190,214),2:(160,152,182),1:(120,112,142),14:(70,62,86),4:(84,58,110),6:(40,28,54),8:(62,44,84),9:(118,100,150)}
folA, folB = mk(fn1, FA), mk(fn1, FB)
assert ow[579][0x41A0:0x41C0] == struct.pack('<16H', *fn1) and ow[579][0x4180:0x41A0] == struct.pack('<16H', *fn0)
def wbin(name, cols):
    p = os.path.join(OUT, name); open(p, 'wb').write(struct.pack('<16H', *cols)); return p
files = {k: wbin(k + '.bin', v) for k, v in [('battle_shadowA', battleA), ('battle_shadowB', battleB),
         ('follower_shadowA', folA), ('follower_shadowB', folB), ('battle_normal_orig', bn), ('battle_shiny_orig', bs),
         ('follower_normal_pal0_orig', fn0), ('follower_shiny_pal1_orig', fn1)]}
hx = lambda c: '#%02x%02x%02x' % bgr555(c)
info = {
 'battle': {
   'format': 'NCLR (RLCN), 72 bytes, 16 colours BGR555 at TTLP data offset; replace the 32 bytes of colour data only',
   'targets_shiny': [
     {'narc': 'data/pokepic_m.narc', 'rom_file_id': r.files['data/pokepic_m.narc'], 'entries': [1997, 1999],
      'note': '8 entries/species (1441 species): +0 front NCGR,+1 normal pal,+2 back NCGR,+3 normal pal,+4 front,+5 shiny pal,+6 back,+7 shiny pal. Sprites unencrypted. 249*8=1992'},
     {'narc': 'pbr/pokegra.narc', 'rom_file_id': r.files['pbr/pokegra.narc'], 'entries': [1499],
      'note': 'vanilla a/0/0/4 layout moved here (a/0/0/4 is a 1-byte stub): 6/species, 494 species; 1494 back F (empty), 1495 back M, 1496 front F (empty), 1497 front M, 1498 normal, 1499 shiny. Sprites encrypted (backward, seed=last u16)'}],
   'index_roles': {i: {'role': BROLES[i], 'normal': hx(bn[i]), 'shiny_orig': hx(bs[i]), 'shadowA': hx(battleA[i]), 'shadowB': hx(battleB[i])} for i in range(16)}},
 'follower': {
   'format': 'BTX0 in a/0/8/1, two 16-colour palettes tsure_poke0 / tsure_poke1 (32 bytes each at entry-relative offsets 0x4180 / 0x41A0); 8 textures tsure_poke*',
   'narc': 'a/0/8/1', 'rom_file_id': r.files['a/0/8/1'], 'entry': 579,
   'mapping': 'data/pokemon_overworld_info.narc[249] = 0x011A (282); arm9 table @0x020FBE24 (6-byte rows: sprite id, model id, flags), sprite 282+428=710 -> model 579 (same scheme as Darkrai 545+428=973 -> 842)',
   'palette_note': 'tsure_poke0 = normal (blue accents), tsure_poke1 = shiny (pink accents; same pal0/pal1 = normal/shiny pattern as Pikachu model 322 and Darkrai 842). Replace tsure_poke1 (32 bytes at entry offset 0x41A0).',
   'index_roles': {i: {'role': FROLES[i], 'pal0': hx(fn0[i]), 'pal1': hx(fn1[i]), 'shadowA': hx(folA[i]), 'shadowB': hx(folB[i])} for i in range(16)}},
 'files': {k: os.path.relpath(v, ROOT) for k, v in files.items()},
}
json.dump(info, open(os.path.join(OUT, 'lugia_palettes.json'), 'w'), indent=1)
# swatch sheet: rows = palettes, 16 swatches each, mid-grey background, 2x scale (16px swatches -> 32px)
rows = [('battle normal', bn), ('battle shiny (orig)', bs), ('battle Shadow A', battleA), ('battle Shadow B', battleB),
        ('follower normal (pal0)', fn0), ('follower shiny (pal1)', fn1), ('follower Shadow A', folA), ('follower Shadow B', folB)]
S, G = 32, 4; W = 16*(S+G)+G; H = len(rows)*(S+G)+G
img = [[(128,128,128,255)]*W for _ in range(H)]
for ri, (_, cols) in enumerate(rows):
    for ci, c in enumerate(cols):
        rgb = bgr555(c) + (255,); x0 = G + ci*(S+G); y0 = G + ri*(S+G)
        for y in range(y0, y0+S):
            for x in range(x0, x0+S):
                img[y][x] = ((200,200,200,255) if ((x//8+y//8)&1) else (150,150,150,255)) if ci == 0 else rgb
write_png(os.path.join(OUT, 'palette_swatches.png'), W, H, img)
print('rows top->bottom:', [n for n, _ in rows])
