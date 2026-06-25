  // --- PINS (TCE Robot Hardware) ---
  const int DIR1 = 6; const int PWM1 = 10;
  const int DIR2 = 5; const int PWM2 = 9;
  const int L_ENC_A = 3; 

  // --- CALIBRATION ---
  const float TICKS_PER_CM = 20.0; 
  const int STOPPING_OFFSET = 3; 
  const float TICKS_PER_DEG = 3.3; // Base calibration for 90 deg

  const int MOVE_SPEED = 50; 
  const int TURN_SPEED = 50;

volatile long left_ticks = 0;

void setup() {
  Serial.begin(9600);
  pinMode(DIR1, OUTPUT); pinMode(PWM1, OUTPUT);
  pinMode(DIR2, OUTPUT); pinMode(PWM2, OUTPUT);
  attachInterrupt(digitalPinToInterrupt(L_ENC_A), [](){ left_ticks++; }, RISING);
  stopRobot();
}

void loop() {

  if (Serial.available() > 0) {

    char cmd = Serial.read();

    switch (cmd) {

      case 'F':
        moveForwardCell();
        break;

      case 'L':
        pivot(90, true);
        break;

      case 'R':
        pivot(90, false);
        break;

      case 'B':
        pivot(180, true);   // U-turn
        break;

      case 'S':
        stopRobot();
        break;
    }

    while (Serial.available() > 0)
      Serial.read();
  }
}

void moveDistance(int cm, int direction) {
  if (cm <= 0) return;
  int targetCm = (cm > STOPPING_OFFSET) ? cm - STOPPING_OFFSET : 0;
  long targetTicks = targetCm * TICKS_PER_CM;
  left_ticks = 0;
  digitalWrite(DIR1, direction); digitalWrite(DIR2, direction);
  analogWrite(PWM1, MOVE_SPEED); analogWrite(PWM2, MOVE_SPEED);
  while(left_ticks < targetTicks); 
  stopRobot();
}

void pivot(int degrees, bool isLeft) {

  long targetTicks =
      (long)(degrees * TICKS_PER_DEG);

  left_ticks = 0;

  if (isLeft) {

    digitalWrite(DIR1, HIGH);
    digitalWrite(DIR2, LOW);

  } else {

    digitalWrite(DIR1, LOW);
    digitalWrite(DIR2, HIGH);
  }

  analogWrite(PWM1, TURN_SPEED);
  analogWrite(PWM2, TURN_SPEED);

  while (left_ticks < targetTicks);

  stopRobot();
}
void moveByTime(int seconds, int direction) {
  digitalWrite(DIR1, direction); digitalWrite(DIR2, direction);
  analogWrite(PWM1, MOVE_SPEED); analogWrite(PWM2, MOVE_SPEED);
  delay(seconds * 1000);
  stopRobot();
}

void moveForwardCell() {

  const int CELL_CM = 23;

  long targetTicks = CELL_CM * TICKS_PER_CM;

  left_ticks = 0;

  digitalWrite(DIR1, LOW);
  digitalWrite(DIR2, LOW);

  analogWrite(PWM1, MOVE_SPEED);
  analogWrite(PWM2, MOVE_SPEED);

  while (left_ticks < targetTicks);

  stopRobot();
}


void stopRobot() {
  digitalWrite(DIR1, 0); digitalWrite(DIR2, 0);
  digitalWrite(PWM1, 0); digitalWrite(PWM2, 0);
}