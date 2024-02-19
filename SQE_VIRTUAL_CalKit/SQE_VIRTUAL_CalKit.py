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
        if self.getValue('Calibration method') == 'SOLR':
            self.QSwitchDict = {standard_name: self.getValue(f'Position of {standard_name} standard') for standard_name in ['short', 'open', 'load', 'reciprocal']}
        elif self.getValue('Calibration method') == 'SOLT':
            self.QSwitchDict = {standard_name: self.getValue(f'Position of {standard_name} standard') for standard_name in ['short', 'open', 'load', 'thru']}
        elif self.getValue('Calibration method') == 'TRL':
            self.QSwitchDict = {standard_name: self.getValue(f'Position of {standard_name} standard') for standard_name in ['thru', 'reflect', 'line']}
        else:
            self.QSwitchDict = {}
    
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
        
        # If the requested quantitity is a Corrected S-parameter and the virtual driver has been already started
        if quant.name.startswith('Output'):
            value = self.getValue(quant.name.replace('Output', 'Input'))
            if str(self.getValue('Selected switch')) in self.QSwitchDict.keys() and quant.name.endswith('S22'):
                if value is None:
                    raise ValueError('No Trace received')
                
                # Builds the frequency vector
                freqStart = tryAttrs(value, 'x0', 't0')
                freqStop = tryAttrs(value, 'x1', 't1')
                freqStep = tryAttrs(value, 'dx', 'dt')
                npoints = tryAttrs(value, 'npoints', 'shape')
                if isinstance(npoints, tuple):
                    npoints = npoints[0]
                f =  generate_equidistant_array(start=freqStart, stop=freqStop, step=freqStep, npoints=npoints)

                # Fills an array with the 4 S-parameters
                s = np.empty((len(f), 2, 2), dtype=complex)
                for i in [1,2]:
                    for j in [1,2]:
                        s[:,i-1,j-1] = self.getValue(f'Input S{i}{j}')['y']
        
                # Creates a network object, naming it as the standard placed on the switch that is currently selected
                Matrix = rf.Network(f=f, s=s, name=[standard_name for standard_name, switch in self.QSwitchDict.items() if switch == self.getValue('Selected switch')][0])
                Matrix.write_touchstone(dir=self.getValue('Folder to save s2p files in'), form='db')
        else:
            value = quant.getValue()
        return value

if __name__ == '__main__':
    pass
