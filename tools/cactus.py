# SPDX-License-Identifier: MIT
# Cactus: the pad skin texture (512 square), its 16-bit tangent-space normal map (1024 square, s wrapping
# around the pad) and the RIB of four pads with areoles, spines and fruit.
# Usage: cactus.py <skin.tif> <rib> <tex_name> <normal.tif> [scale]   scale multiplies both maps' sides
import numpy as np, os, struct, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tiff16 import write_tiff16
out_tif, out_rib, tex_name, out_normal = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
SCALE=int(sys.argv[5]) if len(sys.argv)>5 else 1
if SCALE<1: sys.exit('scale must be a positive integer')
AR=0.0055*0.75
rng=np.random.default_rng(11)
# ---- pad skin ----
SKIN=512
N=SKIN*SCALE
def vnoise(n, cx, cy, source=rng, wrap=False):
    g=source.random((cy+1,cx+1))
    if wrap: g[:,cx]=g[:,0]
    y=np.linspace(0,cy,n,endpoint=False); x=np.linspace(0,cx,n,endpoint=False)
    yi=y.astype(int); xi=x.astype(int); yf=y-yi; xf=x-xi
    yf=yf*yf*(3-2*yf); xf=xf*xf*(3-2*xf)
    a=g[np.ix_(yi,xi)]; b=g[np.ix_(yi,xi+1)]; c=g[np.ix_(yi+1,xi)]; d=g[np.ix_(yi+1,xi+1)]
    X=xf[None,:]; Y=yf[:,None]
    return (a*(1-X)+b*X)*(1-Y)+(c*(1-X)+d*X)*Y
mott=0.5*vnoise(N,6,6)+0.3*vnoise(N,14,14)+0.2*vnoise(N,40,40)
streak=vnoise(N,90,6)
v,u=np.mgrid[0:N,0:N]/N        # rows ~ t, cols ~ s
theta=u*2*np.pi
face=np.abs(np.sin(theta))     # 1 at pad faces, 0 at the rim
pole=np.sin(v*np.pi)           # 0 at top and bottom
deep=np.array([0.17,0.36,0.13]); mid=np.array([0.36,0.56,0.22]); pale=np.array([0.58,0.66,0.32])
k=(0.55*face*pole+0.45*mott)[...,None]
col=deep*(1-k)+mid*k
col=col+(pale-col)*np.clip((mott-0.62)*3,0,1)[...,None]*0.5
col*= (0.93+0.12*streak)[...,None]
rim=np.clip(1-face*1.6,0,1)*0.0+np.clip(0.25-pole,0,1)*2.2
col=col*(1-0.35*rim[...,None])+np.array([0.5,0.45,0.25])*0.35*rim[...,None]
write_tiff16(out_tif, col*0.86)
# ---- pad skin normal map: gentle undulation and fine pebbling, tangent space, s wrapping around the pad ----
NORMAL_N=1024*SCALE
NORMAL_STRENGTH=6
nrng=np.random.default_rng(23)
def relief(n, cx, cy): return vnoise(n, cx, cy, nrng, True)
height=0.45*relief(NORMAL_N,8,4)+0.3*relief(NORMAL_N,32,16)+0.15*relief(NORMAL_N,96,48)+0.1*relief(NORMAL_N,240,120)
hx=(np.roll(height,-1,1)-np.roll(height,1,1))*0.5
hy=(np.roll(height,-1,0)-np.roll(height,1,0))*0.5
nx,ny,nz=-hx*NORMAL_STRENGTH*NORMAL_N/SKIN,hy*NORMAL_STRENGTH*NORMAL_N/SKIN,np.ones_like(hx)
length=np.sqrt(nx*nx+ny*ny+nz*nz)
write_tiff16(out_normal, np.stack([nx,ny,nz],-1)/length[...,None]*0.5+0.5)
# ---- pads, areoles, spines ----
pads=[((0,0.44,0),(15,0),(0.12,0.16,0.04)),
      ((-0.08,0.71,0.01),(15,28),(0.1,0.13,0.035)),
      ((0.09,0.69,-0.01),(-20,-25),(0.09,0.12,0.032)),
      ((-0.17,0.89,0.01),(10,12),(0.065,0.085,0.025))]
