#from __future__ import unicode_literals
import InstrumentDriver
from VISA_Driver import VISA_Driver
#import PyVISA
from InstrumentConfig import InstrumentQuantity
import numpy as np
from struct import *
import struct
import re
import imp
import sys
if sys.version[0] == '2' :
    imp.reload(sys)
    sys.setdefaultencoding('utf-8')


class Error(Exception):
    pass
	
	
class Driver(VISA_Driver):
    """ This class implements the Agilent U2542A driver"""

    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection"""
        # add compatibility with pre-python 3 version of Labber
        if not hasattr(self, 'write_raw'):
            self.write_raw = self.write
        # start by calling the generic VISA open to make sure we have a connection
        VISA_Driver.performOpen(self, options)           
           
    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform the Set Value instrument operation. This function should return the actual value set by the instrument"""
        # check type of quantity
        if self.isFirstCall(options):
            self.bWaveUpdated1 = False
            self.bWaveUpdated2 = False
            self.bBitUpdated1 = False
            self.bBitUpdated2 = False
            self.bBitUpdated3 = False
            self.bBitUpdated4 = False
        if quant.name in ('Amplitude waveform ch1','Offset waveform ch1','Output function ch1'):
            quant.setValue(value)
            self.bWaveUpdated1 = True
        elif quant.name in ('Amplitude waveform ch2','Offset waveform ch2','Output function ch2'):
            quant.setValue(value)
            self.bWaveUpdated2 = True
        elif quant.name in ('Bit number ch1','Bit value ch1'):
            quant.setValue(value)
            self.bBitUpdated1 = True
        elif quant.name in ('Bit number ch2','Bit value ch2'):
            quant.setValue(value)
            self.bBitUpdated2 = True
        elif quant.name in ('Bit number ch3','Bit value ch3'):
            quant.setValue(value)
            self.bBitUpdated3 = True
        elif quant.name in ('Bit number ch4','Bit value ch4'):
            quant.setValue(value)
            self.bBitUpdated4 = True
        elif quant.name in ('Enable the analog output'):
            self.write_raw(b':OUTPut?')
            read_bytes = self.read(ignore_termination=True)
            output = read_bytes.decode('ascii')
            if (int(output) != int(value)) :
                self.write_raw(b':OUTPut %d' % int(value))                
        else:
            # run standard VISA case
            value = VISA_Driver.performSetValue(self, quant, value, sweepRate, options)
            return value
        if self.isFinalCall(options):
            if self.bWaveUpdated1:
                # get data
                amplitude = self.getValue('Amplitude waveform ch1')
                offset = self.getValue('Offset waveform ch1')
                function = self.getValueIndex('Output function ch1')
                # write header + data
                if function == 0:
                    self.write_raw(b':APPLy:SINusoid %.4f, %.4f, (@201)' % (amplitude, offset))
                elif function == 1:
                    self.write_raw(b':APPLy:SQUare %.4f, %.4f, (@201)' % (amplitude, offset))
                elif function == 2:
                    self.write_raw(b':APPLy:SAWTooth %.4f, %.4f, (@201)' % (amplitude, offset))
                elif function == 3:
                    self.write_raw(b':APPLy:TRIangle %.4f, %.4f, (@201)' % (amplitude, offset))
                elif function == 4:
                    self.write_raw(b':APPLy:NOISe %.4f, %.4f, (@201)' % (amplitude, offset))
            elif self.bWaveUpdated2:
                # get data
                amplitude = self.getValue('Amplitude waveform ch2')
                offset = self.getValue('Offset waveform ch2')
                function = self.getValueIndex('Output function ch2')
                # write header + data
                if function == 0:
                    self.write_raw(b':APPLy:SINusoid %.4f, %.4f, (@202)' % (amplitude, offset))
                elif function == 1:
                    self.write_raw(b':APPLy:SQUare %.4f, %.4f, (@202)' % (amplitude, offset))
                elif function == 2:
                    self.write_raw(b':APPLy:SAWTooth %.4f, %.4f, (@202)' % (amplitude, offset))
                elif function == 3:
                    self.write_raw(b':APPLy:TRIangle %.4f, %.4f, (@202)' % (amplitude, offset))
                elif function == 4:
                    self.write_raw(b':APPLy:NOISe %.4f, %.4f, (@202)' % (amplitude, offset))
            elif self.bBitUpdated1:
                #get data
                bit_number = int(self.getValue('Bit number ch1'))
                bit_value = self.getValue('Bit value ch1')
                if bit_value :
                    bit_int_value  = int(1)
                else :
                    bit_int_value = int(0)
                #write data 
                self.write_raw(b':SOURce:DIGital:DATA:BIT %d, %d, (@501)' % (bit_int_value, bit_number))
            elif self.bBitUpdated2:
                #get data
                bit_number = int(self.getValue('Bit number ch2'))
                bit_value = self.getValue('Bit value ch2')
                if bit_value :
                    bit_int_value  = int(1)
                else :
                    bit_int_value = int(0)
                #write data 
                self.write_raw(b':SOURce:DIGital:DATA:BIT %d, %d, (@502)' % (bit_int_value, bit_number))
            elif self.bBitUpdated3:
                #get data
                bit_number = int(self.getValue('Bit number ch3'))
                bit_value = self.getValue('Bit value ch3')
                if bit_value :
                    bit_int_value  = int(1)
                else :
                    bit_int_value = int(0)
                #write data 
                self.write_raw(b':SOURce:DIGital:DATA:BIT %d, %d, (@503)' % (bit_int_value, bit_number))
            elif self.bBitUpdated4:
                #get data
                bit_number = int(self.getValue('Bit number ch4'))
                bit_value = self.getValue('Bit value ch4')
                if bit_value :
                    bit_int_value  = int(1)
                else :
                    bit_int_value = int(0)
                #write data 
                self.write_raw(b':SOURce:DIGital:DATA:BIT %d, %d, (@504)' % (bit_int_value, bit_number))


    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation"""
        
        # check type of quantity
        
        if quant.name in ('Read voltages',):
        #To convert the data into actual float number, we need the voltage range and polarity information
            value = []
            little_endian = b''
            resolution = '16'
            x_0=0.0
            dx=1.0
            complete = 0
            
            en_ch1 = self.getValue('Enable signal route input ch1')
            en_ch2 = self.getValue('Enable signal route input ch2')
            en_ch3 = self.getValue('Enable signal route input ch3')
            en_ch4 = self.getValue('Enable signal route input ch4')
            polarity_ch1 = self.getValueIndex('AI polarity ch1')
            polarity_ch2 = self.getValueIndex('AI polarity ch2')
            polarity_ch3 = self.getValueIndex('AI polarity ch3')
            polarity_ch4 = self.getValueIndex('AI polarity ch4')
            range_index_data_ch1 = self.getValueIndex('AI voltage range ch1')
            range_index_data_ch2 = self.getValueIndex('AI voltage range ch2')
            range_index_data_ch3 = self.getValueIndex('AI voltage range ch3')
            range_index_data_ch4 = self.getValueIndex('AI voltage range ch4')
            points = self.getValue('Sample points')
            wait_time = float(points) * 0.001
            
            self.write(':DIGitize',bCheckError=False)
            self.wait(wait_time)
            while (complete == 0):
                self.write('*OPC?',bCheckError=False)
                complete_bytes = self.read(ignore_termination=True)
                complete = complete_bytes.decode('ascii')
                if (int(complete) != 1) :
                    self.wait(wait_time)
            
            self.write(':WAVeform:DATA?',bCheckError=False)
            self.wait(0.1)
            read_bytes =  self.read(ignore_termination=True)
            little_endian = read_bytes[10:len(read_bytes)]
            
            value = convertvalues(little_endian, en_ch1, en_ch2, en_ch3, en_ch4, polarity_ch1, polarity_ch2, polarity_ch3, polarity_ch4, range_index_data_ch1, range_index_data_ch2, range_index_data_ch3, range_index_data_ch4)
            dictionary = quant.getTraceDict(value,x_0,dx)
            return dictionary
        elif quant.name in ('Voltages read from ch1',):
            values = {}
            array1 = []
            
            channel = 1
            values = self.getValue('Read voltages')
            en_ch1 = self.getValue('Enable signal route input ch1')
            en_ch2 = self.getValue('Enable signal route input ch2')
            en_ch3 = self.getValue('Enable signal route input ch3')
            en_ch4 = self.getValue('Enable signal route input ch4')
            array1 = values['y']
            value = get_corresponding_values(array1, channel, en_ch1, en_ch2, en_ch3, en_ch4)
            
            return quant.getTraceDict(value,x0=0.0,dx=1.0)
        elif quant.name in ('Voltages read from ch2',):
            values = {}
            array1 = []
            channel = 2
            values = self.getValue('Read voltages')
            en_ch1 = self.getValue('Enable signal route input ch1')
            en_ch2 = self.getValue('Enable signal route input ch2')
            en_ch3 = self.getValue('Enable signal route input ch3')
            en_ch4 = self.getValue('Enable signal route input ch4')
            array1 = values['y']
            value = get_corresponding_values(array1, channel, en_ch1, en_ch2, en_ch3, en_ch4)
            
            return quant.getTraceDict(value,x0=0.0,dx=1.0)
        elif quant.name in ('Voltages read from ch3',):
            values = {}
            array1 = []
            channel = 3
            values = self.getValue('Read voltages')
            en_ch1 = self.getValue('Enable signal route input ch1')
            en_ch2 = self.getValue('Enable signal route input ch2')
            en_ch3 = self.getValue('Enable signal route input ch3')
            en_ch4 = self.getValue('Enable signal route input ch4')
            array1 = values['y']
            value = get_corresponding_values(array1, channel, en_ch1, en_ch2, en_ch3, en_ch4)
            
            return quant.getTraceDict(value,x0=0.0,dx=1.0)
        elif quant.name in ('Voltages read from ch4',):
           values = {}
           array1 = []
           channel = 4
           values = self.getValue('Read voltages')
           en_ch1 = self.getValue('Enable signal route input ch1')
           en_ch2 = self.getValue('Enable signal route input ch2')
           en_ch3 = self.getValue('Enable signal route input ch3')
           en_ch4 = self.getValue('Enable signal route input ch4')
           array1 = values['y']
           value = get_corresponding_values(array1, channel, en_ch1, en_ch2, en_ch3, en_ch4)
           
           return quant.getTraceDict(value,x0=0.0,dx=1.0)
        # for all other cases, call VISA driver
        else:
            value = VISA_Driver.performGetValue(self, quant, options)
            return value

def  get_corresponding_values(ivalues, channel, en_ch1, en_ch2, en_ch3, en_ch4):
    fvalues = []
    i=0
    while i < len(ivalues):
        if en_ch1:
            if channel == 1:
                fvalues.append(float(ivalues[i]))
                i=i+1
            else :
                i=i+1
        if en_ch2:
            if channel == 2:
                fvalues.append(float(ivalues[i]))
                i=i+1
            else :
                i=i+1
        if en_ch3:
            if channel == 3:
                fvalues.append(float(ivalues[i]))
                i=i+1
            else :
                i=i+1
        if en_ch4:
            if channel == 4:
                fvalues.append(float(ivalues[i]))
                i=i+1
            else :
                i=i+1
    return fvalues
    
def convertvalues(little_endian, en_ch1, en_ch2, en_ch3, en_ch4, polarity_ch1, polarity_ch2, polarity_ch3, polarity_ch4, range_index_data_ch1, range_index_data_ch2, range_index_data_ch3, range_index_data_ch4):
    """Perform the conversion from the little_endian string to the vector containing the data"""
    vector_index_to_range = np.array([10, 5, 2.5, 1.25, 10])
    value = []
    resolution = '16'
    #1->10    #2->5    #3->2.5    #4->1.25    #5->auto

    if en_ch1 :
        range_ch1 = vector_index_to_range[range_index_data_ch1]
    if en_ch2 :
        range_ch2 = vector_index_to_range[range_index_data_ch2]
    if en_ch3 :
        range_ch3 = vector_index_to_range[range_index_data_ch3]
    if en_ch4 :
        range_ch4 = vector_index_to_range[range_index_data_ch4]
    
    #from little_endian string to initial values
    
    iqty_of_values = len(little_endian)/2
    h = "h" * int(iqty_of_values)
    
    ivalues = struct.unpack("<"+h,little_endian)
    
    #polarity == 0 : bipolar
    #polarity == 1 : unipolar
    
    i=0
    while i < len(ivalues):
        if en_ch1:
            if polarity_ch1 == 0:
                value.append(float(((2*float(ivalues[i]))/2**(float(resolution))*range_ch1)))
                i=i+1
            elif polarity_ch1 == 1:
                value.append(float((float(ivalues[i])/2**(float(resolution)) + 0.5)*range_ch1))
                i=i+1
        if en_ch2:
            if polarity_ch2 == 0:
                value.append(float(((2*float(ivalues[i]))/2**(float(resolution))*range_ch2)))
                i=i+1
            elif polarity_ch2 == 1:
                value.append(float((float(ivalues[i])/2**(float(resolution)) + 0.5)*range_ch2))
                i=i+1
        if en_ch3:
            if polarity_ch3 == 0:
                value.append(float(((2*float(ivalues[i]))/2**(float(resolution))*range_ch3)))
                i=i+1
            elif polarity_ch3 == 1:
                value.append(float((float(ivalues[i])/2**(float(resolution)) + 0.5)*range_ch3))
                i=i+1
        if en_ch4:
            if polarity_ch4 == 0:
                value.append(float(((2*float(ivalues[i]))/2**(float(resolution))*range_ch4)))
                i=i+1
            elif polarity_ch4 == 1:
                value.append(float((float(ivalues[i])/2**(float(resolution)) + 0.5)*range_ch4))
                i=i+1
    return value

if __name__ == '__main__':
    pass