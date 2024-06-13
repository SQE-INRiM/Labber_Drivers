#!/usr/bin/env python
#!/usr/bin/env python

from VISA_Driver import VISA_Driver
import numpy as np
import pyvisa
import time

__version__ = "0.0.1"

class Error(Exception):
    pass

class Driver(VISA_Driver):
    """ This class implements the Rohde&Schwarz Network Analyzer driver"""

    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection"""
        #Connect to the switches
        self.rm = pyvisa.ResourceManager()
        self.RTSwitchBox = self.rm.open_resource(self.getValue('RTSwitchBox address'))
        self.RTSwitchBox.baud_rate = 115200
        self.RTSwitchBox.timeout = 1000
        time.sleep(2)
        try:
            self.RTSwitchBox.query('*IDN?')
        except:
            self.RTSwitchBox.close()
            raise ConnectionError("RTSwitchBox at " + self.getValue('RTSwitchBox address') + " is not responding")
        self.sw1 = self.getValue('Switch on VNA port 1') # e.g. 'A'
        self.sw2 = self.getValue('Switch on VNA port 2') # e.g. 'B'
        
        # init meas param dict
        self.dMeasParam = {}
        # calling the generic VISA open to make sure we have a connection
        VISA_Driver.performOpen(self, options=options)

    def performClose(self, options={}):
        self.RTSwitchBox.close()
        VISA_Driver.performClose(self, options=options)


    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform the Set Value instrument operation. This function should
        return the actual value set by the instrument"""
        if quant.name in ('RTSwitchBox address', 'Switch on VNA port 1', 'Switch on VNA port 2'): 
            value = self.setValue(quant.name, value)

        elif quant.name == 'Current S-parameter':
            x = str(value)[-2] # 1
            y = str(value)[-1] # 2
            self.RTSwitchBox.write(f"{self.sw2} {x}") # 'B 1'
            self.RTSwitchBox.write(f"{self.sw1} {y}") # 'A 2'
            time.sleep(0.3)
            # S21 is refreshed
            self.disableVNAtrace('S21')
            self.enableVNAtrace('S21')
    
        elif quant.name in ('Wait for new trace',):
            # do nothing
            pass
        else:
            # run standard VISA case 
            value = VISA_Driver.performSetValue(self, quant, value, sweepRate, options)
        return value


    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation"""
        # check type of quantity
        if quant.name.startswith('Network'): # e.g. 'Network S12'
            # The switches are set to the configuration needed to read the requested s-parameter
            self.sendValueToOther('Current S-parameter', quant.name[-3:])
            # At this point, the VNA reads "its" S21
            value = self.readValueFromOther('S21')

        elif quant.name in ('S11', 'S21', 'S12', 'S22'):
            # check if channel is on
            if quant.name not in self.dMeasParam:
                # get active measurements again, in case they changed
                self.getActiveMeasurements()
            if quant.name in self.dMeasParam:
                # get trace name from parameter (use last trace in list)
                sName = self.dMeasParam[quant.name][-1]
                self.writeAndLog("CALC:PAR:SEL '%s'" % sName)
                # if not in continous mode, trig from computer
                bWaitTrace = self.getValue('Wait for new trace')
                bAverage = self.getValue('Average')
                # wait for trace, either in averaging or normal mode
                if bWaitTrace:
                    if bAverage:
                        nAverage = int(self.getValue('# of averages'))
                        self.writeAndLog(':SENS:AVER:CLE;:ABOR;')
                    else:
                        self.writeAndLog(':ABOR;:INIT:CONT OFF;:INIT:IMM;*OPC')
                    # wait some time before first check
                    self.wait(0.03)
                    bDone = False
                    while (not bDone) and (not self.isStopped()):
                        # check if done
                        if bAverage:
                            sAverage = self.askAndLog('SENS:AVER:COUN?')
                            bDone = (int(sAverage) >= nAverage)
                        else:
                            stb = int(self.askAndLog('*ESR?'))
                            bDone = (stb & 1) > 0
                        if not bDone:
                            self.wait(0.1)
                    # if stopped, don't get data
                    if self.isStopped():
                        self.writeAndLog('*CLS;:INIT:CONT ON;')
                        return []
                # get data as float32, convert to numpy array
                self.write(':FORM REAL,32;CALC:DATA? SDATA', bCheckError=False)
                sData = self.read(ignore_termination=True)
                if bWaitTrace and not bAverage:
                    self.writeAndLog(':INIT:CONT ON;')
                # strip header to find # of points
                i0 = sData.find(b'#')
                nDig = int(sData[i0+1:i0+2])
                nByte = int(sData[i0+2:i0+2+nDig])
                nData = int(nByte/4)
                nPts = int(nData/2)
                # get data to numpy array
                vData = np.frombuffer(sData[(i0+2+nDig):(i0+2+nDig+nByte)], 
                                      dtype='>f', count=nData)
                # data is in I0,Q0,I1,Q1,I2,Q2,.. format, convert to complex
                mC = vData.reshape((nPts,2))
                vComplex = mC[:,0] + 1j*mC[:,1]
                # get start/stop frequencies
                startFreq = self.readValueFromOther('Start frequency')
                stopFreq = self.readValueFromOther('Stop frequency')
                sweepType = self.readValueFromOther('Sweep type')
                # if log scale, take log of start/stop frequencies
                logX = (sweepType == 'Log')
                value = quant.getTraceDict(vComplex, x0=startFreq, x1=stopFreq,
                                           logX=logX)
            else:
                # not enabled, return empty array
                value = quant.getTraceDict([])
        elif quant.name in ('Wait for new trace', 'Current S-parameter'):
            # do nothing, return local value
            value = quant.getValue()
        else:
            # for all other cases, call VISA driver
            value = VISA_Driver.performGetValue(self, quant, options)
        return value
    
    def enableVNAtrace(self, param: str):
        # get updated list of measurements in use
            self.getActiveMeasurements()
            # clear old measurements for this parameter
            if param in self.dMeasParam:
                for name in self.dMeasParam[param]:
                    self.writeAndLog("CALC:PAR:DEL '%s'" % name)
            # create new measurement
            newName = 'LabC_%s' % param
            self.writeAndLog("CALC:PAR:SDEF '%s','%s'" % (newName, param))
            # show on PNA screen
            iTrace = 1 + ['S11', 'S21', 'S12', 'S22'].index(param)
            self.writeAndLog("DISP:WIND:TRAC%d:FEED '%s'" % (iTrace, newName))
            # add to dict with list of measurements
            self.dMeasParam[param] = [newName]

    def disableVNAtrace(self, param: str):
        # get updated list of measurements in use
            self.getActiveMeasurements()
            # clear old measurements for this parameter
            if param in self.dMeasParam:
                for name in self.dMeasParam[param]:
                    self.writeAndLog("CALC:PAR:DEL '%s'" % name)

    def getActiveMeasurements(self):
        """Retrieve and a list of measurement/parameters currently active"""
        # proceed depending on model
        sAll = self.askAndLog("CALC:PAR:CAT?")
        # strip "-characters
        sAll = sAll[1:-1]
        # parse list, format is channel, parameter, ...
        self.dMeasParam = {}
        lAll = sAll.split(',')
        nMeas = len(lAll)//2
        for n in range(nMeas):
            sName = lAll[2*n] 
            sParam = lAll[2*n + 1]
            if sParam not in self.dMeasParam:
                # create list with current name
                self.dMeasParam[sParam] = [sName,]
            else:
                # add to existing list
                self.dMeasParam[sParam].append(sName)
        
if __name__ == '__main__':
    pass
