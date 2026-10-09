#!/usr/bin/env python3
"""Strip of one Sketch Sprint character's run frames (in the given order) with a grid, for judging the cycle."""
import sys
from PIL import Image, ImageDraw
A=sys.argv[4] if len(sys.argv)>4 else 'src/assets/sketch-sprint/'
i=sys.argv[1];order=[int(x) for x in sys.argv[2].split(',')];out=sys.argv[3]
ims=[Image.open(A+'%s-run-%d.webp'%(i,f)).convert('RGBA') for f in order]
W=max(m.width for m in ims);H=max(m.height for m in ims)
sh=Image.new('RGB',(W*len(ims),H+20),'white');d=ImageDraw.Draw(sh)
for k,(f,m) in enumerate(zip(order,ims)):
  bg=Image.new('RGBA',(W,H),(240,240,240,255));bg.alpha_composite(m,((W-m.width)//2,H-m.height));sh.paste(bg.convert('RGB'),(k*W,0))
  for y in range(0,H,25):d.line([k*W,y,k*W+W,y],fill=(200,220,255))
  d.line([k*W+W//2,0,k*W+W//2,H],fill=(255,150,150))
  d.text((k*W+4,H+4),'%s %d'%(i,f),fill='black')
sh.save(out)
