from VISA_Driver import VISA_Driver
import time

class Driver(VISA_Driver):
    """ This class re-implements the VISA driver"""

    def sim900_module_ask(self, port, module_cmd, timeout = 0.5, bCheckError=False):
        """This function tries to get a value from a SIM 900 module in a smart way
        without directly connecting in passthrough mode. This is important because
        any intermediate calls to the SIM 900 (like setting a value) should accumulate
        in the SIM 900 buffer and not the module buffer. It probably doesn't actually
        matter here, because the underlying Driver event queue shouldn't allow concurrent
        writes and reads, but in principle it's good to be smart."""

        self.writeAndLog('FLSH %d' % port)
        self.writeAndLog('SNDT %d, "%s"' % (port, module_cmd), bCheckError=bCheckError)
        
        wait_on_term = True
        response = ''
        start = time.time()
        while wait_on_term:
            nbytes_waiting = 0

            #Poll the mainframe until it reports data is waiting or it times out
            while nbytes_waiting == 0:
                nbytes_waiting = int(self.askAndLog('NINP? %d' % port, bCheckError=bCheckError))
                if time.time() - start > timeout:
                    response = 'None'
                    wait_on_term = False
                    break

            #Grab the data and check for a term char. If not there yet, wait for more data or timeout
            if wait_on_term:
                self.writeAndLog('RAWN? %d, %d' % (port, nbytes_waiting), bCheckError=bCheckError)
                response += self.read(nbytes_waiting).decode()

                if response[-2:] == '\r\n':
                    wait_on_term = False

                if time.time()-start > timeout:
                    start = time.time()
                    response = 'Timed Out'
                    wait_on_term = False

        value = response.strip('\r\n')
        return value

    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection"""
        # calling the generic VISA open to make sure we have a connection
        VISA_Driver.performOpen(self, options=options)
        # do additional initialization code here...

        #Hacky way to make sure the input buffer is flushed out
        try:
            self.reportProgress(1/8)
            _ = self.read(1024)
        except:
            pass

        #Flush everything (hopefully)
        self.writeAndLog('*CLS')
        self.writeAndLog('FLOQ')

        #Step through each channel and query ID
        #Build up a dict of IDN/Channel pairs
        self.ports_dict = {}
        for ix in range(8):
            channel = ix+1
            idn = self.sim900_module_ask(channel, '*IDN?', timeout = 0.5, bCheckError=False)

            if idn not in  ['None', 'Timed Out']:
                module_code = idn.split(',')[1]
                self.ports_dict[module_code] = channel
            else:
                module_code = idn
            
            self.setValue('Slot %d' % channel, module_code)
            self.reportProgress(channel/8)
                   
    def performClose(self, bError=False, options={}):
        """Perform the close instrument connection operation"""
        # calling the generic VISA class to close communication
        VISA_Driver.performClose(self, bError, options=options)
        # do additional cleaning up code here...
        pass

    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform the Set Value instrument operation. This function should
        return the actual value set by the instrument"""

        if 'Slot' in quant.name:
            pass
             
        
        elif quant.name == 'Passthrough':
            module_code = options.pop('module_code', None)

            if module_code is None:
                value='None'
            else:
                port = self.ports_dict[module_code]
                module_cmd = options.pop('module_cmd', None)

                self.writeAndLog('FLSH %d' % port)
                self.writeAndLog('SNDT %d, "%s"' % (port, module_cmd), bCheckError=False)
        else:
           value =  VISA_Driver.performSetValue(self, quant, value, sweepRate, options)

        return value

    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation"""

        if 'Slot' in quant.name:
            value = quant.getValue()
        elif quant.name == 'Passthrough':

            module_code = options.pop('module_code', None)
            if module_code is None:
                value='None'
            else:
                port = self.ports_dict[module_code]
                module_cmd = options.pop('module_cmd', None)

                value = self.sim900_module_ask(port, module_cmd)



                
        else:
            value = VISA_Driver.performGetValue(self, quant, options=options)
        return value