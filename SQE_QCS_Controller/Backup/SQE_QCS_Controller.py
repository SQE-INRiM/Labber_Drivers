import InstrumentDriver
import json
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

    """ This class implements a connection with the QCS to run a specific API script"""

    def __init__(self, *args, **kwargs):                                    # Call to constructor with all received arguments
        super().__init__(*args, **kwargs)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)       # Initialization of attributes
        self.server_address = ('10.10.28.209', 1000)

    def connection(self):                                                   # Connects client to server
        server_address = ('10.10.28.209', 10000)                            # if pass server address passed in constructor -> problems
        print(f'Connecting to {self.server_address[0]} port {self.server_address[1]}')
        try:
            self.sock.connect(server_address)
        except socket.error as e:
            print(f"Connection error: {e}")
            raise

    def send_data(self, data):                                             # Sends data to server and print its answer
        try:
            message = f"{data};"
            self.sock.sendall(message.encode())
            print('Sending: "%s"' % message)
            print(self.receive_data())
        except Exception as e:
            print(f"Error sending data: {e}")
            raise

    def receive_data(self):                                               # Receive data from server
        data = b""
        while b";" not in data:
            chunk = self.sock.recv(1024)
            if not chunk:
                break
            data += chunk
        received_message = data.decode().strip(";")
        return received_message

    def performOpen(self, options={}):  
        """Perform the connection with the instrument"""                                  
        self.connection()
        self.send_data("Open")

    def performClose(self, bError=False, options={}):
        """Perform the close instrument connection operation"""
        self.log('Closing socket')
        self.send_data("Close")
        self.sock.close()
        super().performClose(bError=bError, options=options)

    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation"""
        message = f"{quant.name}?;"
        try:
            self.sock.sendall(message.encode())
            self.log('Sending: "%s"' % message)
            received_message = self.receive_data()
            self.log(received_message)
            if '[' not in received_message:
                value = float(received_message)
            else:
                pass # stuff to do
            return value
        except Exception as e:
            print(f"Error in performGetValue: {e}")
            
        return value

    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform te Set Value instrument operation. 
        This function should return the actual value set by the instrument"""
        message = f"{quant.name},{value}"
        self.send_data(message)
        self.log('Out of send_data')
        return value


# class Driver(InstrumentDriver.InstrumentWorker):
#     """ This class implements a connection with the QCS to run a specific API script"""

#     def __init__(self, *args, **kwargs):                                    # Call to constructor with all received arguments
#         super().__init__(*args, **kwargs)
#         self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)       # Initialization of attributes
#         self.server_address = ('10.10.28.209', 1000)

#     def connection(self):                                                   # Connects client to server
#         server_address = ('10.10.28.209', 10000)                            # if pass server address passed in constructor -> problems
#         print(f'Connecting to {self.server_address[0]} port {self.server_address[1]}')
#         try:
#             self.sock.connect(server_address)
#         except socket.error as e:
#             print(f"Connection error: {e}")
#             raise

#     def send_data(self, data):                                             # Sends data to server and print its answer
#         try:
#             message = f"{data};"
#             self.sock.sendall(message.encode())
#             print('Sending: "%s"' % message)
#             print(self.receive_data())
#         except Exception as e:
#             print(f"Error sending data: {e}")
#             raise

#     def receive_data(self):                                               # Receive data from server
#         data = b""
#         while b";" not in data:
#             chunk = self.sock.recv(1024)
#             if not chunk:
#                 break
#             data += chunk
#         received_message = data.decode().strip(";")
#         return received_message

#     def performOpen(self, options={}):  
#         """Perform the connection with the instrument"""                                  
#         self.connection()
#         self.send_data("Open")

#     def performSetValue(self, quant, value, sweepRate=0.0, options={}):
#         """Perform te Set Value instrument operation. 
#         This function should return the actual value set by the instrument"""
#         message = f"{quant.name},{value}"
#         self.send_data(message)

#     def performGetValue(self, quant, options={}):
#         """Perform the Get Value instrument operation"""
#         message = f"{quant.name},GetValue;"
#         try:
#             self.sock.sendall(message.encode())
#             print('Sending: "%s"' % message)
#             received_message = self.receive_data()
#             self.log(received_message)
#             #value = float(received_message)
#             value = json.loads(received_message.decode())   # json to convert message to a array
#             return value
#         except Exception as e:
#             print(f"Error in performGetValue: {e}")
#             raise
    
#     def performClose(self, bError=False, options={}):
#         """Perform the close instrument connection operation"""
#         print('Closing socket')
#         self.send_data("Close")
#         self.sock.close()
        
if __name__ == '__main__':
    pass





















# class Error(Exception):
#     pass

