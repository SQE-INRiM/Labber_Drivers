# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
Created on Wed Oct  4 09:36:47 2023

@author: NM_User
"""

#import clr
import sys
import time
import serial
import InstrumentDriver
from InstrumentConfig import InstrumentQuantity
from scipy.optimize import curve_fit
from scipy.signal import savgol_filter
import random
import os
from scipy.fftpack import fft, fftfreq, fftshift

'''
clr.AddReference('Ivi.Visa')
clr.AddReference('System.Windows.Forms')
clr.AddReference('Metas.Instr.Driver')
from System import TimeSpan
from System.IO import Path
from InstrumentConfig import InstrumentQuantity
from System.Threading import Thread
from System.Diagnostics import Stopwatch
from Ivi.Visa import ISerialSession, GlobalResourceManager, SerialParity, SerialStopBitsMode
'''

        
class QSwitchBox:
    '''
    This class contains methods to control QSwitchBox from python. It can be imported in any python script.
    '''

    
    def __init__(self, COM):            #Serial Conf.
        '''
        A serial connection with QSwitchBox is established immediately when an object of this class is created
        -----------------------------------------------
        Parameters:
        COM : string the serial port to be used
        -----------------------------------------------
        Returns:
        None
        '''
        self.arduino = serial.Serial(port=COM, baudrate=115200, timeout=.1)
        time.sleep(2) # Wait for the connection to set-up
        #self.arduino = serial.Serial(COM, baudrate=115200, timeout=.1)
        #time.sleep(2) # Wait for the connection to set-up

    
    def write_read(self, x):  # Function to form a communication between Arduino and Control Panel
        '''
        Sends a command to QSwitchBox and returns the corresponding answer
        -----------------------------------------------
        Parameters:
        x : string command to be sent to QSwitchBox
        -----------------------------------------------
        Returns:
        data: bytes return message from the QSwitchBox
        '''
        self.arduino.write(bytes(x, 'utf-8'))
        time.sleep(0.05)
        data = self.arduino.readline()
        return data

    def resetAll(self):
        '''
        Sends a reset command to QSwitchBox. This will put all switches in the open position
        -----------------------------------------------
        Parameters:
        None
        -----------------------------------------------
        Returns:
        None
        '''
        message = self.write_read("reset")
        while message != b'resetNow':
                time.sleep(1)
                message = self.write_read("reset")
        print('Resetting all the switches into initial state')
        #self.log('Reset')
        time.sleep(2) #Allow all the switches to reset
        
    def setWaitTime(self, PulseWidth):           #PulseWidth instead delayTime
        '''
        Sets the width of the control pulse to be sent to the cryogenic switches by the QSwitchBox.
        The pulse width must be between 4 and 10000 ms
        -----------------------------------------------
        Parameters:
        delayTime : float command to be sent to QSwitchBox
        -----------------------------------------------
        Returns:
        None
        '''
        if PulseWidth < 10001.00 and PulseWidth > 4.00:
            print("Setting a Pulse Width of", PulseWidth, " ms")
            deneme = "del" + str(PulseWidth)  # Arduino only reads the wait time if command starts with "del". Adds it to user input string
            toSent = self.write_read(deneme)  # Send command to Arduino
            #print(deneme)
            #print(type(deneme))
            while toSent != b'dataTime':
                time.sleep(1)
                toSent = self.write_read(deneme)
            print("Pulse Width successfully set")
        else:  # If the user input is not in between the scope it will print an error message
            print("ERROR: Please enter a value between 4-10000 ms. If it is a fractional number, use \".\" instead of \",\"")
            
    def portConnect(self, port):  # First action for first button RF PIN 1 Closed
        '''
        Connect a port
        -----------------------------------------------
        Parameters:
        port : int port number
        -----------------------------------------------
        Returns:
        num: string string corresponting to the port that has been connected
        '''
        if port == 1:
            num = "one"
            stringMessage = b'executed1'
            print(num)
        elif port == 2:
            num = "three"
            stringMessage = b'executed3'
        elif port == 3:
            num = "five"
            stringMessage = b'executed5'
        elif port == 4:
            num = "seven"
            stringMessage = b'executed7'
        elif port == 5:
            num = "nine"
            stringMessage = b'executed9'
        elif port == 6:
            num = "eleven"
            stringMessage = b'executed11'
        else: print("Invalid port") 
        print(num)
        messageArduino = self.write_read(num)  # Sends Arduino the signal "one", and Arduino will reads and use it to activate relays.
        print(num)
        self.lastused= num                     #take the value of num, for revert function
        print("Power-on signal sent to PORT", port,". Please wait for the confirmation message...")
        
        while messageArduino != stringMessage:
            print("ERROR: Relays are not responding. Trying again...")
            time.sleep(1)
            messageArduino = self.write_read(num)
        print("\nCONFIRMATION: Relays are working properly. Successfully connected.")
        
        time.sleep(2)
        
        return num  # saves the last used one.
    
    def portDisconnect(self, port):
        '''
        Disconnect a port
        -----------------------------------------------
        Parameters:
        port : int port number
        -----------------------------------------------
        Returns:
        num: string string corresponding to the port that has been connected
        '''

        if port == 1:
            num = "two"
            stringMessage = b'executed2'
        elif port == 2:
            num = "four"
            stringMessage = b'executed4'
        elif port == 3:
            num = "six"
            stringMessage = b'executed6'
        elif port == 4:
            num = "eight"
            stringMessage = b'executed8'
        elif port == 5:
            num = "ten"
            stringMessage = b'executed10'
        elif port == 6:
            num = "twelve"
            stringMessage = b'executed12'
        else: print("Invalid port")
        
        messageArduino = self.write_read(num)
        print("Power-off signal sent to PORT", port, ". Please wait for the confirmation message...")
        
        while messageArduino != stringMessage:
            print("ERROR: Relays are not responding. Trying again...")
            time.sleep(1)
            messageArduino = self.write_read(num)
        print("\nCONFIRMATION: Relays are working properly. Successfully disconnected.")
        
        time.sleep(2)
        
        return num
    
    def revertSwitch(self, lastused):
        '''
        Checks what is the last port that has been closed and opens it
        -----------------------------------------------
        Parameters:
        lastused : string the last port that has been closed
        -----------------------------------------------
        Returns:
        None
        '''
        
        if lastused == "one":
            messageArduino = self.write_read("two")
            time.sleep(1.5)
            print(messageArduino)
            while messageArduino != b'executed2':
                time.sleep(1)
                messageArduino = self.write_read("two")
            print("Port 1 was connected, now disconnected")
            
        elif lastused == "three":
            messageArduino = self.write_read("four")
            time.sleep(1.5)
            while messageArduino != b'executed4':
                time.sleep(1)
                messageArduino = self.write_read("four")
            print("Port 2 was connected, now disconnected")
    
        elif lastused == "five":
            messageArduino = self.write_read("six")
            time.sleep(1.5)
            while messageArduino != b'executed6':
                time.sleep(1)
                messageArduino = self.write_read("six")
            print("Port 3 was connected, now disconnected")
    
        elif lastused == "seven":
            messageArduino = self.write_read("eight")
            time.sleep(1.5)
            while messageArduino != b'executed8':
                time.sleep(1)
                messageArduino = self.write_read("eight")
            print("Port 4 was connected, now disconnected")
    
        elif lastused == "nine":
            messageArduino = self.write_read("ten")
            time.sleep(1.5)
            while messageArduino != b'executed10':
                time.sleep(1)
                messageArduino = self.write_read("ten")
            print("Port 5 was connected, now disconnected")
    
        elif lastused == "eleven":
            messageArduino = self.write_read("twelve")
            time.sleep(1.5)
            while messageArduino != b'executed12':
                time.sleep(1)
                messageArduino = self.write_read("twelve")
            print("Port 6 was connected, now disconnected")
        else:
            print("All the switches are open. This is in the initial state.")
            time.sleep(1)                                                       #aggiunto dopo


    

class Driver(InstrumentDriver.InstrumentWorker):
    """ This class implements a demodulation driver"""
    
    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection"""
        #global here
        # message = self.write_read("reset")
        #Connect to QSwitchBox
        #COM = selectPort()
        COM = "COM4"
    
        #Create a QSwitchBox instance with immediate connection to QSwitchBox
        self.switch = QSwitchBox(COM)
    
        #Reset all switches
        #switch.resetAll()

        #Set Pulse Width in ms between 4 and 10000 ms
        PulseWidth = 1000.00                                
        self.switch.setWaitTime(PulseWidth)
      
        #Select the coaxial switch port you want to use
        port = 1
        
        
        #Connect the selected port
        self.lastused = self.switch.portConnect(port)
 
        #Disconnect the selected port
        #self.lastused = self.switch.portDisconnect(port)
 
        #Open all the swithes before exiting the program
        print("Exiting the script")
        self.switch.revertSwitch(self.lastused)
        
    

           
    def performClose(self, bError=False, options={}):
        """Perform the close instrument connection operation"""
        pass

    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform the Set Value instrument operation. This function should
        return the actual value set by the instrument"""
        self.fitPerformed = False
        if quant.name in ('Port'):
           # self.log('start')
           port=quant.setValue('Port')
           print(value)
           print(type(port))
           self.switch.revertSwitch(self.lastused)              #disable all switchs before connect another one
           self.switch.portConnect(port)                        #connection 
           print(port)
           return port
        if quant.name in ('PulseWidth'):
            PulseWidth = quant.setValue('PulseWidth')
            self.switch.setWaitTime(PulseWidth)
            
    
    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation"""
        pass

if __name__ == '__main__':
        pass