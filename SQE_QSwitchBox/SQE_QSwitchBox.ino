/*
 * Document Name: SQE_QSwitchBOx.ino
 * Major update by: Andrea Celotto
 * Date: 02/12/2024
 *
 * Document Name: ControlCode.ino 
 * Edited and Designed by Ege "Katya" Sonmezoglu for INRiM QSwitch-Box project 
 * Date: 05/28/2022
 * 
 */

#include <EEPROM.h>

class QSwitch {
  public:
    int pins_open[6]; // Array whose (i-1)-th entry is the pin that opens the i-th switch path
    int pins_closed[6]; // Array whose (i-1)-th entry is the pin that closes the i-th switch path
    int open_relay_state[6]; // Array whose (i-1)-th entry is the final state of the pulse to send to the right pin to open the the i-th switch path
    int closed_relay_state[6]; // Array whose (i-1)-th entry is the final state of the pulse to send to the right pin to close the the i-th switch path
    int address; // Address of the byte in the board internal memory where the switch state is stored
    
    QSwitch(){ // Default constructor
      pins_open = [0,0,0,0,0,0];
      pins_closed = [0,0,0,0,0,0];
      open_relay_state = [HIGH, HIGH, HIGH, HIGH, HIGH, HIGH];
      closed_relay_state = [HIGH, HIGH, HIGH, HIGH, HIGH, HIGH];
      address = 0; 
    }

    QSwitch(String _name, int _pins_open[6], int _pins_closed[6], int _open_relay_state[6], int _closed_relay_state[6], int _address) { // Constructor
      pins_open = _pins_open;
      pins_closed = _pins_closed;
      open_relay_state = _open_relay_state;
      closed_relay_state = _closed_relay_state; 
      address = _address;
    }
};

// Command sintax:
// [Switch]<*>
// [Switch]: SW1, SW2, BOTH
// <*>: " 1", " 2", " 3", " 4", " 5", " 6", "?"

QSwitch1 = QSWitch(
  [2, 3, 4, 5, 6, 7], 
  [3, 4, 5, 6, 7, 8],
  [HIGH, HIGH, HIGH, HIGH, HIGH, HIGH],
  [HIGH, HIGH, HIGH, HIGH, LOW, HIGH], 
  0,
);
QSwitch2 = QSWitch(
  [24, 26, 28, 30, 32, 34], 
  [22, 24, 26, 28, 30, 32],
  [HIGH, HIGH, HIGH, HIGH, HIGH, LOW],
  [HIGH, LOW, HIGH, HIGH, LOW, HIGH], 
  1,
);

String command = ""; // Global variable to save command coming from QSwitch-Box Controller Panel, Labber or whatever
float myDelay = 20; // Total delay between close and open operations. Addressed by commands of the form DEL <*>

void setup(){
  Serial.begin(115200);
  Serial.setTimeout(1);

  for (int i = 0; i < 6; i++) {
    pinMode(QSwitch1.pins_open[i],OUTPUT);
    pinMode(QSwitch1.pins_closed[i],OUTPUT);
    pinMode(QSwitch2.pins_open[i],OUTPUT);
    pinMode(QSwitch2.pins_closed[i],OUTPUT);
  }

  for (int i = 0; i < 6; i++) {
    digitalWrite(QSwitch1.pins_open[i],HIGH);
    digitalWrite(QSwitch1.pins_closed[i],HIGH);
    digitalWrite(QSwitch2.pins_open[i],HIGH);
    digitalWrite(QSwitch2.pins_closed[i],HIGH);
  }
}

void loop() {
  // Wait for any character available on the serial channel
  while (!Serial.available()) {
    delay(10);
  }
  // Read the available character and add it to the current command
  char receivedChar = Serial.read();
  command += receivedChar;
  // If the last received character is a newline ("\n"), process the command
  if (receivedChar == '\n') {
    // Remove any excess spaces
    command.trim();
    // Process the command
    if (command=="*IDN?"){
      Serial.println("SQE_QSwitchBox");
    }
    else if (command == "*CLS"){
      Serial.flush();
    }
    else if (command == "*RST"){
      EEPROM.write(QSwitch1.address, 0);
      EEPROM.write(QSwitch2.address, 0);
      reset();
    }
    else if (command.startswith("DEL")){
      Serial.print("Delay set to " + a.substring(3) + " ms");
      myDelay = a.substring(3).toFloat();
    }
    else if (command.endsWith("?")) {
      String output = processQuery(command);
    }
    else {
      processWrite(command);
    }
    command = "";
  }
}

