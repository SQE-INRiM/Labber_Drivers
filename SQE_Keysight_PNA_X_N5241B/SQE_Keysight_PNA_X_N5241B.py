#!/usr/bin/env python

from VISA_Driver import VISA_Driver
import numpy as np
import re

__version__ = "0.0.1"


class Error(Exception):
    pass

class Driver(VISA_Driver):
    """ This class implements the Keysoght 5241B PNA driver"""

    def myLog(self, message, level: int = 20):
        """Show messages in the Instrument Log preceded by the instrument name"""
        self.log(f'{self.getName()} - {message}', level=level)

    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection"""
        # init meas param dict
        self.dMeasParam = {}
        self.range_dict = {}
        self.port_dict = {}
        self.ports = None
        
        # calling the generic VISA open to make sure we have a connection
        VISA_Driver.performOpen(self, options=options)
        # do perform get value for acquisition mode

    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation"""
        value = self.getValue(quant.name)
        # check type of quantity
        if 'Enabled' in quant.name:
            # update list of channels in use
            self.getActiveMeasurements()
            # get selected parameter
            param = quant.name.split(' - ')[0]
            value = (param in self.dMeasParam)
        elif quant.name in ('S11 - Value', 'S21 - Value', 'S12 - Value', 'S22 - Value'):
            # read trace, return averaged data
            data = self.readValueFromOther(quant.name.split(' - ')[0])
            return np.mean(data['y'])
        elif quant.name in ('S11', 'S21', 'S12', 'S22', 'a1/b1_2', 'a2/b2_1', 'A_2', 'B_1',):

            # check if channel is on
            if quant.name not in self.dMeasParam:
                # get active measurements again, in case they changed
                self.getActiveMeasurements()
            if quant.name in self.dMeasParam:
                
                # old parameter handing, select parameter (use last in list)
                sName = self.dMeasParam[quant.name][-1]
                self.writeAndLog("CALC:PAR:SEL '%s'" % sName)
                # if not in continous mode, trig from computer
                bWaitTrace = self.getValue('Wait for new trace')
                bAverage = self.getValue('Average')
                # wait for trace, either in averaging or normal mode
                if bWaitTrace:
                    if bAverage:
                        # set channels 1-4 to set event when average complete (bit 1 start)
                        self.writeAndLog(':SENS:AVER:CLE;:STAT:OPER:AVER1:ENAB 30;:ABOR;:SENS:AVER:CLE;')
                    else:
                        self.writeAndLog(':ABOR;:INIT:CONT OFF;:INIT:IMM;')
                        self.writeAndLog('*OPC') 
                    # wait some time before first check
                    self.wait(0.03)
                    bDone = False
                    while (not bDone) and (not self.isStopped()):
                        # check if done
                        if bAverage:
                            sAverage = self.askAndLog('STAT:OPER:AVER1:COND?')
                            bDone = int(sAverage)>0
                        else:
                            stb = int(self.askAndLog('*ESR?'))
                            bDone = (stb & 1) > 0
                        if not bDone:
                            self.wait(0.1)
                    # if stopped, don't get data
                    if self.isStopped():
                        self.writeAndLog('*CLS;:INIT:CONT ON;')
                        return []
                if quant.name in ('S11', 'S21', 'S12', 'S22', 'a1/b1_2', 'a2/b2_1'):
                    self.writeAndLog('CALC:MEAS:FORM MLOG')
                    # get data as float32, convert to numpy array
                    # old parameter handing
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
                    vector = vComplex
                else:
                    # get data as float32, convert to numpy array
                    # old parameter handing
                    
                    self.write(':CALC:MEAS:FORM MLOG')
                    self.write('CALC:MEAS:FORM:UNIT MLOG, DBM')
                    
                    self.write(':FORM REAL,32;CALC:DATA? FDATA', bCheckError=False)
                    
                    sData = self.read(ignore_termination=True)
                    self.log(sData)
                    if bWaitTrace and not bAverage:
                        self.writeAndLog(':INIT:CONT ON;')
                    # strip header to find # of pointsll 
                    i0 = sData.find(b'#') # (nDig) (nByte) 
                    nDig = int(sData[i0+1:i0+2])
                    nByte = int(sData[i0+2:i0+2+nDig])
                    nData = int(nByte/4)
                    nPts = int(nData/2)
                    # get data to numpy array
                    vData = np.frombuffer(sData[(i0+2+nDig):(i0+2+nDig+nByte)], 
                                        dtype='>f', count=nData)
                    vector = vData
                    
                # get start/stop frequencies
                centerFreq = self.readValueFromOther('Center frequency')
                sweepType = self.readValueFromOther('Sweep type')
                # if log scale, take log of start/stop frequencies
                logX = (sweepType == 'Log')
                lorX = (sweepType == 'Lorentzian')
                if lorX:
                    qEst = self.getValue('Q Value')
                    thetaMax = self.getValue('Maximum Angle')
                    numPoints = self.getValue('# of points')
                    value = quant.getTraceDict(vector, x=self.calcLorentzianDistr(thetaMax, numPoints, qEst, centerFreq))
                else:
                    span = self.readValueFromOther('Span')
                    startFreq = centerFreq - (span/2)
                    stopFreq = centerFreq + (span/2)
                    value = quant.getTraceDict(vector, x0=startFreq, x1=stopFreq,
                                               logX=logX)
            else:
                # not enabled, return empty array
                value = quant.getTraceDict([])
        elif quant.name in ('Wait for new trace',):
            # do nothing, return local value
            value = quant.getValue()

        elif quant.name == 'X-axis values':
            self.write('FORM ASC,0')
            value = self.askAndLog('CALC:MEAS:X?')
            value = value.split(',')
            for n, val in enumerate(value):
                value[n] = float(val)
            value = np.array(value)

        elif 'range' in quant.name and any(keyword in quant.name for keyword in ('Source', 'Receivers', 'Source2')):

            self.log(f'Asking {quant.name}...')
            
            range_name = quant.name.split(' ')[0]
            if range_name not in self.range_dict:
                self.range_dict[range_name] = int(self.ask(f':SENSe:FOM:RNUM? "{range_name}"'))
            range_num = self.range_dict[range_name]
            
            if 'Mode' in quant.name:
                value = self.askAndLog(f':SENS:FOM:RANG{range_num}:COUP?') 
            elif 'Start' in quant.name:
                value = self.askAndLog(f':SENS:FOM:RANG{range_num}:FREQ:STAR?')
            elif 'Stop' in quant.name:
                value = self.askAndLog(f':SENS:FOM:RANG{range_num}:FREQ:STOP?')
            elif 'Center' in quant.name:
                value = (float(self.askAndLog(f':SENS:FOM:RANG{range_num}:FREQ:STOP?')) + float(self.askAndLog(f':SENS:FOM:RANG{range_num}:FREQ:STAR?')) )/2
            elif 'Span' in quant.name:
                value = float(self.askAndLog(f':SENS:FOM:RANG{range_num}:FREQ:STOP?')) - float(self.askAndLog(f':SENS:FOM:RANG{range_num}:FREQ:STAR?'))
            elif 'Sweep type' in quant.name:
                value = self.askAndLog(f':SENSe:FOM:RANG{range_num}:SWE:TYPE?').lower()
                if 'segm' in value:
                    value = 'Lorentzian'
                elif 'lin' in value:
                    value = 'Linear'
                elif 'log' in value:
                    value = 'Log'
            elif 'Offset' in quant.name:
                value = self.askAndLog(f':SENS:FOM:RANG{range_num}:FREQ:OFFS?')
            elif 'Multiplier' in quant.name:
                value = self.askAndLog(f':SENS:FOM:RANG{range_num}:FREQ:MULT?')
            elif 'Divisor' in quant.name:
                value = self.askAndLog(f':SENS:FOM:RANG{range_num}:FREQ:DIV?')
        elif 'on Port' in quant.name  and not 'Port power' in quant.name and not self.getValue('Couple port powers'):
            port_name = quant.name.split(' on ')[-1]
            if port_name not in self.port_dict:
                self.port_dict[port_name] = int(float(self.ask(f'SOUR:PORT:NUM? "{port_name}"')))
            port_num = self.port_dict[port_name]
            if 'Source power' in quant.name:
                offset = self.readValueFromOther('Power offset on ' + port_name)
                port_pow = self.readValueFromOther('Port power on ' + port_name)
                value = port_pow - offset
            elif 'Enable power limit' in quant.name:
                value = bool(self.askAndLog(f':SYST:POW{port_num}:LIM:STAT?'))
            elif 'Power limit' in quant.name:
                value = self.askAndLog(f':SYST:POW{port_num}:LIM?')
        elif quant.name == "X-axis display range":
            value = self.ask(":SENS:FOM:DISP:SEL?").replace('"', '')

        elif "Source attenuation on Port" in quant.name:
            x = quant.name[-1]
            value = str(int(float(self.askAndLog(f'SOUR:POW:ATT? "Port {x}"'))))

        elif quant.name == "Source attenuation":
            value = str(int(float(self.askAndLog(f'SOUR:POW:ATT?'))))

        elif "Attenuation on receiver" in quant.name:
            x = quant.name[-1]
            value = int(float(self.askAndLog(f'SENS:POW:ATT? {x}REC')))


        else:
            # for all other cases, call VISA driver
            value = VISA_Driver.performGetValue(self, quant, options)
            
        return value
    
    def updateDriverValue(self, quant_name):
        self.setValue(quant_name, self.readValueFromOther(quant_name))
        return
    
    def getPowerLimits(self):
        if self.ports is None:
            self.ports = self.ask('SOUR:CAT?')[1:-2].split(',')
        limits = []
        for port in self.ports:
            try:
                if self.getValue('Enable power limit on ' + port):
                    limits.append(self.getValue('Power limit on ' + port))
            except:
                pass
        return limits


    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform the Set Value instrument operation. This function should 
        return the actual value set by the instrument"""
        #self.log(f'Starting to set {quant.name} to a new value!')
        if self.isFinalCall(options) and self.getValue('Sweep type') == 'Lorentzian':
            # get parameters
            centerFreq = self.getValue('Center frequency')
            qEst = self.getValue('Q Value')
            thetaMax = self.getValue('Maximum Angle')
            numPoints = self.getValue('# of points')
            # calculate distribution
            frequencies = self.calcLorentzianDistr(thetaMax, numPoints, qEst, centerFreq)
            data = []
            for freq in frequencies:
                data.append('1')
                data.append('1')
                data.append(str(freq))
                data.append(str(freq))
            dataset = ','.join(data)
            self.writeAndLog(':SENS:SEGM:LIST SSTOP, %s, %s' % (numPoints, dataset))
        
        # update visa commands for triggers
        if 'Enabled' in quant.name:
            # get updated list of measurements in use
            self.getActiveMeasurements()

            param = quant.name.split(' - ')[0]
            
            # old-type handling of traces
            if param in self.dMeasParam:
                # clear old measurements for this parameter
                for name in self.dMeasParam[param]:
                    self.writeAndLog("CALC:PAR:DEL '%s'" % name)

            
            # create new measurement, if enabled is true
            if value:
                newName = ('LabC_%s' % param)
                self.writeAndLog("CALC:PAR:EXT '%s','%s'" % (newName, param))
                # show on PNA screen
                #iTrace = 1 + ['S11', 'S21', 'S12', 'S22'].index(param)
                iTrace = 1 + ['S11', 'S21', 'S12', 'S22', 'a2/b2_1', 'a1/b1_2', 'A_2', 'B_1'].index(param)
#                sPrev = self.askAndLog('DISP:WIND:CAT?')
#                if sPrev.find('EMPTY')>0:
#                    # no previous traces
#                    iTrace = 1
#                else:
#                    # previous traces, add new
#                    lTrace = sPrev[1:-1].split(',')
#                    iTrace = int(lTrace[-1]) + 1
                self.writeAndLog("DISP:WIND:TRAC%d:FEED '%s'" % (iTrace, newName))
                # add to dict with list of measurements
                self.dMeasParam[param] = [newName]
                self.writeAndLog('DISP:WIND:TRAC:Y:COUP:METH ALL')


                
        elif quant.name in ('Wait for new trace',):
            # do nothing
            pass
        
        elif quant.name in ('Range type',):
            # change range if single point
            if value == 'Single frequency':
                self.writeAndLog(':SENS:FREQ:SPAN 0')
                self.writeAndLog(':SENS:SWE:POIN 1')

        elif quant.name == 'Start frequency' and self.getValue('Range type') == 'Start - Stop':
            self.writeAndLog(f':SENS:FREQ:STAR {value}')
            self.setValue('Center frequency', (value + self.getValue('Stop frequency'))/2)
            self.setValue('Span', self.getValue('Stop frequency') - value)

        elif quant.name == 'Stop frequency' and self.getValue('Range type') == 'Start - Stop':
            self.writeAndLog(f':SENS:FREQ:STOP {value}')
            self.setValue('Center frequency', (value + self.getValue('Start frequency'))/2)
            self.setValue('Span', value - self.getValue('Stop frequency'))

        elif quant.name == 'Center frequency' and self.getValue('Range type') == 'Center - Span':
            span = self.getValue('Span')
            self.writeAndLog(f':SENS:FREQ:STAR {value-span/2}')
            self.writeAndLog(f':SENS:FREQ:STOP {value+span/2}')
            self.setValue('Start frequency', value-span/2)
            self.setValue('Stop frequency', value+span/2)

        elif quant.name == 'Span' and self.getValue('Range type') == 'Center - Span':
            center = self.getValue('Center frequency')
            self.writeAndLog(f':SENS:FREQ:STAR {center-value/2}')
            self.writeAndLog(f':SENS:FREQ:STOP {center+value/2}')
            self.setValue('Start frequency', center-value/2)
            self.setValue('Stop frequency', center+value/2)

        elif quant.name in ('Sweep type'):
            # if linear:
            if self.getValue('Sweep type') == 'Linear':
                self.writeAndLog(':SENS:SWE:TYPE LIN')
            #if log:
            elif self.getValue('Sweep type') == 'Log':
                self.writeAndLog(':SENS:SWE:TYPE LOG')
            # if Lorentzian:
            elif self.getValue('Sweep type') == 'Lorentzian':
                # prepare VNA for segment sweep
                self.writeAndLog(':SENS:SWE:TYPE SEGM') 
                self.writeAndLog('DISP:WIND:TABL SEGM') 
                
        elif 'range' in quant.name and any(keyword in quant.name for keyword in ('Source', 'Receivers', 'Source2')):
            
            range_name = quant.name.split(' ')[0]
            if range_name not in self.range_dict:
                self.range_dict[range_name] = int(self.ask(f':SENS:FOM:RNUM? "{range_name}"'))
            range_num = self.range_dict[range_name]
            
            if 'Mode' in quant.name:
                if value == 'Coupled':
                    self.writeAndLog(f':SENS:FOM:RANG{range_num}:COUP 1')
                elif value == 'Un-Coupled':
                    self.writeAndLog(f':SENS:FOM:RANG{range_num}:COUP 0')
                    
            elif self.getValue(range_name + ' range Mode') == 'Un-Coupled':
                if self.getValue(range_name  + ' range Range type') == 'Start - Stop':
                    if 'Start' in quant.name:
                        self.writeAndLog(f':SENS:FOM:RANG{range_num}:FREQ:STAR {value}')
                        self.setValue(range_name  + ' range Center', (value + self.getValue(range_name  + ' range Stop frequency'))/2)
                        self.setValue(range_name  + ' range Span', self.getValue(range_name  + ' range Stop frequency') - value)
                    elif 'Stop' in quant.name:
                        self.writeAndLog(f':SENS:FOM:RANG{range_num}:FREQ:STOP {value}')
                        self.setValue(range_name  + ' range Center', (value + self.getValue(range_name  + ' range Start frequency'))/2)
                        self.setValue(range_name  + ' range Span', value - self.getValue(range_name  + ' range Stop frequency'))
                elif self.getValue(range_name  + ' range Range type') == 'Center - Span':
                    if 'Center' in quant.name:
                        span = self.getValue(range_name + ' range Span')
                        self.writeAndLog(f':SENS:FOM:RANG{range_num}:FREQ:STAR {value-span/2}')
                        self.writeAndLog(f':SENS:FOM:RANG{range_num}:FREQ:STOP {value+span/2}')
                        self.setValue(range_name + ' range Start frequency', value-span/2)
                        self.setValue(range_name + ' range Stop frequency', value+span/2)
                    elif 'Span' in quant.name:
                        center = self.getValue(range_name + ' range Center')
                        self.writeAndLog(f':SENS:FOM:RANG{range_num}:FREQ:STAR {center-value/2}')
                        self.writeAndLog(f':SENS:FOM:RANG{range_num}:FREQ:STOP {center+value/2}')
                        self.setValue(range_name + ' range Start frequency', center-value/2)
                        self.setValue(range_name + ' range Stop frequency', center+value/2)
                elif 'Sweep type' in quant.name and value != 'Lorentzian':
                    self.writeAndLog(f':SENSe:FOM:RANG{range_num}:SWE:TYPE {value.upper()[:3]}')
                elif 'Sweep type' in quant.name and value == 'Lorentzian':
                    pass
                    
            elif self.getValue(range_name + ' range Mode') == 'Coupled':
                if 'Offset' in quant.name:
                    self.writeAndLog(f':SENS:FOM:RANG{range_num}:FREQ:OFFS {value}')
                elif 'Multiplier' in quant.name:
                    self.writeAndLog(f':SENS:FOM:RANG{range_num}:FREQ:MULT {value}')
                elif 'Divisor' in quant.name:
                    self.writeAndLog(f':SENS:FOM:RANG{range_num}:FREQ:DIV {value}')

        elif quant.name == 'Output power' and self.getValue('Couple port powers'):

            
            limits = self.getPowerLimits()
            if any(limit_ < value for limit_ in limits):
                value = min(limits)
                self.myLog(f'The output power is being capped to the limit of {value:.1f} dBm put on an output port')
            self.writeAndLog(f'SOUR:POW {value}')
            value = self.readValueFromOther('Output power')
            if self.getValue('Autorange source attenuation'):
                self.updateDriverValue('Source attenuation')

        elif quant.name == 'Couple port powers':
            #self.log('Eighth elif')
            if value:
                limits = self.getPowerLimits()
                if any(limit_ < self.getValue('Output power') for limit_ in limits):
                    limit = min(limits)
                    self.myLog(f'The output power is being capped to the limit of {limit:.1f} dBm put on an output port')
                    self.writeAndLog(f'SOUR:POW {limit}')
            self.writeAndLog(f'SOUR:POW:COUP {int(value)}')
            self.updateDriverValue('Output power')
            if self.getValue('Autorange source attenuation'):
                self.updateDriverValue('Source attenuation')

        elif quant.name == 'Source attenuation' and not self.getValue('Autorange source attenuation'):
            #self.log('Ninth elif')
            limits = self.getPowerLimits()
            if any(limit_ < self.getValue('Output power') for limit_ in limits):
                limit = min(limits)
                self.myLog(f'The output power is being capped to the limit of {limit:.1f} dBm put on an output port')
                self.writeAndLog(f'SOUR:POW {limit}')
            self.writeAndLog(f'SOUR:POW:ATT {value}')
            self.updateDriverValue('Output power')

        elif quant.name == 'Autorange source attenuation':
            self.writeAndLog(f'SOUR:POW:ATT:AUTO {int(value)}')
            if value:
                self.updateDriverValue('Source attenuation')


        elif 'on Port' in quant.name and 'Source state' not in quant.name:

            port_name = quant.name.split(' on ')[-1]
            if port_name not in self.port_dict:
                self.port_dict[port_name] = int(float(self.ask(f'SOUR:PORT:NUM? "{port_name}"')))
            port_num = self.port_dict[port_name]
            
            if 'Enable power limit' in quant.name:
                if value:
                    limit = self.getValue('Power limit on ' + port_name)
                    if limit < self.getValue('Port power on ' + port_name):
                        self.myLog(f'The port power at {port_name} is being capped to the limit of {limit:.1f} dBm')
                        self.sendValueToOther('Port power on ' + port_name, limit)
                        self.updateDriverValue('Port power on ' + port_name)
                        self.updateDriverValue('Source power on ' + port_name)
                self.writeAndLog(f'SYST:POW{port_num}:LIM:STAT {int(value)}')

            elif 'Power limit' in quant.name:
                if self.getValue('Enable power limit on ' + port_name) and value < self.getValue('Port power on ' + port_name):
                    self.myLog(f'The port power at {port_name} is being capped to the limit of {value:.1f} dBm')
                    self.sendValueToOther('Port power on ' + port_name, value)
                    self.setValue('Port power on ' + port_name, value)
                    self.updateDriverValue('Port power on ' + port_name)
                    self.updateDriverValue('Source power on ' + port_name)
                self.writeAndLog(f'SYST:POW{port_num}:LIM {value}')

            if not self.getValue('Couple port powers'):

                if 'Port power' in quant.name:
                    #self.log(value)
                    if self.getValue('Enable power limit on ' + port_name) and value > self.getValue('Power limit on ' + port_name):
                        limit = self.getValue('Power limit on ' + port_name)
                        self.myLog(f'The port power at {port_name} is being capped to the limit of {limit:.1f} dBm')
                        self.writeAndLog(f':SOUR:POW {limit}, "{port_name}"')
                    else:
                        self.writeAndLog(f':SOUR:POW {value}, "{port_name}"')
                    value = float(self.askAndLog(f':SOUR:POW? "{port_name}"'))
                    #self.log(value)
                    offset = self.getValue('Power offset on ' + port_name)
                    self.setValue('Source power on ' + port_name, value-offset)
                    if self.getValue('Autorange source attenuation on ' + port_name):
                        self.updateDriverValue('Source attenuation on ' + port_name)

                
                elif 'Source power' in quant.name:
                    offset = self.getValue('Power offset on ' + port_name)
                    port_pow = value+offset
                    if self.getValue('Enable power limit on ' + port_name) and port_pow > self.getValue('Power limit on ' + port_name):
                        limit = self.getValue('Power limit on ' + port_name)
                        self.myLog(f'The port power at {port_name} is being capped to the limit of {limit:.1f} dBm')
                        self.writeAndLog(f':SOUR:POW {limit}, "{port_name}"')
                    else:
                        self.writeAndLog(f':SOUR:POW {port_pow}, "{port_name}"')
                    
                    port_pow = float(self.askAndLog(f':SOUR:POW? "{port_name}"'))
                    value = port_pow - offset
                    self.setValue('Port power on ' + port_name, port_pow)
                    
                    if self.getValue('Autorange source attenuation on ' + port_name):
                        self.updateDriverValue('Source attenuation on ' + port_name)


                elif 'Power offset' in quant.name:
                    old_value = quant.getValue()
                    self.writeAndLog(f':SOUR:POW:CORR:OFFS:MAGN {value}, "{port_name}"')
                    new_port_pow = value-old_value+self.getValue('Port power on ' + port_name)
                    if self.getValue('Enable power limit on ' + port_name) and new_port_pow > self.getValue('Power limit on ' + port_name):
                        limit = self.getValue('Power limit on ' + port_name)
                        self.myLog(f'The port power at {port_name} is being capped to the limit of {limit:.1f} dBm')
                        self.writeAndLog(f':SOUR:POW {limit}, "{port_name}"')
                    else:
                        self.writeAndLog(f':SOUR:POW {new_port_pow}, "{port_name}"')
                    self.setValue('Port power on ' + port_name, new_port_pow)

                elif 'Autorange source attenuation' in quant.name:
                    self.writeAndLog(f'SOUR:POW:ATT:AUTO {int(value)}, "{port_name}"')
                    if value:
                        self.updateDriverValue('Source attenuation on ' + port_name)

                elif 'Source attenuation' in quant.name and not self.getValue('Autorange source attenuation on ' + port_name):
                    if self.getValue('Enable power limit on ' + port_name) and float(value) - 30 > self.getValue('Power limit on ' + port_name):
                        limit = self.getValue('Power limit on ' + port_name)
                        self.myLog(f'The port power at {port_name} is being capped to the limit of {limit:.1f} dBm')
                        self.writeAndLog(f':SOUR:POW {limit}, "{port_name}"')
                    self.writeAndLog(f'SOUR:POW:ATT {value}, "{port_name}"')
                    self.updateDriverValue('Port power on ' + port_name)
                    self.updateDriverValue('Source power on ' + port_name)  

        

        else:
            # run standard VISA case 
            self.log('Using standard visa case')
            value = VISA_Driver.performSetValue(self, quant, value, sweepRate, options)
            
        return value 
        
    def getActiveMeasurements(self):
        """Retrieve a list of measurement/parameters currently active"""
        # proceed depending on model
        
        sAll = self.askAndLog("CALC:PAR:CAT:EXT?")
        # strip "-characters
        sAll = sAll[1:-1]
        # parse list, format is channel, parameter, ...
        self.dMeasParam = {}
        lAll = sAll.split(',')
        nMeas = len(lAll)//2
        for n in range(nMeas):
            sName = lAll[2*n] # The nickname given to the trace. e.g.: "MyS11"
            sParam = lAll[2*n + 1] # The actual measured quantity corresponding to the trace. e.g. "S11"
            if sParam not in self.dMeasParam:
                # create list with current name
                self.dMeasParam[sParam] = [sName,]
            else:
                # add to existing list
                self.dMeasParam[sParam].append(sName)
        self.log(self.dMeasParam)
    
    # helper function to calculate Lorentzian frequency distribution 
    def calcLorentzianDistr(self, thetaMax, numPoints, qEst, centerFreq):
        theta = np.linspace(-thetaMax, thetaMax, numPoints)
        freq = np.multiply(centerFreq, (1 - np.multiply(1 / (2*qEst), np.tan(np.divide(theta, 2)))))
        return freq
    


if __name__ == '__main__':
    pass
