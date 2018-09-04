#!/usr/bin/env python

import struct
from utils import *
from utils import _keyrec
from utils import _header
import astropy.io.fits as fits
import numpy as np


headerGDS = 'data/test64.descr'
dataGDS = 'data/test64.image'
#headerGDS = 'data/test.descr'
#dataGDS = 'data/test.image'


def read_header(filename):

    # prepare header object
    hdu = fits.PrimaryHDU()
    header = hdu.header
    if 'EXTEND' in header:
        del header['EXTEND']
    header['BITPIX'] = -32
    header['BSCALE'] = 1.0
    header['BZERO'] = 0.0

    # open header file and read it as binary
    f = open(filename, 'rb')

    # value of the number 1
    # go to 9th byte and read the following 4 bits
    f.seek(2*4)
    one = struct.unpack('i', f.read(4))[0]
    if one == 16777216:
        swapBytes = True
    else:
        swapBytes = False


    # version, sub version and osdep
    # extract from the first and second 4 bytes and the last 4 bytes
    f.seek(0) 
    gipsyVersion = read_blocks(f, 1, 4, 'i', swapBytes)[0]
    gipsySubVersion = read_blocks(f, 1, 4, 'i', swapBytes)[0]
    f.seek(3*4)
    osdep = read_blocks(f, 1, 4, 'i', swapBytes)[0]


    print 'GIPSY version %d.%d'%(gipsyVersion, gipsySubVersion)
    if gipsyVersion < 3:
        bitSys = 32
        REC_SIZ = REC_SIZ_32
    else:
        bitSys = 64
        REC_SIZ = REC_SIZ_64


    # read beginning of header information
    h = _header(f, bitSys, swapBytes)

    # loop through all keywords
    for i in range(0, h.maxrec-h.rec_start+2):
        
        # loop through all key records
        f.seek((h.rec_start+i)*REC_SIZ)
        k = _keyrec(bitSys, swapBytes)
        k.h.read_keyhead(f)
        
        # only consider keys with key_ind 1
        SHK = key_record_SHK(bitSys)
        if k.h.key_ind == 1:
            KEY_AL = SL + (SL*SHK-SHK)%SL  # key alignment size
            KEY_DL = REC_SIZ - SHK - KEY_AL   # data size
            k.alignment = read_blocks(f, KEY_AL, 1, 'c', swapBytes)
            k.data = read_blocks(f, KEY_DL, 1, 'c', swapBytes)
            
            # key name as string from char tuple
            ind = 0
            key = ''
            while k.h.name[ind] != '\x00':
                    key += k.h.name[ind]
                    ind += 1
            
            # only include data where type starts with fits
            if k.data[0:4] == tuple(['F', 'I', 'T', 'S']):
                # read data type
                ind = 5
                while k.data[ind] != ' ':
                    k.dtype += k.data[ind]
                    ind += 1
                
                # read data value
                k.value = ''
                while k.data[ind] != '\x00':
                    k.value += k.data[ind]
                    ind += 1
                
                try:
                    if k.dtype == 'CHAR':
                        value = k.value.split('\'')[1].strip()
                        comment = k.value.split('\'')[2].strip()
                        if comment != '':
                            comment = '/'.join(comment.split('/')[1:].strip())
                    if k.dtype == 'DBLE':
                        value = float(k.value.strip().split('/')[0].replace('D','E'))
                        if '/' in k.value:
                            comment = '/'.join(k.value.strip().split('/')[1:]).strip()
                    if k.dtype == 'INT':
                        value = int(k.value.strip().split('/')[0].replace('D','E'))
                        if '/' in k.value:
                            comment = '/'.join(k.value.strip().split('/')[1:]).strip()
                    header[key] = (value,comment)
                except:
                    pass
    f.close()
    
    return header

def read_data(header,filename):
    
    # get dimensions from the header and prepare empty array
    naxis = header['NAXIS']
    dims = []
    for i in range(naxis):
        dims.append(header['NAXIS%d'%(i+1)])
    # python reverses the order of the cube axes
    data = np.zeros(tuple(dims[3::-1]))
    
    # open file and start filling the array
    f = open(dataGDS, 'rb')
    for k in range(0,dims[2]):
        for j in range(0,dims[1]):
            for i in range(0,dims[0]):
                data[k,j,i] = read_blocks(f,1,4,'f',swapBytes=False)[0]
    
    # Nan's seem to be converted to -infs
    data[~np.isfinite(data)] = np.nan
    
    f.close()
    
    return data
    




h = read_header(headerGDS)
data = read_data(h,dataGDS)

if headerGDS == 'test64.descr':
    h['CTYPE1'] = 'RA---NCP'

hdu = fits.PrimaryHDU(data=data,header=h)
hdu.writeto('out.fits',overwrite=True)
del hdu