def norm(v): v=np.asarray(v,float); return v/np.linalg.norm(v)
L=[]
w=L.append
for (t,(ry,rz),(a,b,c)) in pads:
    w('AttributeBegin')
    w('\tTranslate %g %g %g'%t); w('\tRotate %g 0 1 0'%ry)
    if rz: w('\tRotate %g 0 0 1'%rz)
    w('\tAttributeBegin')
    w('\t\tSurface "paintedplastic" "Kd" [0.85] "Ks" [0.18] "roughness" [0.22] "texturename" ["%s"] "string normalname" ["%s"]' % (tex_name, out_normal))
    w('\t\tColor [1 1 1]')
    w('\t\tScale %g %g %g'%(a,b,c)); w('\t\tRotate -90 1 0 0'); w('\t\tSphere 1 -1 1 360')
    w('\tAttributeEnd')
    pts=[]
    for j,yy in enumerate(np.arange(-0.75,0.85,0.27)):
        off=0.5*0.36 if j%2 else 0
        for xx in np.arange(-0.9+off,0.91,0.36):
            if xx*xx+yy*yy<0.72: pts.append((xx,yy))
    for side in (1,-1):
        for (xx,yy) in pts:
            xx+=rng.normal(0,0.07); yy+=rng.normal(0,0.06)
            zz=side*math.sqrt(max(0.0,1-xx*xx-yy*yy))
            P=np.array([a*xx,b*yy,c*zz]); n=norm([xx/a,yy/b,zz/c])
            ex=norm(np.cross(n,[0.3,0.2,0.93])); ey=np.cross(n,ex)
            w('\tSurface "matte"'); w("\tColor [0.15 0.29 0.08]")
            M=list(ex)+[0]+list(ey)+[0]+list(n*0.4)+[0]+list(P)+[1]
            w('\tAttributeBegin'); w('\t\tConcatTransform ['+' '.join('%.5f'%m for m in M)+']')
            w('\t\tSphere %g %g %g 360'%(AR,-AR,AR)); w('\tAttributeEnd')
            def cone(d,h,r,base):
                ex=norm(np.cross(d,[0.3,0.2,0.93]) if abs(d[2])<0.9 else np.cross(d,[1,0,0])); ey=np.cross(d,ex)
                M=list(ex)+[0]+list(ey)+[0]+list(d)+[0]+list(base)+[1]
                w('\tAttributeBegin'); w('\t\tConcatTransform ['+' '.join('%.5f'%m for m in M)+']')
                w('\t\tCone %.4f %.5f 360'%(h,r)); w('\tAttributeEnd')
            w('\tSurface "matte"'); w('\tColor [0.95 0.94 0.88]')
            w('\tAttributeBegin'); w('\t\tTranslate %.5f %.5f %.5f'%tuple(P+n*0.0012)); w('\t\tSphere %g %g %g 360'%(AR*0.5,-AR*0.5,AR*0.5)); w('\tAttributeEnd')
            for g in range(rng.integers(6,10)):
                d=norm(n+rng.normal(0,0.55,3))
                if d@n<0.3: d=norm(d+n)
                cone(d,rng.uniform(0.004,0.007),0.0009,P+n*0.0008+(ex*rng.normal(0,1)+ey*rng.normal(0,1))*AR*0.35)
            w('\tSurface "plastic" "Ks" [0.35] "roughness" [0.08]'); w('\tColor [0.88 0.84 0.7]')
            for k in range(rng.integers(1,3)):
                d=norm(n+np.array([0,0.45,0])+rng.normal(0,0.3,3))
                if d@n<0.35: d=norm(d+n)
                cone(d,rng.uniform(0.024,0.04),0.0017,P)
    w('AttributeEnd')
w('Surface "plastic" "Ks" [0.25] "roughness" [0.2]')
w('Color [0.95 0.32 0.5]')
for (x,y,z,r) in [(-0.19,0.975,0.01,0.026),(0.15,0.795,-0.02,0.024),(-0.03,0.83,0.01,0.02)]:
    w('AttributeBegin'); w('\tTranslate %g %g %g'%(x,y,z)); w('\tScale 1 1.25 1'); w('\tSphere %g %g %g 360'%(r,-r,r)); w('AttributeEnd')
open(out_rib,'w').write('\n'.join(L)+'\n')
print(sum(1 for l in L if 'Cone' in l),'cones')
