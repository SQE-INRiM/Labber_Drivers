#!/usr/bin/env python

from VISA_Driver import VISA_Driver
import BaseDriver
import numpy as np
import csv

__version__ = "0.0.5"

class Error(Exception):
    pass

class Driver(VISA_Driver):
    """ This class implements the LakeShore 37xAC driver"""
        
    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection"""
        self.isInKelvin = np.full(16, False)
        self.isInWatts = {'Sample': False, 'Warm-up': False, 'Still': False}
        self.heaters = {'Sample': '0', 'Warm-up': '1', 'Still': '2'}

        try:
           # start by calling the generic VISA open to make sure we have a connection
           VISA_Driver.performOpen(self, options=options)

        except Error as e:
            # re-cast errors as a generic communication error
            msg = str(e)
            raise BaseDriver.CommunicationError(msg)

    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform the Set Value instrument operation."""
        try:

            quant.setValue(value)

            # 'Settings' quantities

            if quant.name[-1] in ('1','2','3','4','5','6','7','8'):
              
                name = quant.name[:-2]
                dConfigChannel = int(quant.name[-1])
              
                if name == 'Show Ch':
                    #This control is makes the submenu visible in instrument server, no instrument communication
                    return value
                
                elif name == 'Sensor Name':
                    sCmd = 'INNAME "%s"' %(value)
                    self.writeAndLog(sCmd)
                    self.log('Command sent: ' + sCmd)
                    return value
                
                # elif name == 'Preferred Units':
                #     cfgCmd = 'INTYPE? %s' %(str(dConfigChannel))
                #     cfgVals = self.askAndLog(cfgCmd).split(',')
                #     cfgVals[-1] = '1' if value == 'K' else '2'
                #     sCmd = 'INTYPE %s,%s' %(str(dConfigChannel), ','.join(cfgVals))
                #     self.writeAndLog(sCmd)
                #     return value

                elif name in ('Excitation Mode', 'Autorange', 'Resistance Range',
                              'Voltage Range', 'Current Range'):
                    # Based on which mode is used, the range is chosen
                    if self.getValue('Excitation Mode %s' %(str(dConfigChannel))) == 'Voltage':
                        dExcitationMode = self.getValueIndex('Excitation Mode %s' %(str(dConfigChannel)))
                        dVoltageRange = self.getValueIndex('Voltage Range %s' %(str(dConfigChannel)))+1
                        dAutorange = self.getValueIndex('Autorange %s' %(str(dConfigChannel)))
                        dResistanceRange = self.getValueIndex('Resistance Range %s' %(str(dConfigChannel)))+1
                        dCSoff = 0 # turn excitation on always
                        # Send command to change quantities
                        sCmd = 'RDGRNG %s,%s,%s,%s,%s,%s' %(str(dConfigChannel), 
                             str(dExcitationMode), str(dVoltageRange), str(dResistanceRange), 
                             str(dAutorange), str(dCSoff))
                        self.writeAndLog(sCmd)
                        self.log('Command sent: ' + sCmd)
                        return value
                       
                    elif self.getValue('Excitation Mode %s' %(str(dConfigChannel))) == 'Current':
                        dExcitationMode = self.getValueIndex('Excitation Mode %s' %(str(dConfigChannel)))
                        dCurrentRange = self.getValueIndex('Current Range %s' %(str(dConfigChannel)))+1
                        dAutorange = self.getValueIndex('Autorange %s' %(str(dConfigChannel)))
                        if dAutorange == 1:
                            #set resistance range to dummy if autorange is on
                            dResistanceRange = 1
                        else:
                            dResistanceRange = self.getValueIndex('Resistance Range %s' %(str(dConfigChannel)))+1
                        dCSoff = 0 # turn excitation on always
                        # Send command to change quantities
                        sCmd = 'RDGRNG %s,%s,%s,%s,%s,%s' %(str(dConfigChannel), 
                              str(dExcitationMode), str(dCurrentRange), str(dResistanceRange), 
                              str(dAutorange), str(dCSoff))
                        self.writeAndLog(sCmd)
                        self.log('Command sent: ' + sCmd)
                        return value

                elif name in ('Filter', 'Filter Settle Time', 'Filter Window'):
                    filterBool = self.getCmdStringFromValue('Filter %s' %(str(dConfigChannel)))
                    filterSettleTime = self.getValue('Filter Settle Time %s' %(str(dConfigChannel)))
                    filterWindow = self.getValue('Filter Window %s' %(str(dConfigChannel)))
                    cmd = 'FILTER %s,%s,%s,%s' %(str(dConfigChannel), str(filterBool),
                        str(filterSettleTime), str(filterWindow))
                    self.writeAndLog(cmd)
                    self.log('Command sent: ' + cmd)
                    return value
          
          # 'Advanced Settings' quantities

            elif quant.name in ('Apply Settings', 'Channel Number', 'Channel Enabled', 'Dwell Time',
                                'Change Pause', 'Curve Number (config)', 'Temperature Coefficient (config)'):
                if quant.name == 'Apply Settings':
                    # Read out quantities
                    channel = int(self.getValue('Channel Number'))
                    enabled = self.getCmdStringFromValue('Channel Enabled')
                    dwell = int(self.getValue('Dwell Time'))
                    pause = int(self.getValue('Change Pause'))
                    curveNumber = int(self.getValue('Curve Number (config)'))
                    tempCoefficient = self.getCmdStringFromValue('Temperature Coefficient (config)')
                    # Send command to configure channel
                    cmd = 'INSET %s,%s,%s,%s,%s,%s' %(str(channel), str(enabled), str(dwell),
                        str(pause), str(curveNumber), str(tempCoefficient))
                    self.writeAndLog(cmd)
                    self.log('Command sent: ' + cmd)                
                else:
                    pass
                return value
       

            elif quant.name in ('Upload Data', 'Path', 'Curve Number (upload)', 'Curve Name', 'Sensor Serial Number',
                                'Format', 'Setpoint Limit', 'Temperature Coefficient (upload)'):
                if quant.name == 'Upload Data':
                    # Read out quantities
                    path = self.getValue('Path')
                    curveNumber = int(self.getValue('Curve Number (upload)'))
                    curveName = self.getValue('Curve Name')
                    sensorSN = self.getValue('Sensor Serial Number')
                    curveFormat = self.getCmdStringFromValue('Format')
                    setpointLimit = self.getValue('Setpoint Limit')
                    tempCoefficient = self.getCmdStringFromValue('Temperature Coefficient (upload)')
                    # Call class function to upload curve (defined below)
                    self.uploadCurve(path, curveNumber, curveName, sensorSN, curveFormat, 
                                     setpointLimit, tempCoefficient)
                else:
                    pass
                return value

            elif 'Heater' in quant.name:
                heaterName, name = quant.name.split(' Heater ')
                self.log(f'{heaterName}, {name}')

                if name in ('Input Channel', 'Temperature Control Mode',):
                    sOutputStatus = self.askAndLog('OUTMODE? %s' %(self.heaters[heaterName]))
                    sOutputList = sOutputStatus.split(',')
                    if name == 'Input channel':
                        sOutputList[1] = value
                        sCmd = 'OUTMODE ' + self.heaters[heaterName] + ',' + ','.join(sOutputList)
                        self.writeAndLog(sCmd)
                        self.log('Command sent: ' + sCmd)
                    if name == 'Temperature Control Mode':
                        if value == 'Closed loop (PID)':
                            sOutputList[0] = '5'
                        elif value == 'Open loop (Manual)':
                            sOutputList[0] = '2'
                        else: 
                            sOutputList[0] = '0'
                        sCmd = 'OUTMODE ' + self.heaters[heaterName] + ',' + ','.join(sOutputList)
                        self.writeAndLog(sCmd)
                        self.log('Command sent: ' + sCmd)
                    return value

                elif name in ('Temperature Ramp','Temperature Ramp Rate'):
                    dTempRamp = int(self.getValueIndex(heaterName+' Heater Temperature Ramp'))
                    dTempRampRate = float(self.getValue(heaterName+' Heater Temperature Ramp Rate'))
                    sCmd = 'RAMP %s,%s,%s' %(self.heaters[heaterName], str(dTempRamp), str(dTempRampRate))
                    self.writeAndLog(sCmd)
                    self.log('Command sent: ' + sCmd)
                    return value

                if name in ('P - Proportional', 'I - Integral', 'D - Derivative'):
                    dP = self.getValue(heaterName+' Heater P - Proportional')
                    dI = self.getValue(heaterName+' Heater I - Integral')
                    dD= self.getValue(heaterName+' Heater D - Derivative')
                    sCmd = 'PID %s,%s,%s,%s' %(self.heaters[heaterName], str(dP), str(dI), str(dD))
                    self.writeAndLog(sCmd)
                    self.log('Command sent: ' + sCmd)
                    return value
              
                # elif name in ('Resistance'):
                #     sCmd = self.askAndLog('HTRSET? %s' %(self.heaters[heaterName])).split(',')
                #     sCmd[0] = str(value)
                #     self.writeAndLog('HTRSET %s, ' %(self.heaters[heaterName]) +','.join(sCmd))
                #     return value
            
                elif name in ('Power Range'):
                    if heaterName == 'Sample':
                        heater_ranges = {option: str(n) for n, option in enumerate(['Off', '100 nW', '1 uW', '10 uW', '100 uW', '1 mW', '10 mW', '100 mW', '1 W'])}
                        sCmd = 'RANGE 0, %s' %(heater_ranges[value])
                    else:
                        sCmd = 'RANGE %s, %s' %(self.heaters[heaterName], str(int(value)))
                    self.writeAndLog(sCmd)
                    self.log('Command sent: ' + sCmd)
                    return value
            
                elif name in ('Temperature Setpoint'):
                    inputChannel = int(self.readValueFromOther(heaterName + ' Heater Input Channel'))
                    self.setInKelvin(inputChannel)
                    sCmd = 'SETP %s, %s' %(self.heaters[heaterName], str(value))
                    self.writeAndLog(sCmd)
                    self.log('Command sent: ' + sCmd)
                    return value
                
                elif name in ('Manual Output Power'):
                    self.setInWatts(heaterName)
                    sCmd = 'MOUT %s,%s' %(self.heaters[heaterName], str(value))
                    self.writeAndLog(sCmd)
                    return value


            else:
                # for all other quantities, call the generic VISA driver
                return VISA_Driver.performSetValue(self, quant, sweepRate, options=options)

        except Error as e:
           # re-cast errors as a generic communication error
           msg = str(e)
           raise BaseDriver.CommunicationError(msg)
        
    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation"""

        # start with setting current quant value
        value = quant.getValue()
        
        try:

            # 'Settings' quantities

            if quant.name[-1] in ('1','2','3','4','5','6','7','8'):
                name = quant.name[:-2]
                channel = int(quant.name[-1])

                if name == 'Show Ch':
                    #This control is makes the submenu visible in instrument server, no instrument communication
                    return value
                
                elif name == 'Sensor Name':
                    sCmd = 'INNAME? %s' % str(channel)
                    value = self.askAndLog(sCmd)
                    return value
                
                # elif name == 'Preferred Units':
                #     sCmd = 'INTYPE? %s' %(str(channel))
                #     value = int(self.askAndLog(sCmd).split(',')[-1])
                #     return value

                elif name in ('Excitation Mode', 'Autorange', 'Resistance Range', 
                             'Voltage Range', 'Current Range'):
                    # Read out the status of the resistance range for the configured channel
                    # Format: <mode>,<excitation>,<range>,<autorange>,<cs off>
                    sCmd = 'RDGRNG? %s' % str(channel)
                    #sCmd = 'RDGRNG? 1'
                    sRangeStatus = self.askAndLog(sCmd)
                    listRangeStatus = sRangeStatus.split(',')
                    if name == 'Excitation Mode':
                        value = int(listRangeStatus[0])
                    elif name in ('Voltage Range','Current Range'):
                        value = int(listRangeStatus[1])-1
                    elif name == 'Resistance Range':
                        value = int(listRangeStatus[2])-1
                    elif name in ('Autorange'):
                        value = int(listRangeStatus[3])
                    return value
                
                elif name in ('Rapid temperature'):
                    sCmd3 = 'RDGK? %s' %(int(channel))
                    sTempStatus = self.askAndLog(sCmd3)
                    self.log('Command sent: ' + sCmd3)
                    self.log('Answer received: '+ sTempStatus)
                    value = float(sTempStatus)
                    return value

                elif name in ('Temperature', 'Resistance', 'Excitation Power'):
                    
                    self.log(f'Measuring {quant.name} with the instrument')
                    # Send command to switch to channel
                    sCmd1 = 'SCAN %s,0' %(str(channel))
                    self.writeAndLog(sCmd1)
                    # Send command to wait until settling of channel - for Model 370, this requires a workaorund
                    model = self.getModel()
                    if model == 'Lakeshore 370AC':
                        dAutorange = self.getValueIndex('Autorange %s' %(str(channel)))
                        filterBool = int(self.getCmdStringFromValue('Filter %s' %(str(channel))))
                        timeFilter = int(self.getValue('Filter Settle Time %s' %(str(channel))))
                        timeout = 50 # in seconds
                        waitLoop = 0.05 # in seconds
                        waitEnd = 4 # in seconds to wait for readout to settle
                        n = 0 # timer
                        while not self.isStopped():
                            status = self.askAndLog('RDGST? %s' %(str(channel)))
                            # The instrument is likely settled when there is no error in status query bits 2,3,4,6,7
                            if (int(status) & 220) == 0: # 220 = 2^2 + 2^3 + 2^4 + 2^6 + 2^7
                                if filterBool == 1:
                                    self.wait(timeFilter + waitEnd)
                                    self.log('Wait for %s s (includes filter settle time)' %(str(timeFilter + waitEnd)))
                                else:
                                    self.wait(waitEnd)
                                    self.log('Wait for %s s' %(str(waitEnd)))
                                break
                            # Timeout
                            elif n > int(timeout/waitLoop):
                                break
                            n += 1
                    elif model == 'Lakeshore 372AC':

                        ## ORIGINAL CODE FROM KEYSIGHT
                        #settledMeasure0 = 2
                        #while not self.isStopped():
                        #    settled = self.askAndLog('RDGSTL?')
                        #    settledMeasure1 = int(settled.split(',')[1].strip())
                        #    if settledMeasure0 == 0 and settledMeasure1 == 0:
                        #        break
                        #    settledMeasure0 = settledMeasure1
                        #    self.wait(0.05)




                        ##USING THE SAME WORKAROUND OF THE 370AC Model - Lele/Luca 11-04-2024
                        dAutorange = self.getValueIndex('Autorange %s' %(str(channel)))
                        filterBool = int(self.getCmdStringFromValue('Filter %s' %(str(channel))))
                        timeFilter = int(self.getValue('Filter Settle Time %s' %(str(channel))))
                        timeout = 50 # in seconds
                        waitLoop = 0.05 # in seconds
                        waitEnd = 4 # in seconds to wait for readout to settle
                        n = 0 # timer
                        while not self.isStopped():
                            status = self.askAndLog('RDGST? %s' %(str(channel)))
                            # The instrument is likely settled when there is no error in status query bits 2,3,4,6,7
                            if (int(status) & 220) == 0: # 220 = 2^2 + 2^3 + 2^4 + 2^6 + 2^7
                                if filterBool == 1:
                                    self.wait(timeFilter + waitEnd)
                                    self.log('Wait for %s s (includes filter settle time)' %(str(timeFilter + waitEnd)))
                                else:
                                    self.wait(waitEnd)
                                    self.log('Wait for %s s' %(str(waitEnd)))
                                break
                            # Timeout
                            elif n > int(timeout/waitLoop):
                                break
                            n += 1


                        # Send command to request measurement result
                    value = 0.
                    m = 0 # timeout timer
                    while value == 0 and m < 20:
                        if name == 'Temperature':
                            sCmd3 = 'RDGK? %s' %(int(channel))
                            sTempStatus = self.askAndLog(sCmd3)
                            self.log('Command sent: ' + sCmd3)
                            value = float(sTempStatus)
                        elif name == 'Resistance':
                            sCmd3 = 'RDGR? %s' %(int(channel))
                            sTempStatus = self.askAndLog(sCmd3)
                            self.log('Command sent: ' + sCmd3)
                            value = float(sTempStatus)
                        elif name == 'Excitation Power':
                            sCmd3 = 'RDGPWR? %s' %(int(channel))
                            sTempStatus = self.askAndLog(sCmd3)
                            self.log('Command sent: ' + sCmd3)
                            value = float(sTempStatus)
                        if value == 0:
                            # If the value has 'settled' to an error, include an additional wait 
                            self.wait(0.5)
                            self.log('Instrument not settled - wait for 0.5s')
                        m += 1
                    # get resistance range from hardware
                    self.readValueFromOther('Resistance Range %s' %(str(channel)))
                    return value
                    
                    
                

                elif name in ('Filter', 'Filter Settle Time', 'Filter Window'):
                    cmd = 'FILTER? %s' % str(channel)
                    filterStatus = self.askAndLog(cmd)
                    self.log('Filter status instr reply:' + filterStatus)
                    listFilterStatus = filterStatus.split(',')
                    if name == 'Filter':
                        value = int(listFilterStatus[0])
                    if name == 'Filter Settle Time':
                        value = int(listFilterStatus[1])
                    if name == 'Filter Window':
                        value = int(listFilterStatus[2])
                    return value

           # 'Advanced Settings' quantities

            elif quant.name in ('Channel Number', 'Channel Enabled', 'Dwell Time', 'Change Pause',
                                'Curve Number (config)', 'Temperature Coefficient (config)'):
                if quant.name == 'Channel Number':
                    # This quantity cannot be queried from the instrument
                    pass
                else:
                    channel = int(self.getValue('Channel Number'))
                    cmd = 'INSET? %s' %(str(channel))
                    channelStatus = self.askAndLog(cmd)
                    self.log('Channel config instr reply:' + channelStatus)
                    listChannelStatus = channelStatus.split(',')
                    if quant.name == 'Channel Enabled':
                        value = int(listChannelStatus[0])
                    if quant.name == 'Dwell Time':
                        value = int(listChannelStatus[1])
                    if quant.name == 'Change Pause':
                        value = int(listChannelStatus[2])
                    if quant.name == 'Curve Number (config)':
                        value = int(listChannelStatus[3])
                    if quant.name == 'Temperature Coefficient (config)':
                        value = int(listChannelStatus[4])
                return value


            elif quant.name in ('Path', 'Curve Number (upload)', 'Curve Name', 'Sensor Serial Number',
                                'Format', 'Setpoint Limit', 'Temperature Coefficient (upload)'):
                if quant.name in ('Path', 'Curve Number (upload)'):
                    pass
                else:
                    curveNumber = int(self.getValue('Curve Number (upload)'))
                    cmd = 'CRVHDR? %s' %(str(curveNumber))
                    curveStatus = self.askAndLog(cmd)
                    self.log('Curve info instr reply:' + curveStatus)
                    listCurveStatus = curveStatus.split(',')
                    if quant.name == 'Curve Name':
                        value = listCurveStatus[0]
                    if quant.name == 'Sensor Serial Number':
                        value = listCurveStatus[1]
                    if quant.name == 'Format':
                        value = int(listCurveStatus[2])
                    if quant.name == 'Setpoint Limit':
                        value = float(listCurveStatus[3])
                    if quant.name == 'Temperature Coefficient (upload)':
                        value = int(listCurveStatus[4])
                return value
            
            elif 'Heater' in quant.name:
                heaterName, name = quant.name.split(' Heater ')
                
                self.log(f'{heaterName}, {name}')

                if name in ('Input Channel', 'Temperature Control Mode'):
                    sOutputStatus = self.askAndLog('OUTMODE? %s' %(self.heaters[heaterName]))
                    sOutputList = sOutputStatus.split(',')
                    if name == 'Input channel':
                        value = sOutputList[1]
                    elif name == 'Temperature Control Mode':
                        value = sOutputList[0]
                    return value


                elif name in ('Temperature Ramp','Temperature Ramp Rate'):
                    sRampStatus = self.askAndLog('RAMP? %s' %(self.heaters[heaterName]))
                    listRampStatus = sRampStatus.split(',')
                    if name == 'Temperature Ramp':
                        value = int(listRampStatus[0])
                    elif name == 'Temperature Ramp Rate':
                        value = float(listRampStatus[1])
                    return value
           
                elif name in ('P - Proportional', 'I - Integral', 'D - Derivative'):
                    sPIDStatus = self.askAndLog('PID? %s' %(self.heaters[heaterName]))
                    listPIDStatus = sPIDStatus.split(',')
                    if quant.name == 'P - Proportional':
                        value = float(listPIDStatus[0])
                    elif quant.name == 'I - Integral':
                        value = float(listPIDStatus[1])
                    elif quant.name == 'D - Derivative':
                        value = float(listPIDStatus[2])
                    return value
                
                # elif name in ('Resistance'):
                #     value = float(self.askAndLog('HTRSET? %s' %(self.heaters[heaterName])).split(',')[0])
                #     return value


                elif name in ('Power range'):
                    if heaterName == 'Sample':
                        heater_ranges = {str(n): option for n, option in enumerate(['Off', '100 nW', '1 uW', '10 uW', '100 uW', '1 mW', '10 mW', '100 mW', '1 W'])}
                        msg = self.askAndLog('RANGE? 0')
                        value = heater_ranges[msg]
                    else:
                        value = bool(self.askAndLog('RANGE? %s' %self.heaters[heaterName]))
                    return value
                

                elif name in ('Temperature Setpoint'):
                    inputChannel = int(self.readValueFromOther(heaterName + ' Heater Input Channel'))
                    self.setInKelvin(inputChannel)
        
                    self.askAndLog('SETP? %s' %(self.heaters[heaterName]))
                    return value
            
            
                elif name in ('Output Power', 'Manual Output Power'):
                    self.setInWatts(heaterName)
                    if name == 'Output Power':
                        if heaterName == 'Sample':
                            sCmd = 'HTR?'
                        else:
                            sCmd = 'AOUT? %s' %(self.heaters[heaterName])
                        value = float(self.askAndLog(sCmd))
                        powerRange = self.readValueFromOther(heaterName + ' Heater Power Range')
                        
                        value *= powerRange / 100
                    elif name == 'Manual Output Power':
                        self.askAndLog('MOUT? %s' %(self.heaters[heaterName]))
                    return value
                    

        except Error as e:
            # re-cast errors as a generic communication error
            msg = str(e)
            raise BaseDriver.CommunicationError(msg)
        
    def setInKelvin(self, inputChannel: int):
        if not self.isInKelvin[inputChannel-1]:
            sInputStatus = self.askAndLog('INTYPE? %s' %(str(inputChannel)))
            sInputList = sInputStatus.split(',')
            sInputList[-1] = '1' 
            sCmd = 'INTYPE %s,%s' %(str(inputChannel), ','.join(sInputList))
            self.writeAndLog(sCmd)
            self.log('The preferred units for channel %d have been changed to K')
            self.isInKelvin[inputChannel-1] = True
        return
    
    def setInWatts(self, heaterName: str):
        if not self.isInWatts[heaterName]:
            sHtrSetStatus = self.askAndLog('HTRSET? %s' %(self.heaters[heaterName]))
            sHtrSetList = sHtrSetStatus.split(',')
            sHtrSetList[-1] = '2'
            self.writeAndLog('HTRSET %s,%s' %(self.heaters[heaterName], ','.join(sHtrSetList)))
            self.log('Output display style set to power mode')
            self.isInWatts[heaterName] = True
        return
    
    def uploadCurve(self, path, curveNumber, curveName, sensorSN, curveFormat,
                    setpointLimit, tempCoefficient):
        ## Upload a calibration curve to the instrument - use CRVHDR and CRVPT
        # Erase previous curve
        cmd = 'CRVDEL %s' %(str(curveNumber))
        self.writeAndLog(cmd)
        self.log('Command sent ' + cmd)
        # Configure the curve header on the instrument
        cmd = 'CRVHDR %s,%s,%s,%s,%s,%s' %(str(curveNumber), str(curveName),
            str(sensorSN), str(curveFormat), str(setpointLimit),
            str(tempCoefficient))
        self.writeAndLog(cmd)
        self.log('Command sent ' + cmd)
        # Import data from .txt file (format: rows with 'resistance,temperature')
        resList = []
        tempList = []
        with open(path, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter = ',')
            for row in reader:
                resList.append(row[0])
                tempList.append(row[1])
        del resList[0] #remove first row - excludes header
        del tempList[0] #remove first row - excludes header
        del resList[-1] #remove last row - prevents entry of all zeroes
        del tempList[-1] #remove last row - prevents entry of all zeroes
        # Write data points to instrument
        N = len(resList)
        if N > 200:
            msg = 'Maximum curve point number of 200 exceeded'
            raise Exception(msg)
        for i in range(0,N):
            cmd = 'CRVPT %s,%s,%s,%s' %(str(curveNumber), str(i), str(resList[i]),
                str(tempList[i]))
            self.writeAndLog(cmd)
            self.log('Command sent ' + cmd)

if __name__ == '__main__':
    pass