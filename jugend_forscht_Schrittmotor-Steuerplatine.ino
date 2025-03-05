/*
  Arduino Slave for Raspberry Pi Master
  i2c_slave_ard.ino
  Connects to Raspberry Pi via I2C
  
  DroneBot Workshop 2019
  https://dronebotworkshop.com
*/

// Include the Wire library for I2C
#include <Wire.h>
#include <TMCStepper.h>
#include <SoftwareSerial.h>

// LED on pin 13

#define STEP_PIN  3    // Step pin
#define EN_PIN    4
#define SW_RX     10   // SoftwareSerial RX (connected to TMC2209 TX)
#define SW_TX     11   // SoftwareSerial TX (connected to TMC2209 RX)
#define R_SENSE   0.11 // Sense resistor value
#define DRIVER_ADDRESS 0b00 // Driver address (CFG0/CFG1 pins)

int c = 0;
int speed = 0;

SoftwareSerial SERIAL_PORT(SW_RX, SW_TX); // RX, TX

// Driver configuration
TMC2209Stepper driver(&SERIAL_PORT, R_SENSE, DRIVER_ADDRESS);

void setup() {
  // Join I2C bus as slave with address 8
  Wire.begin(0x8);
  SERIAL_PORT.begin(115200);
  // Call receiveEvent when data received                
  Wire.onReceive(receiveEvent);

  driver.begin();
  driver.toff(4); // Enable driver in SpreadCycle mode
  driver.en_spreadCycle(false); // Enable SpreadCycle
  driver.I_scale_analog(false); // Use internal reference voltage
  driver.rms_current(1500); // Set motor current (mA)
  driver.microsteps(8); // Set microstepping
  
  // Setup pin 13 as output and turn LED off
  pinMode(STEP_PIN, OUTPUT);
  pinMode(EN_PIN, OUTPUT);

  Serial.begin(57600);
}

// Function that executes whenever data is received from master
void receiveEvent(int howMany) {
  while (Wire.available()) { // loop through all but the last
    c = Wire.read(); // receive byte as a character
    Serial.println(c);
  }
}
void loop() {
  digitalWrite(EN_PIN, LOW);

  if (c == 0){
    speed = 0;
  }
  else if (c == 1){
    speed = 400;
  }
  else if (c == 2){
    speed = 300;
  }
  else if (c == 3){
    speed = 200;
  }


  if (speed == 0){
    digitalWrite(EN_PIN, HIGH);
    digitalWrite(STEP_PIN, LOW);
  }
  else{
    digitalWrite(STEP_PIN, HIGH);
    delayMicroseconds(speed);
    digitalWrite(STEP_PIN, LOW);
    delayMicroseconds(speed);
  }
}