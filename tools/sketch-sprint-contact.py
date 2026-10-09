#!/usr/bin/env python3
"""Contact sheet of Sketch Sprint run frames (+slide) per kid, bbox in red, feet baseline in blue, alpha centroid in green."""
import sys
from PIL import Image, ImageDraw
import numpy as np
A='src/assets/sketch-sprint/'
ids=['francis','clare','george','joan','john','catherine','joseph','therese']
out=sys.argv[1]
S=0.6;cw,ch=int(240*S)+8,int(320*S)+24
sheet=Image.new('RGB',(cw*9,ch*len(ids)),'white');d=ImageDraw.Draw(sheet)
for r,i in enumerate(ids):
  for f in range(9):
    fn=A+i+('-run-%d'%(f+1) if f<8 else '-slide')+'.webp'
    im=Image.open(fn).convert('RGBA');a=np.asarray(im)[:,:,3]>40
    bb=im.getchannel('A').point(lambda v:255 if v>40 else 0).getbbox()
    ys,xs=np.nonzero(a);cx=xs.mean()
    # hips: mean x of alpha in rows 45-60% of height
    H=im.height;band=a[int(H*.42):int(H*.55)];hx=np.nonzero(band)[1].mean()
    bg=Image.new('RGBA',im.size,(235,235,235,255));bg.alpha_composite(im)
    t=bg.convert('RGB').resize((int(im.width*S),int(im.height*S)))
    x0,y0=f*cw+4,r*ch+4;sheet.paste(t,(x0,y0));
    d.rectangle([x0+bb[0]*S,y0+bb[1]*S,x0+bb[2]*S,y0+bb[3]*S],outline='red')
    d.line([x0,y0+bb[3]*S-1,x0+t.width,y0+bb[3]*S-1],fill='blue')
    d.line([x0+hx*S,y0,x0+hx*S,y0+t.height],fill='green')
    d.line([x0+im.width/2*S,y0,x0+im.width/2*S,y0+t.height],fill=(200,200,0))
    d.text((x0,y0+t.height+2),'%s %s %dx%d hip%.0f'%(i[:4],f+1 if f<8 else 'sl',im.width,im.height,hx-im.width/2),fill='black')
sheet.save(out)
