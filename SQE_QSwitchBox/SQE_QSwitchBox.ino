/*
 * Document Name: SQE_QSwitchBOx.ino
 * Major update by: Andrea Celotto
 * Date: April 2024
 *
 * Document Name: ControlCode.ino 
 * Firstly edited and Designed by Ege "Katya" Sonmezoglu for INRiM QSwitch-Box project 
 * Date: 05/28/2022
 * 
 */

#include <EEPROM.h>

// Supported commands:
// BOTH <*>, BOTH?, DEL <§>, DEL?, *IDN?, *CLS, *RST
// <*>: 1, 2, 3, 4, 5, 6
// <§>: delay in ms


String command = ""; // Global variable to save the command coming from QSwitch-Box Control Panel, Labber or whatever
float myDelay = 20; // Total delay between close and open operations. Addressed by commands of the form DEL <*>
int state_address = 0; // Address of the byte of the internal ROM o0f the board where the state of the system is saved

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(5);
  pinMode(2,OUTPUT); // Setting the pins to output mode
    pinMode(3,OUTPUT);
    pinMode(4,OUTPUT);
    pinMode(5,OUTPUT);
    pinMode(6,OUTPUT);
    pinMode(7,OUTPUT);
    pinMode(8,OUTPUT);
    pinMode(22,OUTPUT);
    pinMode(24,OUTPUT);
    pinMode(26,OUTPUT);
    pinMode(28,OUTPUT);
    pinMode(30,OUTPUT);
    pinMode(32,OUTPUT);
    pinMode(34,OUTPUT);
  
  digitalWrite(2,HIGH); // Setting the outputs to HIGH
    digitalWrite(3,HIGH);
    digitalWrite(4,HIGH);
    digitalWrite(5,HIGH);
    digitalWrite(6,HIGH);
    digitalWrite(7,HIGH);
    digitalWrite(8,HIGH);
    digitalWrite(22,HIGH);
    digitalWrite(24,HIGH);
    digitalWrite(26,HIGH);
    digitalWrite(28,HIGH);
    digitalWrite(30,HIGH);
    digitalWrite(32,HIGH);
    digitalWrite(34,HIGH);
}

void reset(){
  closeAll();
  digitalWrite(3,LOW);
    digitalWrite(22,LOW);
    delay(myDelay);
    digitalWrite(3,HIGH);
    digitalWrite(22,HIGH);
    closeAll();  
    delay(200);
    digitalWrite(4,LOW);
    digitalWrite(24,LOW);  
    delay(myDelay);
    digitalWrite(4,HIGH);
    digitalWrite(24,HIGH);
    closeAll();
    delay(200);
    digitalWrite(5,LOW);
    digitalWrite(26,LOW);
    delay(myDelay);
    digitalWrite(5,HIGH);
    digitalWrite(26,HIGH);
    closeAll();
    delay(200);
    digitalWrite(6,LOW); 
    digitalWrite(28,LOW);
    delay(myDelay);
    digitalWrite(6,HIGH);
    digitalWrite(28,HIGH);
    closeAll();
    delay(200);
    digitalWrite(7,LOW); 
    digitalWrite(30,LOW);
    delay(myDelay);
    digitalWrite(7,HIGH);
    digitalWrite(30,HIGH);
    closeAll();
    delay(200);
    digitalWrite(8,LOW); 
    digitalWrite(32,LOW);
    delay(myDelay);
    digitalWrite(8,HIGH);
    digitalWrite(32,LOW);
  closeAll();
}

