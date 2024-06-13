import InstrumentDriver
import numpy as np
import numexpr as ne

class Driver(InstrumentDriver.InstrumentWorker):
    """ This class implements a simple signal generator driver"""
    

    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection"""
        pass


    def performClose(self, bError=False, options={}):
        """Perform the close instrument connection operation"""
        pass


    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform the Set Value instrument operation. This function should
        return the actual value set by the instrument"""
        # just return the value
        return value


    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation"""
        # proceed depending on quantity
        if quant.name == 'Spectrum':
            # if asking for signal, start with getting values of other controls

            # frequency array is built
            f0 = self.getValue('Start frequency')
            f1 = self.getValue('Stop frequency')
            n_points = int(self.getValue('Number of points'))
            f = np.linspace(f0, f1, n_points)

            # The input expression is evaluated
            param_dict = eval("dict("+self.getValue('Parameters')+")")

            if self.getValue('Representation') == "Polar":
                mag = ne.evaluate(self.getValue('Magnitude'), {'f': f, 'pi': np.pi, 'e': np.e}, param_dict)
                phase = ne.evaluate(self.getValue('Phase'), {'f': f, 'pi': np.pi, 'e': np.e}, param_dict)
                signal = mag*np.exp(1j*phase)

            else: #self.getValue('Representation') == "Cartesian"
                re = ne.evaluate(self.getValue('Real part'), {'f': f, 'pi': np.pi, 'e': np.e}, param_dict)
                im = ne.evaluate(self.getValue('Imaginary part'), {'f': f, 'pi': np.pi, 'e': np.e}, param_dict)
                signal = re + 1j*im

            
            # add noise
            if self.getValue('Add noise'): 
                signal = signal * (1+np.sqrt(np.random.uniform(0, self.getValue('Magnitude noise'), len(signal))))  * np.exp(1.j * np.random.uniform(0, self.getValue('Phase noise') * np.pi, len(signal)))

            # apply gain and offset
            signal = self.getValue('Gain') * signal + self.getValue('Offset')

            # create trace object that contains spectral info
            try:
                trace = quant.getTraceDict(signal, t0=0.0, dt=f[1]-f[0])
            except Exception:
                trace = quant.getTraceDict(signal, t0=0.0, dt=1.0)

            # finally, return the trace object
            return trace
        else: 
            # for other quantities, just return current value of control
            return quant.getValue()


