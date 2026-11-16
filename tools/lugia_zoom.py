import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw
from lugia_common import Rom, ncgr_info, bgr555
n = Rom().narc('data/pokepic_m.narc')
pal = [bgr555(v) for v in struct.unpack('<16H', open('lugia/' + sys.argv[1], 'rb').read())]
edits = {}
if len(sys.argv) > 3:
    exec(open(sys.argv[3]).read())   # defines EDITS {(entry,x,y):idx}
    edits = EDITS
Z = int(os.environ.get('Z', 8)); boxes = [tuple(map(int, b.split(','))) for b in os.environ['BOXES'].split(';')]
W = sum((b[3]-b[1])*Z + 8 for b in boxes); img = Image.new('RGB', (W, max(b[4]-b[2] for b in boxes)*Z), (128, 128, 128)); d = ImageDraw.Draw(img); ox = 0
for e, x0, y0, x1, y1 in boxes:
    px = ncgr_info(n[e])['px']
    for y in range(y0, y1):
        for x in range(x0, x1):
            i = edits.get((e, x, y), (px[(y*160+x)//2] >> (4*(x & 1))) & 15)
            if i: d.rectangle([ox+(x-x0)*Z, (y-y0)*Z, ox+(x-x0+1)*Z-1, (y-y0+1)*Z-1], fill=pal[i])
    ox += (x1-x0)*Z + 8
img.save('lugia/' + sys.argv[2])
