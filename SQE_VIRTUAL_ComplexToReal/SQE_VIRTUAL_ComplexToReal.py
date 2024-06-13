#!/usr/bin/env python

import InstrumentDriver
import numpy as np
import skrf as rf
import scipy
from skrf.media import Coaxial
from typing import Union, Optional

class Error(Exception):
    pass

def generate_equidistant_array(
    start: Union[int, float], 
    stop: Optional[Union[int, float]]=None, 
    step: Optional[Union[int, float]]=None, 
    npoints: Optional[int]=None
    ):
    if stop is not None:
        if step is not None and npoints is None:
            return np.arange(start, stop+step, step)
        elif npoints is not None:
            return np.linspace(start, stop, npoints)
        else:
            raise ValueError("You must specify two of stop, step, npoints") 
    else:
        if step is not None and npoints is not None:
            stop = start + (npoints - 1) * step
            return np.linspace(start, stop, npoints)
        else:
            raise ValueError("You must specify two of stop, step, npoints")

def tryAttrs(myDict: dict, attr1, attr2):
    try:
        val1 = myDict[attr1]
    except KeyError:
        val1 = None
    try:
        val2 = myDict[attr2]
    except KeyError:
        val2 = None
    
    if val1 is not None and val2 is not None and val1 != val2:
        raise ValueError(f"Values for '{attr1}' and '{attr2}' are different")

    return val1 if val1 is not None else val2

class Driver(InstrumentDriver.InstrumentWorker):
    """ This class implements a S-parameter calibrator for 2-port networks"""

    def performOpen(self, options={}):
        pass
    
    def performClose(self, bError=False, options={}):
        """Perform the close instrument connection operation"""
        pass

    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform te Set Value instrument operation. This function should
        return the actual value set by the instrument"""
        # do nothing here
        return value

    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation"""

        if 'Out' in quant.name:
            # The correct waveform is requested through the signal connection
            if self.getValue('X-axis Unit') == 'Frequency [Hz]':
                complex_signal = self.readValueFromOther('Complex waveform In-Hz')
            else:
                complex_signal = self.readValueFromOther('Complex waveform In-s')
            # The dict containing the trace is copied. The y-data will be changed to real values, but the x-data stays the same
            value = complex_signal.copy()
            self.log(value.keys())
            if 'Linear' in quant.name:
                value['y'] = np.abs(value['y'])
            elif 'Logarithmic' in quant.name:
                value['y'] = 20*np.log10(np.abs(value['y'])) # Conversion in dB
                if self.getValue('Measurement type') == 'Absolute':
                    value['y'] *= 3 # Further conversion in dBm. The factor 3 accounts for the fact that 1 W = 10^3 mW
            elif 'Real' in quant.name:
                value['y'] = np.real(value['y'])
            elif 'Imaginary' in quant.name:
                value['y'] = np.imag(value['y'])
            elif 'phase' in quant.name.lower(): # If the quantity name contains 'phase', regardless of the case
                value['y'] = np.angle(value['y']) # The phase of the complex vector
                if 'Unwrapped' in quant.name:
                    value['y'] = np.unwrap(value['y']) # The phase is unwrapped if it was requested
                if self.getValue('Phase unit') == 'Degrees': # The phase is converted in degrees if it was requested
                    value['y'] = np.degrees(value['y'])
            
                
                # Builds the frequency vector
                # freqStart = tryAttrs(value, 'x0', 't0')
                # freqStop = tryAttrs(value, 'x1', 't1')
                # freqStep = tryAttrs(value, 'dx', 'dt')
                # npoints = tryAttrs(value, 'npoints', 'shape')
                
        else:
            value = quant.getValue()
        return value

if __name__ == '__main__':
    pass
