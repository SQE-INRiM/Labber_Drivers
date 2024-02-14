# -*- coding: utf-8 -*-
"""
Created on Mon Jun 13 18:00:55 2022

@author: NM_User
"""

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
if sys.version[0] == '2' :
    imp.reload(sys)
    sys.setdefaultencoding('utf-8')


class Error(Exception):
    pass
	
	
class Driver(VISA_Driver):
    """ This class implements the Agilent U2542A driver"""

    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection"""
        # add compatibility with pre-python 3 version of Labber
        if not hasattr(self, 'write_raw'):
            self.write_raw = self.write
        # start by calling the generic VISA open to make sure we have a connection
        VISA_Driver.performOpen(self, options)           
           
    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform the Set Value instrument operation. This function should return the actual value set by the instrument"""
        # check type of quantity
        # run standard VISA case
        value = VISA_Driver.performSetValue(self, quant, value, sweepRate, options)
        return value


    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation"""
        
        # check type of quantity
        
        if quant.name in ('Voltage ch1',):
            
            self.write('ROUTe:TERMinals FRONt1',bCheckError=False)
            self.wait(0.01)
            self.write('READ?',bCheckError=False)
            self.wait(0.01)
            value_to_convert =  self.read(ignore_termination=True)
            value = value_to_convert.decode()
            
            return float(value)
        if quant.name in ('Voltage ch2',):
            
            self.write('ROUTe:TERMinals FRONt2',bCheckError=False)
            self.wait(0.01)
            
            self.write('READ?',bCheckError=False)
            self.wait(0.01)
            value_to_convert =  self.read(ignore_termination=True)
            value = value_to_convert.decode()
            
            return float(value)
        # for all other cases, call VISA driver
        else:
            value = VISA_Driver.performGetValue(self, quant, options)
            return value

if __name__ == '__main__':
    pass