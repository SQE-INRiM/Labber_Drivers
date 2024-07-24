#!/usr/bin/env python

import InstrumentDriver
import numpy as np
from scipy.signal import savgol_filter
from scipy.stats import linregress

def phase(x):
    return np.unwrap(np.angle(x))

def dB(x):
    return 20 * np.log10(x)

def anti_dB(x):
    return 10**(x/20)

def lin_trend(x, y):
    res = linregress(x, y)
    return res.intercept + res.slope * x

def log_trend(x, y):
    res = linregress(x, dB(y))
    return anti_dB(res.intercept + res.slope * x)


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
        self.log(f"{quant.name} is being requested")

        if quant.name in ("Real trend", "Complex trend"):
            input_dict = self.getValue(quant.name.replace('trend', 'input signal'))
            signal = input_dict['y']
            if len(signal) == 0:
                input_dict = self.readValueFromOther(quant.name.replace('trend', 'input signal'))
                signal = input_dict['y']
            df = input_dict['dt']
            N = input_dict['shape'][0]
            f0 = input_dict['t0']

            self.log("Input signal aquired")

            if self.getValue('Method') == 'Savitsky-Golay filter':

                if self.getValue('Specify window as...') == 'BW':
                    window_length = int(self.getValue('BW') // df) 
                else:
                    window_length = int(self.getValue('Number of points'))
                
                if window_length <= 1:
                    raise ValueError(f"The provided window is smaller or comparable to the spacing of the x-axis, that is {df:.4f}")
                
                polyorder = np.fmin(int(self.getValue('Degree of polynomial')), window_length-1)

                mag_trend = savgol_filter(np.abs(signal), window_length=window_length, polyorder=polyorder, mode='interp') 

                if self.getValue('Input type') == 'Complex':
                    phase_trend = savgol_filter(phase(signal), window_length=window_length, polyorder=polyorder, mode='interp')

            else:

                if self.getValue('Method') == "Mean value":
                    mag_trend = np.full(N, np.mean(np.abs(signal)))

                elif self.getValue('Method') == "Linear fit":
                    mag_trend = lin_trend(np.linspace(f0, f0+N*df), np.abs(signal)) 

                elif self.getValue('Method') == "Linear fit on log scale":
                    mag_trend = log_trend(np.linspace(f0, f0+N*df), np.abs(signal)) 
                
                if self.getValue('Input type') == 'Complex':
                    phase_trend = lin_trend(phase(signal))

            value = input_dict.copy()

            if self.getValue('Input type') == 'Complex':
                value['y'] = mag_trend * np.exp(1j*phase_trend)
            else:
                value['y'] = mag_trend

        elif quant.name in ("Real de-trended signal", "Complex de-trended signal"):
            input_dict = self.getValue(quant.name.replace('de-trended', 'input'))
            signal = input_dict['y']
            trend = self.getValue(quant.name.replace('de-trended signal', 'trend'))['y']
            value = input_dict.copy()
            if self.getValue('Input type') == 'Complex':
                value['y'] = (np.abs(signal)-np.abs(trend)) * np.exp(1j*(phase(signal)-phase(trend)))

        else:
            value = quant.getValue()

        return value

if __name__ == '__main__':
    pass