void loop() {
  // Wait for any character available on the serial channel
  while (!Serial.available()) {
    delay(20);
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
      EEPROM.write(state_address, 0);
      reset();
    }
    else if (command == "DEL?"){
      Serial.println(myDelay);
    }
    else if (command.startsWith("DEL")){
      myDelay = command.substring(3).toFloat();
    }
    else if (command == "BOTH?") {
      Serial.println(EEPROM.read(state_address));
    }
    else if (command.startsWith("BOTH")){
      // The requested circuit is extracted from the command string
      String termination = command.substring(5);
      
      if (termination.length() == 1){
        int new_state = termination.toInt();
        if (new_state == 0) { 
          reset();
          EEPROM.write(state_address, 0);
        }
        else if(new_state >= 1 && new_state <= 6){ 
          // Reads the current state from the ROM and closes that circuit
          int old_state = EEPROM.read(state_address);
          if (old_state != 0){
            close(old_state);
          }
          open(new_state); 
          EEPROM.write(state_address, new_state);
        }
        else {
          Serial.println("You can't set the switches to state " + command.substring(command.length()-1)) + "! Choose an integar number between 1 and 6, instead";
        }
      }
      else {
        Serial.println("Unknown command: " + command);
      }
      command = "";
    }
    else {
      Serial.println("Unknown command: " + command);
    }
    command = "";
  }
}

void closeAll(){ 
  digitalWrite(2,HIGH); //Setting every pin to high
    digitalWrite(3,HIGH);
    digitalWrite(4,HIGH);
    digitalWrite(5,HIGH);
    digitalWrite(6,HIGH);
    digitalWrite(7,HIGH);
    digitalWrite(8,HIGH);
    digitalWrite(22,HIGH);
    digitalWrite(24,HIGH);
    digitalWrite(26,HIGH);
    digitalWrite(28,HIGH);
    digitalWrite(30,HIGH);
    digitalWrite(32,HIGH);
    digitalWrite(34,HIGH);
  delay(20);
}

void open(int circuit){
  closeAll();
  if (circuit == 1){
    digitalWrite(2,LOW);
    digitalWrite(24,LOW);
    delay(myDelay);
    digitalWrite(2,HIGH);
    digitalWrite(24,HIGH);
  }
  else if (circuit == 2){ //the same with different pin numbers for the other circuits
    digitalWrite(3,LOW);
    digitalWrite(26,LOW);
    delay(myDelay);
    digitalWrite(3,HIGH);
    digitalWrite(26,LOW);
  }
  else if (circuit == 3){
    digitalWrite(4,LOW);
    digitalWrite(28,LOW);
    delay(myDelay);
    digitalWrite(4,HIGH);
    digitalWrite(28,HIGH);
  }
  else if (circuit == 4){
    digitalWrite(5,LOW); 
    digitalWrite(30,LOW);
    delay(myDelay);
    digitalWrite(5,HIGH);
    digitalWrite(30,HIGH);
  }
  else if (circuit == 5){
    digitalWrite(6,LOW); 
    digitalWrite(32,LOW);
    delay(myDelay);
    digitalWrite(6,LOW);
    digitalWrite(32,LOW);
  }
  else if (circuit == 6){
    digitalWrite(7,LOW); 
    digitalWrite(34,LOW);
    delay(myDelay);
    digitalWrite(7,HIGH);
    digitalWrite(34,HIGH);
  }
  closeAll();
}

void close(int circuit){
  closeAll();
  if (circuit == 1){
    digitalWrite(3,LOW);
    digitalWrite(22,LOW);
    delay(myDelay);
    digitalWrite(3,HIGH);
    digitalWrite(22,HIGH);
  }
  else if (circuit == 2){ //the same with different pin numbers for the other circuits
    digitalWrite(4,LOW);
    digitalWrite(24,LOW);  
    delay(myDelay);
    digitalWrite(4,HIGH);
    digitalWrite(24,HIGH);
  }
  else if (circuit == 3){
    digitalWrite(5,LOW);
    digitalWrite(26,LOW);
    delay(myDelay);
    digitalWrite(5,HIGH);
    digitalWrite(26,HIGH);
  }
  else if (circuit == 4){
    digitalWrite(6,LOW); 
    digitalWrite(28,LOW);
    delay(myDelay);
    digitalWrite(6,HIGH);
    digitalWrite(28,HIGH);
  }
  else if (circuit == 5){
    digitalWrite(7,LOW); 
    digitalWrite(30,LOW);
    delay(myDelay);
    digitalWrite(7,HIGH);
    digitalWrite(30,HIGH);
  }
  else if (circuit == 6){
    digitalWrite(8,LOW); 
    digitalWrite(32,LOW);
    delay(myDelay);
    digitalWrite(8,HIGH);
    digitalWrite(32,LOW);
  }
  closeAll();
}
