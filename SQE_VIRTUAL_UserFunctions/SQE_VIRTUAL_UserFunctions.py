# -*- coding: utf-8 -*-
"""
Created on Mon Jun 13 18:00:55 2022

@author: NM_User
"""

# Copyright 2014-2021 Keysight Technologies
import InstrumentDriver
import time
from InstrumentConfig import InstrumentQuantity
import numpy as np
from scipy.optimize import curve_fit
from scipy.signal import savgol_filter
import random
import os
from scipy.fftpack import fft, fftfreq, fftshift
#import Labber


#client = Labber.connectToServer('localhost')

#resistence_meas = client.connectToInstrument('Lakeshore 32xAC', dict(interface='GPIB', addess='1'))

class Error(Exception):
    pass


class Driver(InstrumentDriver.InstrumentWorker):
    """ This class implements a demodulation driver"""

    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection"""
        #global here

    def performClose(self, bError=False, options={}):
        """Perform the close instrument connection operation"""
        pass

    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform the Set Value instrument operation. This function should
        return the actual value set by the instrument"""
        self.fitPerformed = False
        return value

    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation"""
        '''
        if quant.name in ('R',):
            for temperature in (0, 3):
                temperature = 5 * self.getValue('R')
            #resistence= resistence_meas.getValue('Resistence 1')
               # time.sleep(1)                                                      #1 sec of deelay
            #temperature= 5*resistence
            return temperature
        ''' 
        # check type of quantity
        if quant.name in ('T',):
            temperature= 5*self.getValue('R')


          # return float(temperature)         
            return temperature  
        else:
            value = quant.getValue();
            return value


if __name__ == '__main__':
    pass

# client.close()
