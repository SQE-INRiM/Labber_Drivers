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


// Command sintax:
// [Switch] <*>
// [Switch]: SW1, SW2, BOTH
// <*>: " 1", " 2", " 3", " 4", " 5", " 6", "?"


String command = ""; // Global variable to save command coming from QSwitch-Box Controller Panel, Labber or whatever
float myDelay = 20; // Total delay between close and open operations. Addressed by commands of the form DEL <*>
int statte_address = 0;

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

void sendPulse(int pin, int state1, int state2){
  digitalWrite(pin, state1);
  delay(myDelay);
  digitalWrite(pin, state2);
  return;
}

void reset(){
  for (int i = 0; i < 6; i++) {
    closeAll();
    sendPulse(QSwitch1.pins_closed[i], LOW, QSwitch1.closed_relay_state[i]); // closing old path
    sendPulse(QSwitch2.pins_closed[i], LOW, QSwitch2.closed_relay_state[i]); // closing old path
    delay(myDelay);
    sendPulse(QSwitch1.pins_open[i], LOW, QSwitch1.open_relay_state[i]); // opening new path
    sendPulse(QSwitch2.pins_open[i], LOW, QSwitch2.open_relay_state[i]); // opening new path
    closeAll();
    delay(200);
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
    Serial.println(command);
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
    else if (command.startsWith("DEL")){
      Serial.print("Delay set to " + command.substring(3) + " ms");
      myDelay = command.substring(3).toFloat();
    }
    else if (command.endsWith("?")) {
      processQuery(command);
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
  //Serial.println("starting to wait...");
  delay(20);
  //Serial.println("delay has passed");
  return;
}

int processQuery(String cmd){
  String switchName = cmd.substring(0, cmd.length()-1);
  int msg = -1;
  if (cmd.startsWith("SW1")){ 
    //Serial.println("it is SW1");
    msg = EEPROM.read(QSwitch1.address);
  }
  else if (cmd.startsWith("SW2")){
    //Serial.println("it is SW2");
    msg = EEPROM.read(QSwitch2.address);
  }
  else if (cmd.startsWith("BOTH")){
    //Serial.println("it is both");
    int state1 = EEPROM.read(QSwitch1.address);
    int state2 = EEPROM.read(QSwitch2.address);
    if (state1 == state2){ msg = state1; }
    else{ msg = state1*10+state2; }
  }
  Serial.println(msg);
  return msg;
}

void processWrite(String cmd){
  String switchName = cmd.substring(0, cmd.length()-1);
  int old_state = processQuery(switchName + "?");
  int target_state = cmd.substring(cmd.length()-1).toInt();

  if (switchName.startsWith("SW1")){
    closeAll();
    Serial.println(QSwitch1.pins_closed[old_state-1]);
    Serial.println(QSwitch1.closed_relay_state[old_state-1]);
    sendPulse(QSwitch1.pins_closed[old_state-1], LOW, QSwitch1.closed_relay_state[old_state-1]); // closing old path
    delay(myDelay);
    sendPulse(QSwitch1.pins_open[target_state-1], LOW, QSwitch1.open_relay_state[target_state-1]); // opening new path
    EEPROM.write(QSwitch1.address, target_state);
  }
  else if (switchName.startsWith("SW2")){
    closeAll();
    sendPulse(QSwitch2.pins_closed[old_state-1], LOW, QSwitch2.closed_relay_state[old_state-1]); // closing old path
    delay(myDelay);
    sendPulse(QSwitch2.pins_open[target_state-1], LOW, QSwitch2.open_relay_state[target_state-1]); // opening new path
    EEPROM.write(QSwitch2.address, target_state);
  }
  else if (switchName.startsWith("BOTH")){
    closeAll();
    sendPulse(QSwitch1.pins_closed[old_state-1], LOW, QSwitch1.closed_relay_state[old_state-1]); // closing old path
    sendPulse(QSwitch2.pins_closed[old_state-1], LOW, QSwitch2.closed_relay_state[old_state-1]); // closing old path
    delay(myDelay);
    sendPulse(QSwitch1.pins_open[target_state-1], LOW, QSwitch1.open_relay_state[target_state-1]); // opening new path
    sendPulse(QSwitch2.pins_open[target_state-1], LOW, QSwitch2.open_relay_state[target_state-1]); // opening new path
    closeAll();
    EEPROM.write(QSwitch1.address, target_state);
    EEPROM.write(QSwitch2.address, target_state);
  }
}