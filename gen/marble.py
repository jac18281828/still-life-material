import numpy as np, sys
from PIL import Image
rng=np.random.default_rng(7)
N=2048
def vnoise(n, cells):
    g=rng.random((cells+1,cells+1))
    x=np.linspace(0,cells,n,endpoint=False); xi=x.astype(int); xf=x-xi
    u=xf*xf*(3-2*xf)
    a=g[np.ix_(xi,xi)]; b=g[np.ix_(xi+1,xi)]; c=g[np.ix_(xi,xi+1)]; d=g[np.ix_(xi+1,xi+1)]
    U=u[:,None]; V=u[None,:]
    return (a*(1-U)+b*U)*(1-V)+(c*(1-U)+d*U)*V
def fbm(n, base, oct=6):
    s=np.zeros((n,n)); amp=1; tot=0
    for o in range(oct):
        s+=amp*vnoise(n, base*2**o); tot+=amp; amp*=0.5
    return s/tot
yy,xx=np.mgrid[0:N,0:N]/N
tiles=20
def marble(shift, freq, turb, k):
    t=fbm(N, 4)+0.5*fbm(N,8)
    v=np.sin((xx*0.7+yy*0.4+shift)*freq*np.pi + turb*t*8)
    return (1-np.abs(v))**k, fbm(N,16)
light, ln = marble(0.0, 5, 0.6, 5)
dark,  dn = marble(0.37, 4, 0.7, 4)
cream=np.array([0.93,0.9,0.84]); vein=np.array([0.55,0.52,0.5])
slate=np.array([0.36,0.37,0.34]); dvein=np.array([0.62,0.62,0.58])
L=cream*(1-0.1*ln[...,None]) + (vein-cream)*light[...,None]*0.8
D=slate*(0.85+0.3*dn[...,None]) + (dvein-slate)*dark[...,None]*0.7
ti=(xx*tiles).astype(int); tj=(yy*tiles).astype(int)
chk=((ti+tj)%2==0)[...,None]
img=np.where(chk,L,D)
fx=(xx*tiles)%1; fy=(yy*tiles)%1
gw=0.02
grout=((fx<gw)|(fx>1-gw)|(fy<gw)|(fy>1-gw))[...,None]
img=np.where(grout,np.array([0.42,0.4,0.37]),img)
Image.fromarray((np.clip(img,0,1)*255+0.5).astype(np.uint8)).save(sys.argv[1])
