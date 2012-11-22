from PyTango import DevState, AttrQuality
from sardana import pool
from sardana.pool.controller import IORegisterController
import taurus
import time

class BL13EHBlightIORController(IORegisterController):

    axis_attributes ={'Labels':
                          {'Type':'PyTango.DevString',#{'Type':'PyTango.DevVarStringArray',
                           'Description':'String list with the meaning of each discrete position',
                           'R/W Type':'PyTango.READ_WRITE'},
                      'Brightness':
                          {'Type':'PyTango.DevLong',
                           'Description':'Percentage of brightness 0 - 100',
                           'R/W Type':'PyTango.READ_WRITE'},
                      }
    MaxDevice = 1

    def __init__(self, inst, props, *args, **kwargs):
        IORegisterController.__init__(self, inst, props, *args, **kwargs)
        self.labels = ['OFF:0 ON:1']
        self.ls1 = taurus.Device('BL13/CT/SERIAL-09')
        self.brightness = 10

    def AddDevice(self, axis):
        pass

    def DeleteDevice(self, axis):
        pass

    def StateOne(self, axis):
        # Just try to communicate with the device
        state = DevState.ALARM
        status_template = 'Device is in %s state.'
        try:
            value = self.ReadOne(axis)
            if value == 1:
                state = DevState.ON
            else:
                state = DevState.OFF
        except Exception,e:
            state = DevState.ALARM
            status_template += ' Exception: %s ' % str(e)
        return (state, status_template % state)

    def ReadOne(self, axis):
        if self.check_light_is_on():
            return 1
        return 0

    def WriteOne(self, axis, value):
        if value == 1:
            self.light_on()
        else:
            self.light_off()
        
    def GetAxisExtraPar(self, axis, name):
        if name == 'Labels':
            return self.labels
        elif name == 'Brightness':
            # RIGHT NOW WE DON'T KNOW HOW TO READ THE BRIGHTNESS
            # THERE IS A COMMAND FOR READING VARIABLES BUT
            # SOME OF THEM ANSWER WITH AN ERROR
            # THERE IS A COMMAND TO 'ENABLE POLLING ON VARIABLES'
            # MAYBE THIS HAS TO BE SET FOR BRIGHTNESS IN ORDER
            # TO BE ABLE TO READ IT
            # BUT WE STILL DON'T KNOW THE VARIALBE NUMBER FOR IT
            return self.brightness
        return None

    def SetAxisExtraPar(self, axis, name, value):
        if name == 'Labels':
            self.labels = value
        elif name == 'Brightness':
            if 0<=value<=100:
                self.brightness = value
                self.set_brightness(value)
            else:
                raise Exception('Brightness should be between 0 and 100. %d received.'%value)


    ################################################################################
    ## COMMUNICATION WITH LS-1
    ################################################################################
    def ask(self, cmd):
        self.ls1.DevSerFlush(2)
        cmd_list = list(cmd + self.calc_crc8_dallas(cmd))
        self.ls1.DevSerWriteChar(map(ord,cmd_list))
        time.sleep(0.2)
        ans_list = map(chr, self.ls1.DevSerReadNBinData(6))
        ans = ''.join(ans_list)
        # print(cmd_list,'->',ans_list)
        return ans

    def calc_crc8_dallas(self, cmd_str):
        '''
        Compute the CRC-8-Dallas and return the char to append in the command
        E2-LS1-000-A1-Dual Led User Manual.pdf:
        ----------------------------------------------------------------------
        ESC 40h <Cmd> <Nb> [<Data0> [<Data1> ...]] <Crc8>
        ESC : synchro command frame start (1Bh)
        40h : word for commande type
        <Cmd> : command code, 80h-Feh
        <Nb> : # of data byte , 0-255
        <Datax> : data bytes, 0-255
        <Crc8> : 8-bit CRC - From ESC to <Datan>
        CRC is : x8 + x5 + x4 + 1 (0x31) <-- normal representation, CRC8 DALAS
        ----------------------------------------------------------------------
        '''
        TABLE=[0x00, 0x5e, 0xbc, 0xe2, 0x61, 0x3f, 0xdd, 0x83,
               0xc2, 0x9c, 0x7e, 0x20, 0xa3, 0xfd, 0x1f, 0x41,
               0x9d, 0xc3, 0x21, 0x7f, 0xfc, 0xa2, 0x40, 0x1e,
               0x5f, 0x01, 0xe3, 0xbd, 0x3e, 0x60, 0x82, 0xdc,
               0x23, 0x7d, 0x9f, 0xc1, 0x42, 0x1c, 0xfe, 0xa0,
               0xe1, 0xbf, 0x5d, 0x03, 0x80, 0xde, 0x3c, 0x62,
               0xbe, 0xe0, 0x02, 0x5c, 0xdf, 0x81, 0x63, 0x3d,
               0x7c, 0x22, 0xc0, 0x9e, 0x1d, 0x43, 0xa1, 0xff,
               0x46, 0x18, 0xfa, 0xa4, 0x27, 0x79, 0x9b, 0xc5,
               0x84, 0xda, 0x38, 0x66, 0xe5, 0xbb, 0x59, 0x07,
               0xdb, 0x85, 0x67, 0x39, 0xba, 0xe4, 0x06, 0x58,
               0x19, 0x47, 0xa5, 0xfb, 0x78, 0x26, 0xc4, 0x9a,
               0x65, 0x3b, 0xd9, 0x87, 0x04, 0x5a, 0xb8, 0xe6,
               0xa7, 0xf9, 0x1b, 0x45, 0xc6, 0x98, 0x7a, 0x24,
               0xf8, 0xa6, 0x44, 0x1a, 0x99, 0xc7, 0x25, 0x7b,
               0x3a, 0x64, 0x86, 0xd8, 0x5b, 0x05, 0xe7, 0xb9,
               0x8c, 0xd2, 0x30, 0x6e, 0xed, 0xb3, 0x51, 0x0f,
               0x4e, 0x10, 0xf2, 0xac, 0x2f, 0x71, 0x93, 0xcd,
               0x11, 0x4f, 0xad, 0xf3, 0x70, 0x2e, 0xcc, 0x92,
               0xd3, 0x8d, 0x6f, 0x31, 0xb2, 0xec, 0x0e, 0x50,
               0xaf, 0xf1, 0x13, 0x4d, 0xce, 0x90, 0x72, 0x2c,
               0x6d, 0x33, 0xd1, 0x8f, 0x0c, 0x52, 0xb0, 0xee,
               0x32, 0x6c, 0x8e, 0xd0, 0x53, 0x0d, 0xef, 0xb1,
               0xf0, 0xae, 0x4c, 0x12, 0x91, 0xcf, 0x2d, 0x73,
               0xca, 0x94, 0x76, 0x28, 0xab, 0xf5, 0x17, 0x49,
               0x08, 0x56, 0xb4, 0xea, 0x69, 0x37, 0xd5, 0x8b,
               0x57, 0x09, 0xeb, 0xb5, 0x36, 0x68, 0x8a, 0xd4,
               0x95, 0xcb, 0x29, 0x77, 0xf4, 0xaa, 0x48, 0x16,
               0xe9, 0xb7, 0x55, 0x0b, 0x88, 0xd6, 0x34, 0x6a,
               0x2b, 0x75, 0x97, 0xc9, 0x4a, 0x14, 0xf6, 0xa8,
               0x74, 0x2a, 0xc8, 0x96, 0x15, 0x4b, 0xa9, 0xf7,
               0xb6, 0xe8, 0x0a, 0x54, 0xd7, 0x89, 0x6b, 0x35]

        crc = 0
        cmd_list = map(ord, cmd_str)
        for i in range(len(cmd_list)):
            char = cmd_list[i]
            crc = TABLE[( crc ^ char ) & 0xFF]
            # THIS LAST LINE WAS WHAT WAS DRIVING ME CRAZY!
            # PEOPLE NORMALLY DO
            # crc = crc ^ char OR crc = (crc ^ char) ^ xor_value
        return chr(crc)

    def light_on(self):
        CMD_LIGHT_ON = '\x1B\x40\xAA\x02\x02\x00'
        self.ask(CMD_LIGHT_ON)
    
    def light_off(self):
        CMD_LIGHT_OFF = '\x1B\x40\xAA\x02\x02\x01'
        self.ask(CMD_LIGHT_OFF)
    
    def check_light_is_on(self):
        CMD_LIGHT_STATE = '\x1B\x40\xAA\x02\x00\x01'
        ans = self.ask(CMD_LIGHT_STATE)
        state = ord(ans[-2])
        return (state & 2) == 0

    def get_brightness(self):
        # how we should access to this value?
        return None

    def set_brightness(self, n):
        self.set_brightness_int(1023*n/100)
  
    def set_brightness_int(self, n):
        CMD_SET_BRIGHTNESS = '\x1B\x40\xA8\x03\x00'
        n = int(n)
        lsb, msb = self.get_brightness_chars(n)
        cmd = CMD_SET_BRIGHTNESS+msb+lsb
        self.ask(cmd)

    def get_brightness_chars(self, n):
        # return lsb, msb
        return chr(n&0xff),chr(n>>8&0x03)
