#include <math.h>

// Cấu hình chân động cơ
const int LEFT_MOTOR_IN1= 6;  // Chân PWM cho động cơ trái
const int LEFT_MOTOR_IN2 = 7;  // Chân điều khiển chiều động cơ trái
const int RIGHT_MOTOR_IN1 = 5; // Chân PWM cho động cơ phải
const int RIGHT_MOTOR_IN2 = 4; // Chân điều khiển chiều động cơ phải

// Cấu hình tốc độ tối đa
const int MAX_PWM = 255;  // Giá trị PWM tối đa (0-255)

// Biến lưu tốc độ bánh xe
float WL = 0, WR = 0;



void robot_control(const your_package_name::PWMCommand& msg) {
  left = msg.pwm_left;
  right = msg.pwm_right;
      Serial.print("🚀 Tốc độ bánh trái (WL): ");
    Serial.println(left);
    Serial.print("🚀 Tốc độ bánh phải (WR): ");
    Serial.println(rights);

  // Điều khiển động cơ trái
  if (left > 0) {
    digitalWrite(LEFT_MOTOR_IN1, LOW); // Quay theo chiều thuật
    int v_left = int(constrain(left, 0, MAX_PWM));
    //Serial.println(v_left);
    analogWrite(LEFT_MOTOR_IN2, v_left);
 
  } else {
    digitalWrite(LEFT_MOTOR_IN2, LOW); // Quay theo chiều ngược
    int v_left = int(constrain(-left, 0, MAX_PWM));
//    Serial.println(v_left);
    analogWrite(LEFT_MOTOR_IN1, v_left);

  }

  // Điều khiển động cơ phải
  if (right > 0) {
    digitalWrite(RIGHT_MOTOR_IN1, LOW); // Quay theo chiều thuận
    int v_right = int(constrain(right, 0, MAX_PWM));
//    Serial.println(v_right);
    analogWrite(RIGHT_MOTOR_IN2, v_right);

  } else {
    digitalWrite(RIGHT_MOTOR_IN2, LOW); // Quay theo chiều ngược
    int v_right = int(constrain(-right, 0, MAX_PWM));
    //int real_v_right = (-255) + v_right;
//    Serial.println(v_right);
    analogWrite(RIGHT_MOTOR_IN1, v_right);
    

  }
}

ros::Subscriber<your_package_name::PWMCommand> pwm_sub("reader", &robot_control);

// Hàm khởi tạo
void setup() {
  // Cấu hình Serial2 để giao tiếp với HC-05
  //Serial2.begin(9600);  // HC-05 giao tiếp qua Serial2
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
  nh.spinOnce();
  delay(1); // Thời gian chờ nhỏ để duy trì giao tiếp ROS
}
