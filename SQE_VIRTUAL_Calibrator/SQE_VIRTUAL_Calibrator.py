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

        self.cal_alg = None
        self.getMeasured()
        self.getIdeals()
        self.getOptionals()

    def getMeasured(self):

        if self.getValue('Calibration method') in ['SOLR', 'SOLT']:
            meas_short = rf.Network(self.getValue('Measured short (.s2p file)'))
            meas_open = rf.Network(self.getValue('Measured open (.s2p file)'))
            meas_load = rf.Network(self.getValue('Measured load (.s2p file)'))
            meas_thru = rf.Network(self.getValue('Measured reciprocal (.s2p file)')) if self.getValue('Calibration method') == 'SOLR' else rf.Network(self.getValue('Measured thru (.s2p file)'))
            measured = [meas_short, meas_open, meas_load, meas_thru]
        else:
            meas_thru = rf.Network(self.getValue('Measured thru (.s2p file)'))
            meas_reflect = rf.Network(self.getValue('Measured reflect (.s2p file)'))
            meas_line = rf.Network(self.getValue('Measured line (.s2p file)')) 
            measured = [meas_thru, meas_reflect, meas_line]

        for meas in measured:
            if not (meas.f == measured[0].f).all():
                raise ValueError('The provided measured standards are not defined over the same frequency range')
        
        self.measured = measured
        self.standard_frequency = measured[0].f

    def getIdeals(self):
        
        if self.getValue('Calibration method') in ['SOLR', 'SOLT']:
            ideal_short = rf.Network(self.getValue('Ideal short (.s2p file)'))
            ideal_open = rf.Network(self.getValue('Ideal open (.s2p file)'))
            ideal_load = rf.Network(self.getValue('Ideal load (.s2p file)'))
            ideal_thru = rf.Network(self.getValue('Ideal thru (.s2p file)'))
            ideals = [ideal_short, ideal_open, ideal_load, ideal_thru]
        else: #TRL
            ideal_thru = rf.Network(self.getValue('Ideal thru (.s2p file)'))
            ideal_reflect = rf.Network(self.getValue('Ideal reflect (.s2p file)'))
            ideal_line = rf.Network(self.getValue('Ideal line (.s2p file)')) 
            ideals = [ideal_thru, ideal_reflect, ideal_line]

        for ideal in ideals:
            if not (ideal.f == ideals[0].f).all():
                raise ValueError('The provided ideals standards are not defined over the same frequency range')
        
        if self.standard_frequency[-1] > ideals[0].f[-1] or self.standard_frequency[0] < ideals[0].f[0]:
            raise ValueError("The measured standards are defined in a frequency range not completely included in that of the ideals standards!")
        
        self.ideals = ideals

    def getOptionals(self):

        if self.getValue('Load switch-terms'):
            self.switch_terms = rf.Network(self.getValue('Measured switch-terms (.s2p file)'))
            if not (self.switch_terms.f == self.standard_frequency).all():
                raise ValueError("The provided frequency range for the switch-terms does not match the one of the measured standards!")
        else:
            self.switch_terms = None

        if self.getValue('Load isolation'):
            self.isolation = rf.Network(self.getValue('Measured isolation (.s2p file)'))
            if not (self.isolation.f == self.standard_frequency).all():
                raise ValueError("The provided frequency range for the isolation does not match the one of the measured standards!")
        else:
            self.isolation = None
    
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
        if quant.name.startswith('Corrected'): # and self.already_opened[quant.name[-3:]]:
            # if self.isFinalCall(options):
            #     self.log('is final call')
            if self.cal_alg is None:
                # this block is accessed just once during the measurement
                self.getFreqFrom('Raw S11')
                self.runCalibration() 
                self.log('Ran calibration', bCheckError=False)
            
            #self.signal_calls[quant.name[-3:]] += 1 # Updates the number of times the particular trace has been requested
            x = int(quant.name[-2]) # the second to last character in the quantity name. in 'S21' it is 2
            y = int(quant.name[-1])  # the last character in the quantity name. in 'S21' it is 1
            self.log(f'Requested correction of S{x}{y}')
            CorrectedMatrix = self.getCorrectedMatrix() # this line uses the calibration algorithm generated above to compute the corrected S matrix
            CorrectedTrace = CorrectedMatrix.s[:, x-1, y-1]
            value = quant.getTraceDict(CorrectedTrace, x=self.DUT_frequency)
            self.log(f'Correction of S{x}{y} was successful')
        else:
            value = quant.getValue()
        return value

    
    def getFreqFrom(self, quant_name: str):
        '''
        Retrieves the frequency range of the particular measurement.
        '''
        #DUT_Dict = self.readValuefromOther('Raw S11')
        DUT_Dict = self.getValue(quant_name)
        if DUT_Dict is None:
            raise ValueError('No Trace received')
        freqStart = tryAttrs(DUT_Dict, 'x0', 't0')
        freqStop = tryAttrs(DUT_Dict, 'x1', 't1')
        freqStep = tryAttrs(DUT_Dict, 'dx', 'dt')
        npoints = tryAttrs(DUT_Dict, 'npoints', 'shape')
        if isinstance(npoints, tuple):
            npoints = npoints[0]
        f =  generate_equidistant_array(start=freqStart, stop=freqStop, step=freqStep, npoints=npoints)
        self.log(f'Freq start: {f[0]:.3g}, freq stop: {f[-1]:.3g}, npoints: {len(f)}')
        if f[-1] > self.standard_frequency[-1] or f[0] < self.standard_frequency[0]:
            raise ValueError("The measurement is being performed over a frequency range not completely included in that of the measured standards!")
        self.DUT_frequency = f
        
    def runCalibration(self):
        
        #Interpolating the measured standards to the measuremenet frequency range
        interp_sw_terms = self.switch_terms
        if self.switch_terms is not None:
            interp_sw_terms.interpolate_self(self.DUT_frequency)
            self.log(f'{interp_sw_terms.s.shape}')
            interp_sw_terms = (interp_sw_terms.s11, interp_sw_terms.s22)

        interp_iso = self.isolation
        if self.isolation is not None:
            interp_iso.interpolate_self(self.DUT_frequency)
            self.log(f'{interp_iso.s.shape}')

        interp_meas = self.measured
        for meas in interp_meas:
            meas.interpolate_self(self.DUT_frequency)
        self.log(f'{interp_meas[0].s.shape}')


        if self.getValue('Calibration method') == 'SOLR':
            cal_alg = rf.UnknownThru(measured=interp_meas, ideals=self.ideals, switch_terms=interp_sw_terms, isolation=interp_iso)
        elif self.getValue('Calibration method') == 'SOLT':
            cal_alg = rf.SOLT(measured=interp_meas, ideals=self.ideals, switch_terms=interp_sw_terms, isolation=interp_iso)
        else: #TRL
            cal_alg = rf.TRL(measured=interp_meas, ideals=self.ideals, switch_terms=interp_sw_terms, isolation=interp_iso)
        cal_alg.run()
        self.cal_alg = cal_alg
    
    def getCorrectedMatrix(self):
        # Creating the raw S matrix of the DUT
        s = np.empty((len(self.DUT_frequency), 2, 2), dtype=complex)
        for i in [1,2]:
            for j in [1,2]:
                s[:,i-1,j-1] = self.getValue(f'Raw S{i}{j}')['y'] 
        RawMatrix = rf.Network(f=self.DUT_frequency, s=s)
        self.log(f'{s.shape}')
        self._CorrectedMatrix = self.cal_alg.apply_cal(RawMatrix) 
        # If the block above is not accessed, it means that we are inside the same step, therefore the code doesn't compute a new Corrected matrix
        return self._CorrectedMatrix

if __name__ == '__main__':
    pass
