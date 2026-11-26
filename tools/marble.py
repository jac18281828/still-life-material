# SPDX-License-Identifier: MIT
# Marble floor: a 2048 by 2048 checkerboard of cream and slate marble with grout, and its 16-bit
# tangent-space normal map of recessed, bevelled grout and tiles that each sit a hair off level.
# Usage: marble.py <marble.tif> <normal.tif>
import numpy as np, os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tiff16 import write_tiff16
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

NORMAL_N=4096
GROUT_DEPTH=5
BEVEL=0.03
TILE_TILT=0.05
nrng=np.random.default_rng(31)
gy,gx=np.mgrid[0:NORMAL_N,0:NORMAL_N]/NORMAL_N
nfx=(gx*tiles)%1; nfy=(gy*tiles)%1
edge=np.minimum(np.minimum(nfx,1-nfx),np.minimum(nfy,1-nfy))
ramp=np.clip((edge-gw)/BEVEL,0,1)
shoulder=ramp*ramp*(3-2*ramp)
tile_px=NORMAL_N/tiles
tilt=nrng.uniform(-TILE_TILT,TILE_TILT,(2,tiles,tiles))
ni=(gx*tiles).astype(int); nj=(gy*tiles).astype(int)
height=-GROUT_DEPTH*(1-shoulder)+(tilt[0][nj,ni]*(nfx-0.5)+tilt[1][nj,ni]*(nfy-0.5))*tile_px
hx=(np.roll(height,-1,1)-np.roll(height,1,1))*0.5
hy=(np.roll(height,-1,0)-np.roll(height,1,0))*0.5
nx,ny,nz=-hx,hy,np.ones_like(hx)
length=np.sqrt(nx*nx+ny*ny+nz*nz)
write_tiff16(sys.argv[2],np.stack([nx,ny,nz],-1)/length[...,None]*0.5+0.5)
