#include <math.h>
#include <ros.h>
#include <std_msgs/Float32MultiArray.h>

// Cấu hình chân động cơ
const int LEFT_MOTOR_IN1 = 6;   // Chân PWM cho động cơ trái
const int LEFT_MOTOR_IN2 = 7;   // Chân điều khiển chiều động cơ trái
const int RIGHT_MOTOR_IN1 = 5;  // Chân PWM cho động cơ phải
const int RIGHT_MOTOR_IN2 = 4;  // Chân điều khiển chiều động cơ phải

// Cấu hình tốc độ tối đa
int MAX_PWM = 0;   // Giá trị PWM tối đa (0-255)

// Biến lưu tốc độ bánh xe
float left = 0;
float right = 0;


std_msgs::Float32MultiArray chatter_msg;
ros::Publisher chatter("chatter", &chatter_msg);

ros::NodeHandle nh; // Khai báo node handle ở phạm vi toàn cục

void robot_control(const std_msgs::Float32MultiArray& msg) {
  if (msg.data_length == 2) {
     left = msg.data[0];
     right = msg.data[1];
    chatter_msg.data_length = msg.data_length;
    chatter_msg.data[0] = left;
    chatter_msg.data[1] = right;
//    for (int i = 0; i < msg.data_length; ++i) {
//      chatter_msg.data[i] = msg.data[i]; // Assuming chatter_msg.data is an array large enough
//    }
    chatter.publish(&chatter_msg);
    Serial.print("🚀 Tốc độ bánh trái (Left): ");
    Serial.println(left);
    Serial.print("🚀 Tốc độ bánh phải (Right): ");
    Serial.println(right);

    
  }
}
ros::Subscriber<std_msgs::Float32MultiArray> robot_control_sub("reader", &robot_control); // Đổi tên biến subscriber

// Hàm khởi tạo
void setup() {
  Serial.begin(57600);   // Debug qua Serial Monitor

  // Cấu hình chân động cơ
  pinMode(LEFT_MOTOR_IN1, OUTPUT);
  pinMode(LEFT_MOTOR_IN2, OUTPUT);
  pinMode(RIGHT_MOTOR_IN1, OUTPUT);
  pinMode(RIGHT_MOTOR_IN2, OUTPUT);

  // Cài đặt giá trị ban đầu cho chân điều khiển (dừng động cơ)
  digitalWrite(LEFT_MOTOR_IN1, LOW);
  digitalWrite(LEFT_MOTOR_IN2, LOW);
  digitalWrite(RIGHT_MOTOR_IN1, LOW);
  digitalWrite(RIGHT_MOTOR_IN2, LOW);

  Serial.println("🚀 Arduino Mega đã sẵn sàng!");

  nh.initNode();
  nh.subscribe(robot_control_sub); //
  nh.advertise(chatter);
}

// Hàm chính
void loop() {
  nh.spinOnce();
  delay(1); // Thời gian chờ nhỏ để duy trì giao tiếp ROS
//  left = -100;
//  right = 50;
  // Điều khiển động cơ trái
  if (left > 0) {
    digitalWrite(LEFT_MOTOR_IN1, 0); 
    digitalWrite(LEFT_MOTOR_IN2, 1);
    analogWrite(LEFT_MOTOR_IN2, left);
  }
  else if(left < 0) {
    digitalWrite(LEFT_MOTOR_IN1, 1); 
    digitalWrite(LEFT_MOTOR_IN2, 0);
    analogWrite(LEFT_MOTOR_IN1, abs(left));
  }

  // Điều khiển động cơ phải
   if (right > 0) {
    digitalWrite(RIGHT_MOTOR_IN1, 0); 
    digitalWrite(RIGHT_MOTOR_IN2, 1);
    analogWrite(RIGHT_MOTOR_IN2, right);
  }
  else if(right < 0) {
    digitalWrite(RIGHT_MOTOR_IN1, 1); 
    digitalWrite(RIGHT_MOTOR_IN2, 0);
    analogWrite(RIGHT_MOTOR_IN1, abs(right));
  }
}
