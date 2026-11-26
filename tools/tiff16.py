# SPDX-License-Identifier: MIT
# 16-bit RGB TIFF writer (baseline, one strip, top-left) shared by the generators.
import struct

import numpy as np


def write_tiff16(path, img):
    h,w,_=img.shape
    scaled=np.clip(img,0,1)
    scaled*=65535
    scaled+=0.5
    data=scaled.astype('>u2').tobytes()
    del scaled
    entries=[]
    def e(tag,typ,count,val): entries.append((tag,typ,count,val))
    off_bps=8; hdr=b'MM\x00\x2a'
    # layout: header(8) | bps(6) | ifd | data
    bps=struct.pack('>HHH',16,16,16)
    nent=11; ifd_off=8+len(bps); ifd_len=2+nent*12+4; data_off=ifd_off+ifd_len
    e(256,4,1,w); e(257,4,1,h); e(258,3,3,off_bps); e(259,3,1,1); e(262,3,1,2)
    e(273,4,1,data_off); e(274,3,1,1); e(277,3,1,3); e(278,4,1,h); e(279,4,1,len(data)); e(284,3,1,1)
    ifd=struct.pack('>H',nent)
    for tag,typ,count,val in entries:
        if typ==3 and count==1: ifd+=struct.pack('>HHIHH',tag,typ,count,val,0)
        else: ifd+=struct.pack('>HHII',tag,typ,count,val)
    ifd+=struct.pack('>I',0)
    with open(path,'wb') as out:
        out.write(hdr+struct.pack('>I',ifd_off)+bps+ifd+data)
