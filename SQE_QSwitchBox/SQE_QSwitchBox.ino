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
    int address; // Address of the byte in the board internal memory where the switch state is stored
    RTSwitch(){ // Default constructor
      pins_open = [0,0,0,0,0,0];
      pins_closed = [0,0,0,0,0,0];
      address = 0; 
    }
    RTSwitch(String _name, int _pins_open[6], int _pins_closed[6], int _address) { // Constructor
      pins_open = _pins_open;
      pins_closed = _pins_closed;
      address = _address;
    }
};

// Command sintax:
// [Switch]::[status]
// [Switch]: Port1, Port2, BOTH
// [status]: 

QSwitch1 = QSWitch(
  [2, 3, 4, 5, 6, 7], 
  [3, 4, 5, 6, 7, 8], 
  0,
);
QSwitch2 = QSWitch(
  [24, 26, 28, 30, 32, 34], 
  [22, 24, 26, 28, 30, 32], 
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
    / Remove any excess spaces
    command.trim();
    // Process the command
    if (command=="*IDN?"){
      Serial.println("SQE_QSwitchBox");
    }
    else if (command == "*CLS"){
      Serial.flush();
    }
    else if (command == "*RST"){
      reset()
    }
    else if (command.startswith("DEL")){
      Serial.print("Delay set to " + a.substring(3) + " ms");
      myDelay = a.substring(3).toFloat();
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

void processQuery(String cmd){
  String switchName = cmd.substring(0, cmd.size()-1);
  if (switchName == "SW1"){
    Serial.println(EEPROM.red(QSwitch1.address));
  }
  else if (switchName == "SW2"){
    Serial.println(EEPROM.red(QSwitch2.address));
  }
   if (switchName == "BOTH"){
    String state1 = Serial.println(EEPROM.red(QSwitch1.address));
    String state2 = Serial.println(EEPROM.red(QSwitch1.address));
    if (state1 == state2){
      Serial.println(state1)
    }
    else{
      Serial.println("Error")
    }
    Serial.println(EEPROM.red(QSwitch1.address));
  }
  Serial.println(EEPROM.read(RTSwitches[idx].address)); // The switch state saved in the board memory is returned of the serial channel
}

/*
 * Function Name: activateSwitches
 * Function Type: Void
 * Inputs: String a - It is the main command read by Serail Connection coming from QSwitch-Box Controller 
 * Function Description: The input string will compared with if-else statements to find which operation will applied to relay board. 
 * It will activates each relay according to the operatiın table of RF Swiches. 
 * Will send a serial signal (Serial.print"exeutedX") This signal read by the QSwitch-Box Controller panel in order to check if connection is successful and command is activated. 
 */
void processWrite(String cmd){
  int current_state = EEP
  if(a== "one"){ // PIN 1 is CLOSED CIRCUIT
    Serial.print("executed1"); //If the control panel not reads that message, it will ask user to try again because there is a connection problem. It is the same for all if statements
    closeAll();
    digitalWrite(2,LOW);
    digitalWrite(24,LOW);
    delay(y);
    digitalWrite(2,HIGH);
    digitalWrite(24,HIGH);
    closeAll();  
  }else if(a== "two"){ //PIN 1 is OPEN CIRCUIT
    Serial.print("executed2");
    closeAll();
    digitalWrite(3,LOW);
    digitalWrite(22,LOW);
    delay(y);
    digitalWrite(3,HIGH);
    digitalWrite(22,HIGH);
    closeAll();  
  }else if(a=="three"){ //PIN 2 is CLOSED CIRCUIT
    Serial.print("executed3");
    closeAll();
    digitalWrite(3,LOW);
    digitalWrite(26,LOW);
    delay(y);
    digitalWrite(3,HIGH);
    digitalWrite(26,LOW);
    closeAll();
  }else if(a=="four"){ //PIN 2 is OPEN CIRCUIT
    Serial.print("executed4");
    closeAll();
    digitalWrite(4,LOW);
    digitalWrite(24,LOW);  
    delay(y);
    digitalWrite(4,HIGH);
    digitalWrite(24,HIGH);
    closeAll();
  }else if(a=="five"){ //PIN 3 is CLOSED CIRCUIT
    Serial.print("executed5");
    closeAll();
    digitalWrite(4,LOW);
    digitalWrite(28,LOW);
    delay(y);
    digitalWrite(4,HIGH);
    digitalWrite(28,HIGH);
    closeAll();
  }else if(a=="six"){ //PIN 3 is OPEN CIRCUIT
    Serial.print("executed6");
    closeAll();
    digitalWrite(5,LOW);
    digitalWrite(26,LOW);
    delay(y);
    digitalWrite(5,HIGH);
    digitalWrite(26,HIGH);
    closeAll();
  }else if(a=="seven"){ //PIN 4 is CLOSED CIRCUIT
    Serial.print("executed7");
    closeAll();
    digitalWrite(5,LOW); 
    digitalWrite(30,LOW);
    delay(y);
    digitalWrite(5,HIGH);
    digitalWrite(30,HIGH);
    closeAll();
  }else if(a=="eight"){ //PIN 4 is OPEN CIRCUIT
    Serial.print("executed8");
    closeAll();
    digitalWrite(6,LOW); 
    digitalWrite(28,LOW);
    delay(y);
    digitalWrite(6,HIGH);
    digitalWrite(28,HIGH);
    closeAll();
    
    }else if(a=="nine"){ //PIN 5 is CLOSED CIRCUIT
    Serial.print("executed9");
    closeAll();
    digitalWrite(6,LOW); 
    digitalWrite(32,LOW);
    delay(y);
    digitalWrite(6,LOW);
    digitalWrite(32,LOW);
    closeAll();
    
    }else if(a=="ten"){ //PIN 5 is OPEN CIRCUIT
    Serial.print("executed10");
    closeAll();
    digitalWrite(7,LOW); 
    digitalWrite(30,LOW);
    delay(y);
    digitalWrite(7,HIGH);
    digitalWrite(30,HIGH);
    closeAll();
        
    }else if(a=="eleven"){ //PIN 6 is CLOSED CIRCUIT
    Serial.print("executed11");
    closeAll();  
    digitalWrite(7,LOW); 
    digitalWrite(34,LOW);
    delay(y);
    digitalWrite(7,HIGH);
    digitalWrite(34,HIGH);
    closeAll();
    
    }else if(a=="twelve"){ //PIN 6 is OPEN CIRCUIT
    Serial.print("executed12");
    closeAll();
    digitalWrite(8,LOW); 
    digitalWrite(32,LOW);
    delay(y);
    digitalWrite(8,HIGH);
    digitalWrite(32,LOW);
    closeAll();

    }
    else if (a=="reset"){ // 
      Serial.print("resetNow");
      closeAll();
      digitalWrite(3,LOW);
      digitalWrite(22,LOW);
      delay(y);
      digitalWrite(3,HIGH);
      digitalWrite(22,HIGH);
      closeAll();  
      delay(200);
      digitalWrite(4,LOW);
      digitalWrite(24,LOW);  
      delay(y);
      digitalWrite(4,HIGH);
      digitalWrite(24,HIGH);
      closeAll();
      delay(200);
      digitalWrite(5,LOW);
      digitalWrite(26,LOW);
      delay(y);
      digitalWrite(5,HIGH);
      digitalWrite(26,HIGH);
      closeAll();
      delay(200);
      digitalWrite(6,LOW); 
      digitalWrite(28,LOW);
      delay(y);
      digitalWrite(6,HIGH);
      digitalWrite(28,HIGH);
      closeAll();
      delay(200);
      digitalWrite(7,LOW); 
      digitalWrite(30,LOW);
      delay(y);
      digitalWrite(7,HIGH);
      digitalWrite(30,HIGH);
      closeAll();
      delay(200);
      digitalWrite(8,LOW); 
      digitalWrite(32,LOW);
      delay(y);
      digitalWrite(8,HIGH);
      digitalWrite(32,LOW);
      closeAll();
      
    }else{ //If command is not identified, it will close all the relays. 
     digitalWrite(2,HIGH);
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
}
/* Function name: closeAll()
 * Function type: Void
 * Function description: It will be called by activateSwitches in order to prevent any short circuit. 
 * 
 */
 void closeAll(){ 
     digitalWrite(2,HIGH);
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
 
 /*
  * Function Name: operationTime
  * Function Type: Void
  * Input: String a - The command coming from QSwitch-Box controller panel. Function will cut the first three words. Remaining is the time we want for total operation. 
  * Function Description: It will change the user input string to a float value and decleares to the global variable y. 
  */
 void operationTime(String a){
   Serial.print("dataTime"); //Prints dataTime to have a mutual communication between the control panel and Arduino. It will read it and gives a confirmation to user. 
   String myVal = a.substring(3); 
   float delayTime = myVal.toFloat();
   y = delayTime;
 }
