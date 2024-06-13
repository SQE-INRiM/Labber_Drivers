import InstrumentDriver
import numpy as np
from scipy.linalg import fractional_matrix_power
import skrf as rf
from typing import Iterable
import datetime
import os

def myMatPow(A: np.ndarray, t: float):
    """
    Raises a matrix of the form (k,N,N) to 
    """
    if A.ndim > 3 or A.shape[-1] != A.shape[-2]:
        raise ValueError('The shape must be of the form (k,N,N)')
    B = A.copy()
    for i in range(A.shape[0]):
        B[i,:,:] = fractional_matrix_power(A[i,:,:], t)
    return B


class Error(Exception):
    pass

class Driver(InstrumentDriver.InstrumentWorker):
    """ This class implements a S-parameter calibrator for 2-port networks"""

    def getFrequencyVector(self, trace):
        if len(trace['y']) == 0:
            return np.array([])
        f0 = trace.get('t0')
        df = trace.get('dt')
        N = int(trace.get('shape')[0])
        return np.linspace(f0, f0+N*df, N)
    
    def get_most_recent_calibration(self):
        # Initialize the most recent date to a very old date
        most_recent_date = datetime.datetime(year=1, month=1, day=1, hour=0, minute=0)
        most_recent_folder = None
        database = self.getValue('Database for the SNP files')
        # Iterate over all items in the parent folder
        for item in os.listdir(database):
            # Construct the full path of the item
            full_path = os.path.join(database, item)

            # Check if the item is a directory and its name respects the YYYY_MM_DD__HH_MM format
            if os.path.isdir(full_path):
                try:
                    # Parse the date and time from the directory name
                    date = datetime.datetime.strptime(item, '%Y_%m_%d__%H_%M_%S')

                    # If this date is more recent than the most recent date we've seen so far, update our most recent date and folder
                    if date > most_recent_date:
                        most_recent_date = date
                        most_recent_folder = full_path
                except ValueError:
                    # The directory name does not respect the YYYY_MM_DD__HH_MM_SS format, ignore it
                    pass
        if most_recent_folder is None:
            raise NotADirectoryError(f'No sub-folder respecting the YYYY_MM_DD__HH_MM_SS naming convention has been found inside {database}')
        return most_recent_folder
    
    def find_SNP_files(self):
        # Initialize an empty list to store the file paths
        files = []
        names = []

        # Iterate over all items in the folder
        for item in os.listdir(self.dir):
            # Construct the full path of the item
            full_path = os.path.join(self.dir, item)

            # Check if the item is a file and its extension is in the list of extensions
            if os.path.isfile(full_path) and any(full_path.endswith(ext) for ext in ('.s1p', '.s2p')):
                # Add the file path to the list
                files.append(full_path)
                names.append(item.replace('.s2p', '').replace('.s1p', ''))

        return files, names


    def performOpen(self, options={}):
        """
        Set every local variable to default value, then perform the open instrument connection operation
        """
        self.cal_alg = None
        self.fixtures = [None, None]
        self.DUT_frequency = None
        self.dir = None
        self.subfolder = None

        self.NetworkDict = {}
    
    def performClose(self, bError=False, options={}):
        """Perform the close instrument connection operation"""
        super().performClose()

    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform te Set Value instrument operation. This function returns the actual value set by the instrument. 
        If the provided value is a S2P file, the calibration algorithm is reset, and a Network object is created with scikit-rf ansd stored inside the driver"""
        self.log(f'Setting {quant.name} to {value.__repr__()}')
        
        if not isinstance(value, Iterable) or isinstance(value, str): 
            # It checks if the updated quantity is a string or another data type that is not iterable. 
            # That means that it is a calibration option of some sort.
            self.cal_alg = None # The calibration algorithm is refreshed

        if 'fixture removal' in quant.name:
            # If the technique for fixture removal is being updated, the fixtures are refreshed
            self.fixtures = [None, None]

        elif 'Length of fixture on port' in quant.name: # If
            self.fixtures[int(quant.name[-1])-1] = None

        elif 'Ideal' in quant.name or ('Measured' in quant.name and not self.getValue('Load last cal')) or ('Fixture on port' in quant.name and self.getValue('Apply custom fixture removal')):
            # If the quantity consists of S-parameters in a S2P file, memorize the corresponding Network object constructed with scikit-rf
            
            if value == '':
                self.NetworkDict[quant.name] = rf.Network(None)
            else:
                self.NetworkDict[quant.name] = rf.Network(value.replace('__', '/'))
            if value != '' and 'Fixture on port' in quant.name: 
                # If a custom fixture has been actually provided by the user, update the fixtures
                self.fixtures[int(quant.name[-1])-1] = self.NetworkDict[quant.name]

        if quant.name == 'Database for the SNP files' and self.getValue('Load last cal'):
            if value is None:
                raise NotADirectoryError(f'A database was not provided!')
            if os.path.isfile(value):
                value = os.path.dirname(value)
            if not os.path.exists(value):
                raise NotADirectoryError(f'The provided database at {value} does not exist!')
            self.dir = self.get_most_recent_calibration()
            self.log(f'The calibration files inside {self.dir} will be used')
            for file, name in zip(*self.find_SNP_files()):
                self.NetworkDict['Measured ' + name.replace('__', '/')] = rf.Network(file)
            

        self.log(f'Set {quant.name} to {str(value)}')
        return value

    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation"""
        self.log(f'Getting {quant.name}')

        if self.isFirstCall(options):
            self.log('Is first call')
            self.log(self.NetworkDict.keys())
            self.cal_alg = None

        if quant.name.startswith('Corrected'): # If the requested quantity is a Corrected S-parameter
            self.log(f'Requesting ' + quant.name.lower()) 
            raw_dict = self.getValue('Raw ' + quant.name[-3:])
            value = raw_dict.copy()
            if self.cal_alg is None: # If the calibration algorithm has not been constructed yet or if it has been reset

                if len(raw_dict['y']) == 0: # This happens if the driver gets an empty trace
                    self.log(f'DUT_frequency = None')
                    self.DUT_frequency = None
                else:
                    self.DUT_frequency = rf.Frequency.from_f(self.getFrequencyVector(raw_dict))
                    if len(self.DUT_frequency) == 0:
                        self.log(f'DUT_frequency = None')
                        self.DUT_frequency = None
                    else:
                        self.log(f'Frequency: {self.DUT_frequency}')

                if self.DUT_frequency is not None: # If the line above succeded
                    if self.dir is None and self.getValue('Load last cal'):
                        self.sendValueToOther('Database for the SNP files', self.getValue('Database for the SNP files'))
                    self.runCalibration() # This function makes checks that everything is well-defined and then constructs the calibration alogorithm
                    self.log('Ran calibration')
            if self.DUT_frequency is not None:
                x = int(quant.name[-2]) # the second to last character in the quantity name. In "Corrected S21" it's 2
                y = int(quant.name[-1])  # the last character in the quantity name. In the previous example it's 1
                
                CorrectedNetwork = self.getCorrectedMatrix() # The calibration algorithm is used to compute the corrected S matrix 
                value['y'] = CorrectedNetwork.s[:, x-1, y-1] # The right entry of the S-matrix is returned
            else:
                self.log('Correction was not performed')
        else:
            value = quant.getValue()

        if self.isFinalCall(options):
            self.log('Is final call')
            self.cal_alg = None

        return value

    def runCalibration(self):

        ideals = self.check_ideals()
        measured = self.check_measured()

        sw_terms = None
        self.check_switch_terms()
        sw_terms = (self.NetworkDict['Measured a2/b2_1'], self.NetworkDict['Measured a1/b1_2'])
        
        if self.getValue('Calibration method') in ('SOLT', 'SOLR'):
            iso = measured[2] #i.e. the "L" in SOLT and SOLR

        if self.getValue('Apply custom fixture removal'):
            self.check_custom_fixture()

        if self.getValue('Calibration method') == 'SOLR':
            cal_alg = rf.UnknownThru(measured=measured, ideals=ideals, switch_terms=sw_terms, isolation=iso)
            cal_alg.run()

            if self.getValue('Apply default fixture removal'): 
                correctedReciprocal = cal_alg.apply_cal(measured[-1]) # Applies the calibration algorithm to the reciprocal standard itself

                # The two fixtures are computed from the corrected reciprocal's de-embedded S-parameters considering their length ratio with it
                # ABCD_fixture_j = ABCD_corrected_reciprocal ^ ratio_j
                self.fixtures[0] = rf.Network(frequency=correctedReciprocal.frequency, a = myMatPow(correctedReciprocal.a, self.getValue('Length of fixture on port 1')))
                self.fixtures[1] = rf.Network(frequency=correctedReciprocal.frequency, a = myMatPow(correctedReciprocal.a, self.getValue('Length of fixture on port 2')))

        elif self.getValue('Calibration method') == 'SOLT':
            cal_alg = rf.SOLT(measured=measured, ideals=ideals, switch_terms=sw_terms, isolation=iso)
            cal_alg.run()
        elif self.getValue('Calibration method') == 'TRL':
            cal_alg = rf.TRL(measured=measured, ideals=ideals, switch_terms=sw_terms)
            cal_alg.run()
        self.log(f"New {self.getValue('Calibration method')} calibration algorithm has been created")
        self.cal_alg = cal_alg

    def check_ideals(self):
        self.log('Checking ideals')
        if self.getValue('Calibration method') == 'SOLR':
            quants = ['short', 'open', 'load', 'reciprocal']
        elif self.getValue('Calibration method') == 'SOLT':
            quants = ['short', 'open', 'load', 'thru']
        elif self.getValue('Calibration method') == 'TRL':
            quants = ['thru', 'line', 'reflect']
        ideals = [self.NetworkDict[f'Ideal {quant}'] for quant in quants] # This list contains the Networks of the ideal standards

        #Check that they are defined over the same frequency range
        if any(not np.array_equal(ideals[0].f, ideal.f) for ideal in ideals):
            raise ValueError('The ideal standards are not all defined over the same frequency range!')
        
        # Check that the current measurement is performed within the frequency range of the ideal standards
        if self.DUT_frequency.f[0] < ideals[0].f[0] or self.DUT_frequency.f[-1] > ideals[0].f[-1]:
            raise ValueError('The DUT is being measured over a frequency range not completely included in that of the ideal standards!')
        return ideals
        
    def check_measured(self):
        self.log('Checking measured')
        if self.getValue('Calibration method') == 'SOLR':
                quants = ['short', 'open', 'load', 'reciprocal']
        elif self.getValue('Calibration method') == 'SOLT':
            quants = ['short', 'open', 'load', 'thru']
        elif self.getValue('Calibration method') == 'TRL':
            quants = ['thru', 'line', 'reflect']
        meas = [self.NetworkDict[f'Measured {quant}'] for quant in quants] # This list contains the Networks of the measured standards

        #Check that they are defined over the same frequency range
        if any(not np.array_equal(meas[0].f, meas_.f) for meas_ in meas):
            raise ValueError('The provided ideal standards are not defined over the same frequency range!')
        
        # Check that they can be interpolate to the frequency range of the current measurement
        for quant in quants:
            try:
                self.NetworkDict[f'Measured {quant}'].interpolate_self(self.DUT_frequency)
            except:
                self.log(self.DUT_frequency)
                self.log(self.NetworkDict[f'Measured {quant}'].frequency)
                raise ValueError(f"The measured {quant} standard's S-parameters cannot be interpolated to the frequency range of the current measurement")
        return [self.NetworkDict[f'Measured {quant}'] for quant in quants]
    
    def check_switch_terms(self):
        self.log('Checking switch-terms')
        # Check that the switch-terms can be interpolate to the frequency range of the current measurement
        try:
            self.NetworkDict[f'Measured a2/b2_1'].interpolate_self(self.DUT_frequency)
            self.NetworkDict[f'Measured a1/b1_2'].interpolate_self(self.DUT_frequency)
        except:
            raise ValueError(f"The measured switch-terms' S-parameters cannot be interpolated to the frequency range of the current measurement")
    
    def check_custom_fixture(self):
        self.log('Checking custom fixtures')
        #Check that the two fixtures are defined over the same frequency range
        if not np.array_equal(self.fixtures[0].f, self.fixtures[1].f):
            raise ValueError('The fixtures on the two ports are not defined over the same frequency range!')
        # Check that they can be interpolate to the frequency range of the current measurement
        for quant in self.fixtures:
            try:
                quant.interpolate_self(self.DUT_frequency)
            except:
                raise ValueError(f"The S-parameters of the fixtures cannot be interpolated to the frequency range of the current measurement")
        
    def getCorrectedMatrix(self):
        
        # Creating the raw S matrix
        s = np.empty((len(self.DUT_frequency), 2, 2), dtype=complex)
        for i in [1,2]:
            for j in [1,2]:
                s[:,i-1,j-1] = self.getValue(f'Raw S{i}{j}')['y'] 
        RawMatrix = rf.Network(frequency=self.DUT_frequency, s=s)

        # The calibration algorithm is applied to the raw S matrix, returning the S matrix at the reference plane of the SP6T throw switches
        cMat =  self.cal_alg.apply_cal(RawMatrix)

        # Fixture removal
        if self.fixtures[0] is not None and self.fixtures[1] is not None:
            cMat = self.fixtures[0].inv ** cMat ** self.fixtures[1].inv # The fixtures are de-embedded, further correcting the S matrix
        
        return cMat


if __name__ == '__main__':
    pass
