# SPDX-License-Identifier: MIT
# Gold-leaf texture for the gilded shader: crinkled, mottled foil with sparse cracks to a red
# bole, 2048 by 1024, s around the sphere and t pole to pole, and its 16-bit tangent-space normal
# map: the same crinkle and cracks plus sharp creases, so the foil has edges. Usage: foil.py <foil.tif> <normal.tif>
import numpy as np, os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tiff16 import write_tiff16
rng=np.random.default_rng(5)
W,H=2048,1024
yy,xx=np.mgrid[0:H,0:W].astype(float)
u=xx/W; v=yy/H*0.5
P=1024
def noise(x,y):
    g=rng.random((P,P))
    xi=np.floor(x).astype(int); yi=np.floor(y).astype(int); xf=x-xi; yf=y-yi
    xf=xf*xf*(3-2*xf); yf=yf*yf*(3-2*yf)
    x0=xi%P; x1=(xi+1)%P; y0=yi%P; y1=(yi+1)%P
    return (g[y0,x0]*(1-xf)+g[y0,x1]*xf)*(1-yf)+(g[y1,x0]*(1-xf)+g[y1,x1]*xf)*yf
def rot(f,ang):
    c,s=np.cos(ang),np.sin(ang); x=u*f; y=v*f
    return x*c-y*s+100, x*s+y*c+100
wx=noise(*rot(10,0.3))-0.5; wy=noise(*rot(10,1.1))-0.5
def rnoise(f,ang,warp=0.0):
    x,y=rot(f,ang); return noise(x+warp*wx,y+warp*wy)
def ridged(f,p):
    acc=0
    for a in (0.4,1.3,2.2):
        acc+= (1-np.abs(2*rnoise(f,a,1.2)-1))**p
    return acc/3
mott=0.5*rnoise(5,0.7,1)+0.3*rnoise(14,1.9,1)+0.2*rnoise(36,2.8,1)
crinkle=0.45*ridged(60,5)+0.35*ridged(140,6)+0.2*ridged(320,7)
crack=((1-np.abs(2*rnoise(90,0.9,1.5)-1))**50)*(rnoise(18,2.5)>0.76)
lum=0.82+0.18*mott-0.2*crinkle
img=np.stack([lum,lum*0.985,lum*0.96],-1)
k=np.clip(crack*0.7,0,1)[...,None]
img=img*(1-k)+np.array([0.55,0.3,0.22])*k
Image.fromarray((np.clip(img,0,1)*255+0.5).astype(np.uint8)).save(sys.argv[1])

CREASE_WEIGHT=0.8
NORMAL_STRENGTH=12
def crease(f):
    return sum(1-np.abs(2*rnoise(f,a,1.2)-1) for a in (0.4,1.3,2.2))/3
creases=0.5*crease(38)+0.3*crease(90)+0.2*crease(210)
height=lum-0.5*np.clip(crack*0.7,0,1)+CREASE_WEIGHT*creases
hx=(np.roll(height,-1,1)-np.roll(height,1,1))*0.5
hy=(np.roll(height,-1,0)-np.roll(height,1,0))*0.5
nx,ny,nz=-hx*NORMAL_STRENGTH,hy*NORMAL_STRENGTH,np.ones_like(hx)
length=np.sqrt(nx*nx+ny*ny+nz*nz)
write_tiff16(sys.argv[2],np.stack([nx,ny,nz],-1)/length[...,None]*0.5+0.5)
