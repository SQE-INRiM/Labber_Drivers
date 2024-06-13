LABBER_PATH = '/Program Files/Keysight/Labber/Script/'
LABBER_SERVER = 'localhost'
SIM900_NAME = 'SQE_Stanford_SRS_SIM900 Mainframe'
import sys
sys.path.append(LABBER_PATH)

import Labber as lab
import InstrumentDriver

class SIM9XX_Driver(InstrumentDriver.InstrumentWorker):

    def performOpen(self, options={}):
        """Try to connect to the SIM900 mainframe. Start it up if necessary."""
        self.sim900 = None

        self.client = lab.connectToServer(LABBER_SERVER)
        instruments = self.client.getListOfInstruments()

        for hardware, config in instruments:
            if hardware == SIM900_NAME:
                self.sim900 = self.client.connectToInstrument(SIM900_NAME, dict(interface='GPIB', address='2'))

        assert self.sim900 is not None, "ERROR: Could not find a mainframe!"

        if not self.sim900.isRunning():
            self.sim900.startInstrument()

        assert self.sim900.isRunning() == True, "ERROR: Cannot start mainframe"

    def performClose(self, options={}):
        pass

    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """For the generic case, just grab the cmd string and the quantity name, pack it all up
        and send it through the sim900 driver."""

        #DOUBLE -> 0
        if quant.datatype == 0:
            value = str(value).replace('e', 'E')

        options.update(dict(module_code=self.getAddress(),
                            module_cmd=quant.set_cmd.replace('<*>', value)))

        value = self.sim900.setValue('Passthrough', value, sweepRate, options=options)

        return value

    def performGetValue(self, quant, options={}):
        """For the generic case, just grab the cmd string and the quantity name, pack it all up
        and send it through the sim900 driver."""
        
        options.update(dict(module_code=self.getAddress(),
                            module_cmd=quant.get_cmd))

        value = self.sim900.getValue('Passthrough', options=options)

        if quant.datatype == 0:
            value = float(value)

        return value