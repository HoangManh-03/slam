#include <math.h>

// Cấu hình chân động cơ
const int LEFT_MOTOR_IN1= 6;  // Chân PWM cho động cơ trái
const int LEFT_MOTOR_IN2 = 7;  // Chân điều khiển chiều động cơ trái
const int RIGHT_MOTOR_IN1 = 5; // Chân PWM cho động cơ phải
const int RIGHT_MOTOR_IN2 = 4; // Chân điều khiển chiều động cơ phải


// Biến lưu tốc độ bánh xe
float left = 100;
float right = -50;

// Hàm khởi tạo
void setup() {

  Serial.begin(9600);   // Debug qua Serial Monitor

  // Cấu hình chân động cơ
  pinMode(LEFT_MOTOR_IN1, OUTPUT);
  pinMode(RIGHT_MOTOR_IN2, OUTPUT);
  pinMode(LEFT_MOTOR_IN1, OUTPUT);
  pinMode(RIGHT_MOTOR_IN2, OUTPUT);

  Serial.println("🚀 Arduino Mega đã sẵn sàng!");
}

// Hàm chính
void loop() {
  delay(1); 

  if (left >= 0) {
    digitalWrite(LEFT_MOTOR_IN1, 0); 
    digitalWrite(LEFT_MOTOR_IN2, 1);
    analogWrite(LEFT_MOTOR_IN2, left);
  }
  else if(left <= 0) {
    digitalWrite(LEFT_MOTOR_IN1, 1); 
    digitalWrite(LEFT_MOTOR_IN2, 0);
    analogWrite(LEFT_MOTOR_IN1, abs(left));
  }

  // Điều khiển động cơ phải
   if (right >= 0) {
    digitalWrite(RIGHT_MOTOR_IN1, 0); 
    digitalWrite(RIGHT_MOTOR_IN2, 1);
    analogWrite(RIGHT_MOTOR_IN2, right);
  }
  else if(right <= 0) {
    digitalWrite(RIGHT_MOTOR_IN1, 1); 
    digitalWrite(RIGHT_MOTOR_IN2, 0);
    analogWrite(RIGHT_MOTOR_IN1, abs(right));
  }
}
