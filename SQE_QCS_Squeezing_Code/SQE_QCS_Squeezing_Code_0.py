import InstrumentDriver
import subprocess
import numpy as np
import skrf as rf
import os
from datetime import datetime
import socket
import sys


class Error(Exception):
    pass

class Driver(InstrumentDriver.InstrumentWorker):


    def performOpen(self, options={}):
        # Crea un socket TCP/IP
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connette il socket alla porta del server
        server_address = ('10.10.28.209', 1000)
        print('connecting to %s port %s' % server_address, file=sys.stderr)
        sock.connect(server_address)

        try:
            # Invia i dati
            message = 'This is the message. It will be repeated.'
            print('sending "%s"' % message, file=sys.stderr)
            sock.sendall(message.encode())  # Converti il messaggio in bytes

            # Cerca la risposta
            amount_received = 0
            amount_expected = len(message)
            
            while amount_received < amount_expected:
                data = sock.recv(16)
                amount_received += len(data)
                print('received "%s"' % data.decode(), file=sys.stderr)  # Decodifica i dati ricevuti

        finally:
            print('closing socket', file=sys.stderr)
            sock.close()
    
    def performClose(self, bError=False, options={}):
        pass

    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        pass

    def performGetValue(self, quant, options={}):
        return 0
    

if __name__ == '__main__':
    pass








# # Percorso del file PowerShell
# ps_script_path = "I:\Drive condivisi\SuperQuElectronics\Students Folders\Alessandro Alocco\\remote.ps1"

# # Comando per eseguire lo script PowerShell
# #command = ['powershell', '-File', ps_script_path]

# command = ['powershell', '-ExecutionPolicy', 'Bypass', '-File', ps_script_path]

# # Esecuzione del comando
# result = subprocess.run(command, capture_output=True, text=True)

# # Stampa l'output
# print("STDOUT:", result.stdout)
# print("STDERR:", result.stderr)