void closeAll(){ 
  for (int i = 0; i < 6; i++) {
    digitalWrite(QSwitch1.pins_open[i],HIGH);
    digitalWrite(QSwitch1.pins_closed[i],HIGH);
    digitalWrite(QSwitch2.pins_open[i],HIGH);
    digitalWrite(QSwitch2.pins_closed[i],HIGH);
  }
  delay(20);
}

String processQuery(String cmd){
  String switchName = cmd.substring(0, cmd.size()-1);
  String msg;
  if (switchName == "SW1"){
    msg = EEPROM.read(QSwitch1.address)
    Serial.println();
  }
  else if (switchName == "SW2"){
    msg = EEPROM.read(QSwitch2.address);
  }
  else if (switchName == "BOTH"){
    String state1 = EEPROM.read(QSwitch1.address);
    String state2 = EEPROM.read(QSwitch1.address);
    if (state1 == state2){ msg = state1; }
    else{ msg = "Error"; }
    Serial.prinln(msg);
    return msg;
  }
}

void sendPulse(int pin, int state1, int state2){
  digitalWrite(pin, state1);
  delay(myDelay);
  digitalWrite(pin, state2);
  return;
}

void processWrite(String cmd){
  String switchName = cmd.substring(0, cmd.size()-1);
  int old_state = processQuery(switchName + "?");
  int target_state = atoi(cmd.substring(cmd.size-1));
  if (switchName == "SW1"){
    closeAll();
    sendPulse(QSwitch1.pin_closed[old_state-1], LOW, QSwitch1.closed_relay_state[old_state-1]); // closing old path
    delay(myDelay);
    sendPulse(QSwitch1.pin_open[target_state-1], LOW, QSwitch1.open_relay_state[target_state-1]); // opening new path
    EEPROM.write(QSwitch1.address, target_state);
  }
  else if (switchName == "SW2"){
    closeAll();
    sendPulse(QSwitch2.pin_closed[old_state-1], LOW, QSwitch2.closed_relay_state[old_state-1]); // closing old path
    delay(myDelay);
    sendPulse(QSwitch2.pin_open[target_state-1], LOW, QSwitch2.open_relay_state[target_state-1]); // opening new path
    EEPROM.write(QSwitch1.address, target_state);
  }
  else if (switchName == "BOTH"){
    closeAll();
    sendPulse(QSwitch1.pin_closed[old_state-1], LOW, QSwitch1.closed_relay_state[old_state-1]); // closing old path
    sendPulse(QSwitch2.pin_closed[old_state-1], LOW, QSwitch2.closed_relay_state[old_state-1]); // closing old path
    delay(myDelay);
    sendPulse(QSwitch1.pin_open[target_state-1], LOW, QSwitch1.open_relay_state[target_state-1]); // opening new path
    sendPulse(QSwitch2.pin_open[target_state-1], LOW, QSwitch2.open_relay_state[target_state-1]); // opening new path
    closeAll();
    EEPROM.write(QSwitch1.address, target_state);
    EEPROM.write(QSwitch2.address, target_state);
  }

void reset(){
  for (int i = 0; i < 6; i++) {
    closeAll();
    sendPulse(QSwitch1.pin_closed[old_state-1], LOW, QSwitch1.closed_relay_state[old_state-1]); // closing old path
    sendPulse(QSwitch2.pin_closed[old_state-1], LOW, QSwitch2.closed_relay_state[old_state-1]); // closing old path
    delay(myDelay);
    sendPulse(QSwitch1.pin_open[target_state-1], LOW, QSwitch1.open_relay_state[target_state-1]); // opening new path
    sendPulse(QSwitch2.pin_open[target_state-1], LOW, QSwitch2.open_relay_state[target_state-1]); // opening new path
    closeAll();
    delay(200);
  }
}
