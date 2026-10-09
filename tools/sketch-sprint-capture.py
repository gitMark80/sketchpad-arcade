#!/usr/bin/env python3
"""Capture Sketch Sprint's runner frame by frame with a stepped clock (deterministic 40 ms steps).
usage: sketch-sprint-capture.py OUTDIR [tag] [chars,...]   -> OUTDIR/<tag>-<char>-run-NN.png, -slide.png, <tag>-<char>-run.gif"""
import sys, os, threading, http.server, functools, json
from playwright.sync_api import sync_playwright
from PIL import Image
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','src')
out=sys.argv[1];tag=sys.argv[2] if len(sys.argv)>2 else 'cap'
chars=(sys.argv[3] if len(sys.argv)>3 else 'francis,clare,george,joan,john,catherine,joseph,therese').split(',')
os.makedirs(out,exist_ok=True);PORT=8947
class Q(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*a):pass
srv=http.server.ThreadingHTTPServer(('127.0.0.1',PORT),functools.partial(Q,directory=ROOT));threading.Thread(target=srv.serve_forever,daemon=True).start()
INIT="""(()=>{let q=[],t=null;window.requestAnimationFrame=cb=>{q.push(cb);return q.length};
window.__step=ms=>{if(t==null)t=performance.now();t+=ms;const a=q;q=[];a.forEach(cb=>cb(t))};
try{localStorage.setItem('seasidesketch.bank','99999');localStorage.setItem('seasidesketch.char',JSON.stringify(%s))}catch(e){}})()"""
errs=[]
with sync_playwright() as p:
  b=p.chromium.launch()
  for ch in chars:
    ctx=b.new_context(viewport={'width':390,'height':780},device_scale_factor=2)
    ctx.add_init_script(INIT%json.dumps(ch));pg=ctx.new_page()
    pg.on('pageerror',lambda e,ch=ch:errs.append((ch,str(e))))
    pg.on('console',lambda m,ch=ch:m.type=='error' and 'fonts.g' not in m.text and 'ERR_TUNNEL' not in m.text and errs.append((ch,'console:'+m.text)))
    pg.goto('http://127.0.0.1:%d/games/sketch-sprint.html'%PORT);pg.wait_for_timeout(600)
    for i in range(20):pg.evaluate('__step(40)')
    pg.wait_for_timeout(300);pg.evaluate('__step(40)')
    pg.click('#playBtn');pg.evaluate('__game._clear();__game._hold(true)')
    for i in range(60):pg.evaluate('__step(40)')
    pg.evaluate('__game._clear();__game._hold(true)')
    for i in range(80):pg.evaluate('__step(40)')   # get up to speed
    box=pg.evaluate("(()=>{const r=document.getElementById('cv').getBoundingClientRect();return [r.x,r.y,r.width,r.height]})()")
    clip={'x':box[0]+box[2]/2-60,'y':box[1]+box[3]-235,'width':120,'height':165}
    frames=[]
    for i in range(30):
      pg.evaluate('__step(40)');fn=os.path.join(out,'%s-%s-run-%02d.png'%(tag,ch,i));pg.screenshot(path=fn,clip=clip);frames.append(fn)
    sl=[]
    pg.evaluate('__game.slide()')
    for i in range(18):
      pg.evaluate('__step(40)');fn=os.path.join(out,'%s-%s-slideseq-%02d.png'%(tag,ch,i));pg.screenshot(path=fn,clip=clip);sl.append(fn)
    Image.open(sl[5]).save(os.path.join(out,'%s-%s-slide.png'%(tag,ch)))
    ims=[Image.open(f).convert('RGB') for f in frames+sl]
    ims[0].save(os.path.join(out,'%s-%s-run.gif'%(tag,ch)),save_all=True,append_images=ims[1:],duration=40,loop=0)
    # strip of run frames for review
    st=Image.new('RGB',(ims[0].width*15,ims[0].height*2),'white')
    for k in range(30):st.paste(ims[k],((k%15)*ims[0].width,(k//15)*ims[0].height))
    st.save(os.path.join(out,'%s-%s-runstrip.png'%(tag,ch)))
    st=Image.new('RGB',(ims[0].width*9,ims[0].height*2),'white')
    for k in range(18):st.paste(ims[30+k],((k%9)*ims[0].width,(k//9)*ims[0].height))
    st.save(os.path.join(out,'%s-%s-slidestrip.png'%(tag,ch)))
    print(ch,'speed',pg.evaluate('__game.speed'),'state',pg.evaluate('__game.state'))
    ctx.close()
  b.close()
print('ERRORS',errs)
