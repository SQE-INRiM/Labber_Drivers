#!/usr/bin/env python

import InstrumentDriver
import numpy as np
import skrf as rf
import os
from datetime import datetime


class Error(Exception):
    pass

class Driver(InstrumentDriver.InstrumentWorker):
    """ This class implements a S-parameter calibrator for 2-port networks"""

    def myLog(self, message, level: int = 20):
        """Show messages in the Instrument Log preceded by the instrument name"""
        self.log(f'{self.getName()} - {message}', level=level)

    def getFrequencyVector(self, trace):
        if len(trace['y']) == 0:
            return np.array([])
        f0 = trace.get('t0')
        df = trace.get('dt')
        N = int(trace.get('shape')[0])
        return np.linspace(f0, f0+N*df, N)

    def performOpen(self, options={}):
        self.frequency = None
        self.dir = None
        self.database = None
        self.subfolder = None
        self.QSwitchDict = {}
    
        return
    
    def performClose(self, bError=False, options={}):
        """Perform the close instrument connection operation"""
        pass

    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform te Set Value instrument operation. This function should
        return the actual value set by the instrument"""
        
        if 'Input' not in quant.name and 'Current' not in quant.name: 
            # If one changes a quantity that is not expected to change during a measurment, 
            # it means that the user could change the VNA frequency options, therefore...
            self.frequency = None

        if quant.name == 'Database for the SNP files':
            if os.path.isfile(value):
                self.database = os.path.dirname(value)
            
        elif quant.name == 'Sub-folder name' and not self.getValue("Use today's date as sub-folder name"):
            self.subfolder = value

        elif quant.name == 'Calibration method':
            self.QSwitchDict = {}
            quants = []
            if value == 'SOLR':
                quants = ['short', 'open', 'load', 'reciprocal']
            elif value == 'SOLT':
                quants = ['short', 'open', 'load', 'thru']
            elif value == 'TRL':
                quants = ['thru', 'relect', 'line']
            for quant in quants:
                if quant not in self.QSwitchDict:
                    self.QSwitchDict[quant] = None
        elif 'Position' in quant.name:
            standard_name = quant.name.replace('Position of ', '').replace(' standard', '')
            if standard_name in self.QSwitchDict.keys():
                self.QSwitchDict[standard_name] = quant.getValueIndex() #int(value)
            self.myLog(f'Updating QSwitchDict in setValue: {self.QSwitchDict}')
        return value

    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation"""
        
        if quant.name.startswith('Output'):
            #self.log('starts with output')

            value = self.getValue(quant.name.replace('Output', 'Input')).copy()
            #self.log('copy done')

            if len(value['y']) == 0: # This happens if the driver gets an empty trace
                self.myLog(f'No frequency range for the current measurement')
                self.frequency = None

            else:
                self.frequency = rf.Frequency.from_f(self.getFrequencyVector(value))
                if len(self.frequency) == 0:
                    self.myLog(f'No frequency range for the current measurement')
                    self.frequency = None
                else:
                    self.myLog(f'Frequency range of the current measurement: {self.frequency}')
            #self.log('created (or not) frequency vector')
            if self.frequency is not None:
                if self.database is None:
                    self.database = self.getValue('Database for the SNP files')
                if self.dir is None:
                    if self.subfolder is None:
                        self.subfolder =  datetime.today().strftime('%Y_%m_%d__%H_%M_%S')
                    self.dir = os.path.join(self.database, self.subfolder)
                    if not os.path.exists(self.dir):
                        os.makedirs(self.dir)

                if self.getValue('Current switch throw')-1 in self.QSwitchDict.values() and quant.name.endswith('S22'):
                    self.myLog('Starting to create S2P file')

                    # Fills an array with the 4 S-parameters
                    s = np.empty((len(self.frequency), 2, 2), dtype=complex)
                    for i in [1,2]:
                        for j in [1,2]:
                            s[:,i-1,j-1] = self.getValue(f'Input S{i}{j}')['y']

                    # Understands what standard it's dealing with
                    current_standard = [standard_name for standard_name, throw in self.QSwitchDict.items() if throw == self.getValue('Current switch throw')-1][0]
                    self.myLog(f'{current_standard=}')
                    # Creates a network object, naming it as the standard placed on the switch path that is currently selected
                    Matrix = rf.Network(frequency=self.frequency, s=s, name=current_standard)
                    Matrix.write_touchstone(dir=self.dir, form='db')
                    self.myLog(f'Created s2p file for {current_standard} standard')

                elif any(self.getValue('Current switch throw')-1 == self.QSwitchDict.get(transmissive) for transmissive in ['reciprocal', 'thru']) and '/' in quant.name:
                    sw_term = rf.Network(frequency=self.frequency, s=value['y'], name=quant.name.replace('/', '__').replace('Output ', ''))
                    sw_term.write_touchstone(dir=self.dir, form='db')
                    self.myLog(f"Created s1p file for {quant.name.replace('Output ', '')}")
                
                elif self.getValue('Current switch throw')-1 not in self.QSwitchDict.values():
                    self.myLog(f'{self.QSwitchDict}')
        else:
            value = quant.getValue()
        
        if self.isFinalCall(options):
            self.dir = None

        return value

if __name__ == '__main__':
    pass
