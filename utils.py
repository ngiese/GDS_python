import struct

MAXDIM     = 20
REC_SIZ_32 = 200
REC_SIZ_64 = 224
KEY_LEN    = 21
SL = 4 # size of fint



def swap_bytes(byteString, length):
    
    placeHolder = ''.join(['c' for i in range(length)])
    return struct.pack(placeHolder, *(struct.unpack(placeHolder,byteString)[::-1]))


def convert_bytes(byteString, length, fmt, swapBytes = False):
    
    if swapBytes:
        return struct.unpack(fmt, swap_bytes(byteString, length))
    else:
        return struct.unpack(fmt, byteString)


def read_blocks(filePointer, numBlocks, blockSize, varType = 'i', swapBytes = False):
    
    byteString = ''
    for i in range(0, numBlocks):
        byteStringTmp = filePointer.read(blockSize)
        if swapBytes:
            byteStringTmp = swap_bytes(byteStringTmp, blockSize)
        byteString += byteStringTmp
    
    varSize = 4
    if varType in ['q', 'Q', 'd']:
        varSize = 8
    if varType == 'c':
        varSize = 1
    fmt = ''.join([varType for i in range(numBlocks*blockSize/varSize)])
    return convert_bytes(byteString, numBlocks*blockSize, fmt)




class _keyhead:
    
    def __init__(self, bitSys, swapBytes):
        self.bitSys = bitSys
        self.swapBytes = swapBytes
        self.level = None
        self.key_ind = None
        self.length = None
        self.readpos = None
        self.next_key = None
        self.next_ext = None
        self.last_ext = None
        self.curr_ext = None
        self.align = None
        self.type = None
        self.name = None
    
    def read_keyhead(self, f):
        if self.bitSys == 64:
            self.level = read_blocks(f, 1, 8, 'q', self.swapBytes)[0]
        self.key_ind = read_blocks(f, 1, 4, 'i', self.swapBytes)[0]
        if self.key_ind == 1:
            self.length = read_blocks(f, 1, 4, 'i', self.swapBytes)[0]
            self.readpos = read_blocks(f, 1, 4, 'i', self.swapBytes)[0]
            if self.bitSys == 32:
                self.level = read_blocks(f, 1, 4, 'i', self.swapBytes)[0]
            self.next_key  = read_blocks(f, 1, 4, 'i', self.swapBytes)[0]
            self.next_ext  = read_blocks(f, 1, 4, 'i', self.swapBytes)[0]
            self.last_ext  = read_blocks(f, 1, 4, 'i', self.swapBytes)[0]
            self.curr_ext  = read_blocks(f, 1, 4, 'i', self.swapBytes)[0]
            if self.bitSys == 64:
                self.align = read_blocks(f, 1, 4, 'i', self.swapBytes)[0]
            self.type  = read_blocks(f, 1, 1, 'c', self.swapBytes)[0]
            self.name  = read_blocks(f, KEY_LEN, 1, 'c', self.swapBytes)



def key_record_SHK(bitSys):
    
    if bitSys == 64:
        return 8 + 8*4 + 1 + KEY_LEN
    else:
        return 8*4 + 1 + KEY_LEN

class _keyrec:
    
    def __init__(self,bitSys,swapBytes):
        
        self.h = _keyhead(bitSys,swapBytes)
        self.alignment = None
        self.data = None
        self.dtype = ''
        self.value = None
        
    
class _header:
    
    def __init__(self,f,bitSys,swapBytes):
    
        self.ax_origin = read_blocks(f,MAXDIM,8,'d',swapBytes) # axis origis
        if bitSys==32:
            self.ax_size   = read_blocks(f,MAXDIM,4,'i',swapBytes)   # axis sizes
            self.ax_factor = read_blocks(f,MAXDIM+1,4,'i',swapBytes) # factors
        else:
            self.ax_factor = read_blocks(f,MAXDIM+1,8,'q',swapBytes)
            self.ax_size   = read_blocks(f,MAXDIM,4,'i',swapBytes)
        self.naxis      = read_blocks(f,1,4,'i',swapBytes)[0]
        self.nitems     = read_blocks(f,1,4,'i',swapBytes)[0]  # number of items
        self.reserved2  = read_blocks(f,1,4,'i',swapBytes)[0]  # not used space
        self.reserved3  = read_blocks(f,1,4,'i',swapBytes)[0]  # not used space
        self.rec_start  = read_blocks(f,1,4,'i',swapBytes)[0]  # index if first data record
        self.n_alloc    = read_blocks(f,1,4,'i',swapBytes)[0]  # number of records allocated
        self.maxrec     = read_blocks(f,1,4,'i',swapBytes)[0]  # current maximum number of records in file
        self.n_buck     = read_blocks(f,1,4,'i',swapBytes)[0]  # size of hash table
        self.spare_fint = read_blocks(f,8,4,'i',swapBytes)[0]  # some more unused space
        self.free       = read_blocks(f,1,4,'i',swapBytes)[0]  # free list pointer
        self.hash_tab   = read_blocks(f,1,4,'i',swapBytes)[0]  # hash table
