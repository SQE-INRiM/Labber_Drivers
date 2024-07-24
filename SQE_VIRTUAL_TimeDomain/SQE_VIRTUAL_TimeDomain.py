#!/usr/bin/env python

import InstrumentDriver
import numpy as np
from skrf.mathFunctions import psd2TimeDomain


class Error(Exception):
    pass

class Driver(InstrumentDriver.InstrumentWorker):
    """ This class implements a S-parameter calibrator for 2-port networks"""

    def performOpen(self, options={}):
    
        return
    
    def performClose(self, bError=False, options={}):
        """Perform the close instrument connection operation"""
        pass

    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform te Set Value instrument operation. This function should
        return the actual value set by the instrument"""
        
        return value

    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation"""
        
        if quant.name == 'Time-domain output':
            input_dict = self.getValue(self.getValue('Input type') +' input')
            signal = input_dict['y']
            if len(signal) == 0:
                input_dict = self.readValueFromOther(self.getValue('Input type') +' input')
                signal = input_dict['y']
            df = input_dict['dt']
            N = input_dict['shape'][0]
            f0 = input_dict['t0']  
            
            t, TD = psd2TimeDomain(np.linspace(f0, f0+N*df, N), signal+0j)
            if not self.getValue('Keep negative time values'):
                self.log('Discarding negative time')
                t, TD = t[t>=0], TD[t>=0] # Negative time values are discarded
            else:
                self.log("Keeping negative time")
            self.log(f'Time resolution = {(t[1]-t[0]):.3g}') 
            self.log(f'Observation time = {t[-1]:.3g} s')
            value = quant.getTraceDict(TD, x0=t[0], x1=t[-1])
            
        else:
            value = quant.getValue()
    

        return value

if __name__ == '__main__':
    pass
