#from __future__ import unicode_literals
import InstrumentDriver
from VISA_Driver import VISA_Driver
#import PyVISA
from InstrumentConfig import InstrumentQuantity
import numpy as np
from struct import *
import struct
import re
import imp
import sys

class Error(Exception):
    pass
	
	
class Driver(VISA_Driver):
    """ This class implements the RedPitaya STEMlab-125-14 driver"""

    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection"""
        # start by calling the generic VISA open to make sure we have a connection
        VISA_Driver.performOpen(self, options)  
        
        self.nBit = 14
        self.bitRange = float(2**(self.nBit-1)-1)
        # timeout
        self.timeout_ms = int(1000 * self.dComCfg['Timeout'])
       
        # sampling rate and number of channles is set by default
        self.dt = 1/(125*(10**6))
        self.nCh = 2

        # create list of sampled data
        self.lTrace = [np.array([])] * self.nCh

        
        self.write(':ACQ:RST')
        #self.write(':GEN:RST')
        self.write(':ACQ:DATA:FORMAT BIN')
        self.write(':ACQ:DATA:UNITS VOLTS')
        self.write(':ACQ:DEC 1')
        self.write(':ACQ:AVG ON')
        
        #self.write(':SOUR1:FREQ:FIX 5E6')
        #self.write(':SOUR2:FREQ:FIX 5E6')
        
        #self.write(':SOUR1:BURS:STAT BURST')
        #self.write(':SOUR1:BURS:NCYC 30')
        #self.write(':SOUR2:BURS:STAT BURST')
        #self.write(':SOUR3:BURS:NCYC 30')
        
        self.write(':SOUR1:VOLT 0.1')
        self.write(':SOUR2:VOLT 0.1')
        
        #self.write(':OUTPUT1:STATE ON')
        #self.write(':OUTPUT2:STATE ON')
        
        #self.write(':SOUR1:TRIG INT')
        #self.write(':SOUR2:TRIG INT')
        
    def performArm(self, quant_names, options={}):
        """Perform the instrument arm operation"""
        # make sure we are arming for reading traces, if not return
        self.write(':ACQ:START')
        self.log('ACQ:STARTed WITH Trigger')
        
        signal_names = ['RF_In1','RF_In2',]
        signal_arm = [name in signal_names for name in quant_names]
        if not np.any(signal_arm):
            return
        
           
    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform the Set Value instrument operation. This function should return the actual value set by the instrument"""
        value = VISA_Driver.performSetValue(self, quant, value, sweepRate, options)
        return value
     
    def performGetValue(self, quant, options={}):
        
        #self.log(quant.name)
        if quant.name in ('RF_In1',):
            if not self.isHardwareTrig(options):
                self.write(':ACQ:START')
                self.write(':ACQ:TRIG CH2_PE')
                #self.wait(1)
                #self.write(':OUTPUT1:STATE ON')
                #self.write(':OUTPUT2:STATE ON')
                #self.wait(1)
                #self.log('ACQ:STARTed without Trigger')
                #self.write(':SOUR1:TRIG EXT_PE')
                #self.write(':SOUR2:TRIG EXT_PE')
                
                while 1:
                    self.write(':ACQ:TRIG:STAT?')
                    triggStatus = self.read(None,True)
                    if  triggStatus == b'TD':
                        #self.log(triggStatus)
                        break
                    elif  triggStatus == b'TD\r\n':
                        #self.log(triggStatus)
                        
                        self.write(':ACQ:SOUR1:DATA?')
                        buff_byteSCARTO = self.read(None,True)
                        #self.log(buff_byteSCARTO,30)
                        
                        #self.write(':ACQ:START')
                    else:
                        self.log(triggStatus)   

                self.write(':ACQ:SOUR1:DATA?')
                
                buff_byte = self.read(None,True)
                #self.log(buff_byte,30)
                buff_byteCut = buff_byte[9:len(buff_byte)]
                #self.log(buff_byteCut)
                self.log('Buff length')
                self.log(len(buff_byteCut))
                values = []
                for i in range(0, len(buff_byteCut)-4, 4):
                    values.append(float(struct.unpack('!f',buff_byteCut[i:i+4])[0]))

                    
                t0=0
                self.dictionary_RF_In1 = quant.getTraceDict(values,t0,self.dt)
                
                self.write(':ACQ:SOUR2:DATA?')
                
                buff_byte = self.read(None,True)
                #self.log(buff_byte,30)
                buff_byteCut = buff_byte[7:len(buff_byte)]
                #self.log(buff_byteCut)
                self.log('Buff length')
                self.log(len(buff_byteCut))
                values = []
                for i in range(0, len(buff_byteCut)-4, 4):
                    values.append(float(struct.unpack('!f',buff_byteCut[i:i+4])[0]))

                t0=0
                self.dictionary_RF_In2 = quant.getTraceDict(values,t0,self.dt)

    
        
        # check type of quantity
        if quant.name in ('RF_In1',):
            return self.dictionary_RF_In1
        
        elif quant.name in ('RF_In2',):       
            return self.dictionary_RF_In2
        
        else:
            """Perform the Get Value instrument operation"""
            value = VISA_Driver.performGetValue(self, quant, options)
            return value

if __name__ == '__main__':
    pass