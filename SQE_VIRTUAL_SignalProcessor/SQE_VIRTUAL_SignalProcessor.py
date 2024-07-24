#!/usr/bin/env python

import InstrumentDriver
import numpy as np
import numexpr as ne
import pandas as pd
from scipy.signal import savgol_filter, find_peaks
from scipy.optimize import curve_fit
from scipy.stats import linregress
from metas_unclib import np, get_value, get_stdunc, ufloat, ufloatarray, ucomplex, ucomplexarray

class Error(Exception):
    pass

def identity(a):
    return a

def dB(x, n=2):
    return n * 10 * np.log10(x)

def parabula(x, a, b, c):
    x = np.array(x)
    return a*x**2 + b*x +c

class Driver(InstrumentDriver.InstrumentWorker):
    """ This class implements a demodulation driver"""

    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection"""
        self.G = self.BW = self.ripple = None
        pass


    def performClose(self, bError=False, options={}):
        """Perform the close instrument connection operation"""
        pass


    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform the Set Value instrument operation. This function should
        return the actual value set by the instrument"""
        
        return value

    def ConvertToLogScale(self, y):
        if self.getValue('Input class') == 'Power quantity in linear scale':
            y = 10 * np.log10(y)
        if self.getValue('Input class') == 'Root-power quantity in linear scale':
            y = 20 * np.log10(y)
        return y
    
    def ConvertToPowerScale(self, y):
        if self.getValue('Input class') == 'dB':
            y = 10**(y/20)
        elif self.getValue('Input class') == 'dBm':
            y = np.sqrt(10**(y/10)/1000)
        elif self.getValue('Input class') == 'Power quantity in linear scale':
            y = np.sqrt(y)
        return y
    
    def ConvertToRootPowerScale(self, y):
        if self.getValue('Input class') == 'dB':
            y = 10**(y/10)
        elif self.getValue('Input class') == 'dBm':
            y = 10**(y/10)/1000
        elif self.getValue('Input class') == 'Root-power quantity in linear scale':
            y = y**2
        return y
    
    def getXY(self):
        input_dict = self.getValue(self.getValue('Input type') + ' input')
        dx = input_dict['dt']
        N = input_dict['shape'][0]
        x0 = input_dict['t0']  
        return np.linspace(x0, x0+N*dx, N), input_dict['y']
    
    
    def GiveUncToSignal(self, x, y, func: callable = identity):

        y_err = None
        if self.getValue('Consider uncertainty on input') == 'From expression':
            expr = self.getValue('Uncertainty expression')
            if expr in ('', '0'):
                self.setValue('Consider uncertainty on input', 'No')
            if 'y' in expr or 'x' in expr:
                y_err = np.real_if_close(ne.evaluate(expr), local_dict={'y': y, 'x': x})
            else:
                y_err = np.real_if_close(ne.evaluate(expr))
                if y_err.size == 1:
                    y_err = np.full_like(y, y_err)
        elif self.getValue('Consider uncertainty on input') == 'From csv':
            df = pd.read_csv(self.getValue('Uncertainty csv'))
            y_err = np.real_if_close(np.interp(x, df['x'], np.abs(df['y'])) * np.exp(1j*np.interp(x, df['x'], np.angle(df['y']))))
        
        if y_err is not None:
            input_unc = func(y_err)
            if input_signal.dtype != complex:
                input_signal = ufloatarray(input_signal, np.diag(input_unc))
            else:
                input_signal = ucomplexarray(input_signal, np.diag([*(input_unc.real), *(input_unc.imag)]))
        return input_signal
    
    def getBandMetrics(self, x, y_, y_fit):
        
        G = y_fit[get_value(y_fit).argmax()]

        band = x[get_value(y_fit) >= self.G - 3]
        f1, f2 = band[0], band[-1]
        i1_, i2_, = np.argmin(np.abs(x-f1)), np.argmin(np.abs(x-f2))

        if self.getValue('Consider uncertainty on input') != 'No':
            s_f1, s_f2 = get_stdunc(y_fit)[[i1_, i2_]] / np.abs(np.gradient(get_value(y_fit), x)[[i1_, i2_]])
            f1, f2 = ufloat(f1, s_f1), ufloat(f2, s_f2)


        ripple = 2*np.std((y_fit-dB(y_))[i1_:i2_])

        return G, f1, f2, ripple
        
    
    def getBandGap(self, x, y, w: float = 1e9, prominence: float = 0.75):

        dx = x[1]-x[0]

        y_der2 = savgol_filter(y, window_length=int(w / dx), polyorder=4, deriv=2)
        # y_der2 = savgol_filter(y_der2, window_length=int(0.5e9 / dx), polyorder=4)
        min_idxs, _ = find_peaks(-y, prominence=prominence)
        sel_min_idxs = []
        for min_idx in min_idxs:
            if y_der2[min_idx] > 0:
                sel_min_idxs.append(min_idx)
        gap_centers = x[sel_min_idxs]
        if len(gap_centers) == 0:
            return None

        interval_indices = np.where(np.diff(y_der2 > 0))[0]
        x_edges = x[interval_indices]

        if len(x_edges) == 0:
            return None

        x1 = np.max(x_edges[x_edges < np.min(gap_centers)])
        x2 = np.min(x_edges[x_edges > np.max(gap_centers)])

        return x1, x2

    
    def GetTwoBands(self, x, y, w: float = 1e9, prominence: float = 0.75):

        x_lower, x_upper = self.getBandGap(x, get_value(y), w=w, prominence=prominence)

        # The two regions outside the bandgap where there is gain
        x1, y1 = x[x<=x_lower], y[x<=x_lower]
        x1, y1  = x1[get_value(y1)>1], y1[get_value(y1)>1]
        x2, y2 = x[x>=x_upper], y[x>=x_upper]
        x2, y2 = x2[get_value(y2)>1], y2[get_value(y2)>1]
        
        # I fit the two regions with lines, to find their intersection and use it as a guess on the parabula's vertex
        r1 = linregress(x1, dB(get_value(y1)))
        r2 = linregress(x2, dB(get_value(y2)))
        x0 = (r2.intercept - r1.intercept)/(r1.slope-r2.slope)
        y0 = r2.slope * x0 + r2.intercept

        a = (get_value(y1[0])-y0)/(x1[0]-x0)**2 
        b = 2*a*x0
        c = y0 + a*x0**2

        x_fit = np.array([*x1, *x2])
        y_fit = np.array([*y1, *y2])
        
        if self.getValue('Consider uncertainty on input') == 'No':
            popt, pcov = curve_fit(
                parabula, 
                x_fit, 
                dB(y_fit), 
                p0=(a,b,c),
            )
        else:
            popt, pcov = curve_fit(
                parabula, 
                x_fit, 
                dB(np.array(get_value(y_fit))), 
                p0=(a,b,c),
                sigma = get_stdunc(dB(y_fit)),
                absolute_sigma=True
            )
            popt = ufloatarray(popt, pcov)
        
        self.G_l, self.f1_l, self.f2_l, self.ripple_l = self.getBandMetrics(x1, y1, parabula(x1, *popt))
        self.G_u, self.f1_u, self.f2_u, self.ripple_u = self.getBandMetrics(x2, y2, parabula(x2, *popt))

        
    def GetSingleBand(self, x, y):
            
        x_, y_ = x[get_value(y) >= 1], y[get_value(y)>=1]

        x0 = x_[np.argmax(get_value(y_))]
        y0 = np.max(get_value(y_))

        a = (get_value(y_[0])-y0)/(x_[0]-x0)**2 
        b = 2*a*x0
        c = y0 + a*x0**2

        if self.getValue('Consider uncertainty on input') == 'No':
            popt, _ = curve_fit(
                parabula, 
                x_, 
                dB(np.array(get_value(y_))), 
                p0=(a,b,c)
            )
        else:
            popt, pcov = curve_fit(
                parabula, 
                x_, 
                dB(np.array(get_value(y_))), 
                p0=(a,b,c),
                sigma = get_stdunc(dB(y_)),
                absolute_sigma=True
            )
            popt = ufloatarray(popt, pcov)

        self.G, self.f1, self.f2, self.ripple = self.getBandMetrics(x_, y_, parabula(x_, *popt))
        


    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation"""
        x, y = self.getXY()
        
            
        if 'SNR' in quant.name:

            y = self.GiveUncToSignal(x, y, np.abs)
            
            y = self.ConvertToRootPowerScale(y)

            S = y[get_value(y).argmax()] 

            # The noise is computed as the mean of the trace except for 25% of it around the signal peak
            N = np.mean(np.array([
                *y[:np.fmax(get_value(y).argmax()-len(y)//8, 0)], # left of the peak, further than 12.5% the array length
                *y[np.fmin(get_value(y).argmax()-len(y)//8, len(y)-1):] # right of the peak, further than 12.5% the array length
                ]))
            
            SNR = dB(S / N)

            return_func = get_stdunc if 'Uncertainty' in quant.name else get_value
            return return_func(SNR)

        elif any(keyword in quant.name.lower() for keyword in ('gain', '-3 db point', 'ripple')) and 'RB' not in quant.name:

            y = self.GiveUncToSignal(x, y, np.abs)
            y = self.ConvertToRootPowerScale(y)
            
            if self.isConfigUpdated(bReset=True):
                self.GetSingleBand(x, y)
            

            return_func = get_stdunc if 'Uncertainty' in quant.name else get_value
            if 'gain' in quant.name.lower():
                return return_func(self.G)
            elif 'left' in quant.name.lower():
                return return_func(self.f1)
            elif 'right' in quant.name.lower():
                return return_func(self.f1)
            elif 'ripple' in quant.name.lower():
                return return_func(self.ripple)
            
        elif any(keyword in quant.name.lower() for keyword in ('gain', '-3 db point', 'ripple')) and 'RB' not in quant.name:

            y = self.GiveUncToSignal(x, y, np.abs)
            y = self.ConvertToRootPowerScale(y)
            
            if self.isConfigUpdated(bReset=True):
                self.GetTwoBands(x, y)

            return_func = get_stdunc if 'Uncertainty' in quant.name else get_value
            if 'lrb gain' in quant.name.lower():
                return return_func(self.G_l)
            elif 'lrb left' in quant.name.lower():
                return return_func(self.f1_l)
            elif 'lrb right' in quant.name.lower():
                return return_func(self.f1_l)
            elif 'lrb ripple' in quant.name.lower():
                return return_func(self.ripple_l)
            elif 'urb gain' in quant.name.lower():
                return return_func(self.G_u)
            elif 'urb left' in quant.name.lower():
                return return_func(self.f1_u)
            elif 'urb right' in quant.name.lower():
                return return_func(self.f1_u)
            elif 'urb ripple' in quant.name.lower():
                return return_func(self.ripple_u)
            
        else:
            # just return the quantity value
            value = quant.getValue()
        return value

    


if __name__ == '__main__':
    pass
