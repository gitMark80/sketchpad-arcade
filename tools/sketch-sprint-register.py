#!/usr/bin/env python3
"""Measure each Sketch Sprint run frame against a reference frame of the same kid: best scale + offset of the
head/shoulders (top ~38% of the figure), plus where each foot is.  usage: sketch-sprint-register.py SRC_DIR [ids]"""
import sys, json
import numpy as np
from PIL import Image
from scipy.signal import fftconvolve
SRC=sys.argv[1].rstrip('/')+'/'
IDS=(sys.argv[2] if len(sys.argv)>2 else 'francis,clare,george,joan,john,catherine,joseph,therese').split(',')
def alpha(im):return (np.asarray(im)[:,:,3]>60).astype(np.float32)
def match(tpl,img):
  # normalised overlap of template (head mask) slid over image mask; returns best (score, dy, dx) of template's top-left
  c=fftconvolve(img,tpl[::-1,::-1],mode='valid');den=tpl.sum()+fftconvolve(img,np.ones_like(tpl),mode='valid')
  sc=2*c/np.maximum(den,1);k=np.unravel_index(np.argmax(sc),sc.shape);return sc[k],k[0],k[1]
def feet(a,cx):
  H,W=a.shape;res=[]
  for side in (a[:,:int(cx)],a[:,int(cx):]):
    rows=np.nonzero(side[int(H*.6):].any(1))[0];res.append(H-(int(H*.6)+rows.max())-1 if len(rows) else H)
  return res
def analyse(i,ref=None):
  ims=[Image.open(SRC+'%s-run-%d.webp'%(i,f)).convert('RGBA') for f in range(1,9)]
  A=[alpha(m) for m in ims]
  tops=[np.nonzero(a.any(1))[0][0] for a in A]
  if ref is None:ref=int(np.argsort(tops)[3])   # a median-height frame
  a0=A[ref];H,W=a0.shape;t0=tops[ref];hh=int((H-t0)*.38)
  cols=np.nonzero(a0[t0:t0+hh].any(0))[0];x0,x1=max(0,cols[0]-2),cols[-1]+3
  tpl=a0[t0:t0+hh,x0:x1]
  out=[]
  for f,(m,a) in enumerate(zip(ims,A)):
    best=None
    for s in np.arange(.86,1.145,.01):
      w,h=int(round(m.width*s)),int(round(m.height*s))
      b=alpha(m.resize((w,h),Image.BILINEAR));pad=np.zeros((h+80,w+80),np.float32);pad[40:40+h,40:40+w]=b
      sc,dy,dx=match(tpl,pad)
      if best is None or sc>best[0]:best=(sc,s,dy-40,dx-40,w,h)
    sc,s,dy,dx,w,h=best
    # transform: frame pixel p -> ref pixel q = p*s + (x0-dx, t0-dy)
    ox,oy=x0-dx,t0-dy
    bottom=(H-1)*s+oy  # where this frame's baseline lands in ref coords (all frames have feet on the bottom row)
    out.append(dict(f=f+1,score=round(float(sc),3),s=round(float(s),3),ox=round(float(ox),1),oy=round(float(oy),1),baseline_in_ref=round(float(bottom),1),feet=feet(a,W/2)))
  return ref+1,out
if __name__=='__main__':
  R={}
  for i in IDS:
    ref,o=analyse(i);R[i]=dict(ref=ref,frames=o);print(i,'ref',ref)
    for r in o:print('  ',r)
  json.dump(R,open('/dev/stdout','w')) if '--json' in sys.argv else None