# class Driver(InstrumentDriver.InstrumentWorker):

#     def __init__(self):
#      # Inizializzazione dell'oggetto
#         self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)        # Crea un socket TCP/IP
#         self.server_address = ('10.10.28.209', 1000)                         # Connette il socket alla porta del server


#     def connect(self):
#         print(f'Connecting to {self.server_address[0]} port {self.server_address[1]}')
#         #sys.stderr.flush()
#         self.sock.connect(self.server_address)


#     def performOpen(self, options={}):
#         # Crea un socket TCP/IP


#         # Crea un socket TCP/IP
#         # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#         # # Connette il socket alla porta del server
#         # server_address = ('10.10.28.209', 10000)
#         self.connect()

#         try:
#             # Prepara i dati da inviare
#             parameter = "Open"
            
#             # Crea un unico messaggio formattato con un delimitatore
#             message = f"{parameter};"  # Aggiungi ';' come delimitatore
#             print(f'Sending "{message}"')
#             sys.stderr.flush()  # Forza il flush del buffer
            
#             # Converti il messaggio in bytes e invialo tramite il socket
#             self.sock.sendall(message.encode())

#             # Ricevi la risposta dal server
#             data = b""
#             while b";" not in data:  # Continua a ricevere finché non trova il delimitatore
#                 chunk = self.sock.recv(1024)
#                 if not chunk:
#                     break
#                 data += chunk
            
#             # Decodifica e processa la risposta ricevuta
#             received_message = data.decode().strip(";")  # Rimuovi il delimitatore
#             print(f'Received: "{received_message}"')
#             sys.stderr.flush()  # Forza il flush del buffer

#         finally:
#             print('Closing socket')
#             sys.stderr.flush()  # Forza il flush del buffer
#             self.sock.close()


    
#     def performClose(self, bError=False, options={}):
#         pass

#     def performSetValue(self, quant, value, sweepRate=0.0, options={}):

#         # Prepara i dati da inviare
#         self.connect()

#         try:
#             # Prepara i dati da inviare
#             parameter_name1 = "Temperature"
#             unit1 = "mK"
#             value1 = 133.3

#             parameter_name2 = "Pump Power"
#             unit2 = "dBm"
#             value2 = -6

#             parameter_name3 = "Signal Power"
#             unit3 = "dBm"
#             value3 = -15
            
#             # Crea un unico messaggio formattato con un delimitatore
#             message = f"{parameter_name1},{unit1},{value1},{parameter_name2},{unit2},{value2},{parameter_name3},{unit3},{value3};"  # Aggiungi ';' come delimitatore
#             print(f'Sending "{message}"')
#             sys.stderr.flush()  # Forza il flush del buffer
            
#             # Converti il messaggio in bytes e invialo tramite il socket
#             sock.sendall(message.encode())

#             # Ricevi la risposta dal server
#             data = b""
#             while b";" not in data:  # Continua a ricevere finché non trova il delimitatore
#                 chunk = sock.recv(1024)
#                 if not chunk:
#                     break
#                 data += chunk
            
#             # Decodifica e processa la risposta ricevuta
#             received_message = data.decode().strip(";")  # Rimuovi il delimitatore
#             parameter_name_received1, unit_received1, value_received1, parameter_name_received2, unit_received2, value_received2, parameter_name_received3, unit_received3, value_received3 = received_message.split(',')
#             value_received1 = float(value_received1)  # Converti il valore numerico da stringa a float
#             value_received2 = float(value_received2)
#             value_received3 = float(value_received3)
#             print(f'Received: "{parameter_name_received1},{unit_received1},{value_received1},{parameter_name_received2},{unit_received2},{value_received2},{parameter_name_received3},{unit_received3},{value_received3}"')
#             sys.stderr.flush()  # Forza il flush del buffer

#         finally:
#             print('Closing socket')
#             sys.stderr.flush()  # Forza il flush del buffer
#             sock.close()


#     def performGetValue(self, quant, options={}):
#         # Ricevi la risposta dal server
#         return 0
    

# if __name__ == '__main__':
#     pass








# # # Percorso del file PowerShell
# # ps_script_path = "I:\Drive condivisi\SuperQuElectronics\Students Folders\Alessandro Alocco\;emote.ps1"

# # # Comando per eseguire lo script PowerShell
# # #command = ['powershell', '-File', ps_script_path]

# # command = ['powershell', '-ExecutionPolicy', 'Bypass', '-File', ps_script_path]

# # # Esecuzione del comando
# # result = subprocess.run(command, capture_output=True, text=True)

# # # Stampa l'output
# # print("STDOUT:", result.stdout)
# # print("STDERR:", result.stderr)