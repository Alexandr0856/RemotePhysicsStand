
#include <Stepper.h>

int magnit_pin = 2;
int magnit_led = 13;
bool magnitState = 0;
int motorDirection = 1;
int motorSteps = 2900;
String output;
int command;

const int stepsPerRevolution = 420;
Stepper myStepper(stepsPerRevolution, 3, 4, 5, 6);

void setup() {
  pinMode(magnit_pin, OUTPUT);
  pinMode(magnit_led, OUTPUT);
  myStepper.setSpeed(100);
  Serial.begin(9600);
}

void loop() {
  if(Serial.available()>0){
    command = Serial.read()-'0';   
    if(command == 0){
      magnitState = 0;
      Serial.println("0,0");
    }
    else if(command == 1){
      myStepper.step(motorSteps);
      digitalWrite(magnit_pin, HIGH);
      digitalWrite(magnit_led, HIGH);
      Serial.println("1,1");
      myStepper.step(-motorSteps);
      
      delay(450);
      digitalWrite(magnit_pin, LOW);
      digitalWrite(magnit_led, LOW);
      Serial.println("1,0");

    }
  }
}
