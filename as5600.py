from collections import namedtuple
from struct import unpack, pack

m12 = (1<<12)-1  # 0xFFF

AS5600_id = 0x36

REGS=namedtuple('REGS','ZMCO ZPOS MPOS MANG CONF RAWANGLE ANGLE  STATUS AGC MAGNITUDE BURN')
r = REGS(0,1,3,5,7,0xc,0xe,0xb,0x1a,0x1b,0xff)

class RegDescriptor:
    "Read and write a bit field from a register"

    def __init__(self,reg,shift,mask,buffsize=2):
        "initialise with specific identifiers for the bit field"

        self.reg = reg
        self.shift = shift
        self.mask = mask
        self.buffsize = buffsize
        self.writeable = (r.ZMCO,r.ZPOS,r.MPOS,r.MANG,r.CONF,r.BURN)
        # NB the I2c object and the device name come from the main AS5600 class via an object

    def get_register(self,obj):
        "Read an I2C register"
        v = None
        while not obj.i2c.try_lock():
            pass
        try:
            # Cache those registers with values that will not change.
            # Don't bother caching bit fields.
            if self.reg in obj.cache:
                return obj.cache[self.reg]

            buff = bytearray(self.buffsize)
            obj.i2c.writeto_then_readfrom(obj.device, bytes([self.reg]), buff)

            if self.buffsize == 2:
                v = unpack(">H",buff)[0]  # 2 bytes big endian
            else:
                v = unpack(">B",buff)[0]

            # Cache writeable values since they are the ones that will not change in usage
            if self.reg in self.writeable:
                obj.cache[self.reg] = v
        finally:
            obj.i2c.unlock()
        return v

    def __get__(self,obj,objtype):
        "Get the register then extract the bit field"
        v = self.get_register(obj)
        v >>= self.shift
        v &= self.mask
        return v

    def __set__(self,obj,value):
        "Insert a new value into the bit field of the old value then write it back"
        if not self.reg in self.writeable:
            raise AttributeError('Register is not writable')
        oldvalue = self.get_register(obj)
        insertmask = 0xffff ^ (self.mask << self.shift) # make a mask for a hole
        oldvalue &= insertmask # use the mask to make a hole in the old value
        value &= self.mask # mask our new value in case it is too big
        value <<= self.shift # shift it into place
        oldvalue |= value  # OR the new value back into the hole
        if self.buffsize == 2:
            buff = pack(">H",oldvalue)
        else:
            buff = pack(">B",oldvalue)
        while not obj.i2c.try_lock():
            pass
        try:
            obj.i2c.writeto(obj.device, bytes([self.reg]) + buff) # write result back to the AS5600
            # must write the new value into the cache
            obj.cache[self.reg] = oldvalue
        finally:
            obj.i2c.unlock()



class AS5600:
    def __init__(self,i2c,device):
        self.i2c = i2c
        self.device = device
        self.writeable =(r.ZMCO,r.ZPOS,r.MPOS,r.MANG,r.CONF,r.BURN)
        self.cache = {} # cache register values

    # Use descriptors to read and write a bit field from a register
    # 1. we read one or two bytes from i2c
    # 2. We shift the value so that the least significant bit is bit zero
    # 3. We mask off the bits required  (most values are 12 bits hence m12)
    ZMCO=      RegDescriptor(r.ZMCO,0,3,1)          # 2-bit
    ZPOS=      RegDescriptor(r.ZPOS,0,m12)          # zero position
    MPOS=      RegDescriptor(r.MPOS,0,m12)          # maximum position
    MANG=      RegDescriptor(r.MANG,0,m12)          # maximum angle (alternative to above)
    CONF=      RegDescriptor(r.CONF,0,(1<<14)-1)    # this register has 14 bits (see below)
    RAWANGLE=  RegDescriptor(r.RAWANGLE,0,m12)      # raw angle (0-4095)
    ANGLE   =  RegDescriptor(r.ANGLE,0,m12)         # angle with various adjustments (see datasheet)
    STATUS=    RegDescriptor(r.STATUS,0,m12)        # magnet detection/field strength
    AGC=       RegDescriptor(r.AGC,0,0xF,1)         # automatic gain control
    MAGNITUDE= RegDescriptor(r.MAGNITUDE,0,m12)     # ? something to do with the CORDIC for atan RTFM
    BURN=      RegDescriptor(r.BURN,0,0xF,1)        # Used for burning changes to ZPOS/MPOS/MANG (limited number of uses!)

    #Configuration bit fields
    PM =      RegDescriptor(r.CONF,0,0x3)   # 2bits Power mode
    HYST =    RegDescriptor(r.CONF,2,0x3)   # hysteresis for smoothing out zero crossing
    OUTS =    RegDescriptor(r.CONF,4,0x3)   # HARDWARE output stage ie analog (low,high)  or PWM
    PWMF =    RegDescriptor(r.CONF,6,0x3)   # PWM frequency
    SF =      RegDescriptor(r.CONF,8,0x3)   # slow filter (?filters glitches harder) RTFM
    FTH =     RegDescriptor(r.CONF,10,0x7)  # 3 bits fast filter threshold. RTFM
    WD =      RegDescriptor(r.CONF,13,0x1)  # 1 bit watch dog - Kicks into low power mode if nothing changes

    #status bit fields.
    MH =      RegDescriptor(r.STATUS,3,0x1,1) #1 bit  Magnet too strong (high)
    ML =      RegDescriptor(r.STATUS,4,0x1,1) #1 bit  Magnet too weak (low)
    MD =      RegDescriptor(r.STATUS,5,0x1,1) #1 bit  Magnet detected
    MS =      RegDescriptor(r.STATUS,3,0x7,1) #3 bits Magnet Status: MD/ML/MH combined as per STATUS but shifted down to bits 1-3

    def scan(self) -> bool:
        "Debug utility function to check your i2c bus"
        while not self.i2c.try_lock():
            pass
        try:
            devices = self.i2c.scan()
            return AS5600_id in devices
        finally:
            self.i2c.unlock()

    def magnet_status(self) -> str:
        s = "magnet "
        if self.MD == 0:
            s += "NOT "
        s += "detected - strength "
        if self.ML == 1:
            s += "too weak"
        elif self.MH == 1:
            s += "too strong"
        else:
            s += "ok"
        return s
