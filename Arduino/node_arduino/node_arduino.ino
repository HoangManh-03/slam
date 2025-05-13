#include <math.h>
#include <ros.h>
#include <std_msgs/Float32MultiArray.h>

// Cấu hình chân động cơ
const int enA = 9;
const int enB = 10;
const int LEFT_MOTOR_IN1 = 6;  
const int LEFT_MOTOR_IN2 = 5;  
const int RIGHT_MOTOR_IN1 = 7;  
const int RIGHT_MOTOR_IN2 = 8; 
// Cấu hình tốc độ tối đa
int MAX_PWM = 0;   // Giá trị PWM tối đa (0-255)

// Biến lưu tốc độ bánh xe
float left = 0;
float right = 0;


std_msgs::Float32MultiArray chatter_msg;
ros::Publisher control_robot("chatter", &chatter_msg);

ros::NodeHandle nh; // Khai báo node handle ở phạm vi toàn cục

void robot_control(const std_msgs::Float32MultiArray& msg) {
  if (msg.data_length == 2) {
     left = msg.data[0];
     right = msg.data[1];
    chatter_msg.data_length = msg.data_length;
    chatter_msg.data[0] = left;
    chatter_msg.data[1] = right;

    control_robot.publish(&chatter_msg);
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
  pinMode(enA, OUTPUT);
  pinMode(enB, OUTPUT);

  // Cài đặt giá trị ban đầu cho chân điều khiển (dừng động cơ)
  digitalWrite(LEFT_MOTOR_IN1, LOW);
  digitalWrite(LEFT_MOTOR_IN2, LOW);
  digitalWrite(RIGHT_MOTOR_IN1, LOW);
  digitalWrite(RIGHT_MOTOR_IN2, LOW);
  analogWrite(enA, 0);
  analogWrite(enB, 0);

  Serial.println("🚀 Arduino Mega đã sẵn sàng!");

  nh.initNode();
  nh.subscribe(robot_control_sub); 
  nh.advertise(control_robot);
}

// Hàm chính
void loop() {
  nh.spinOnce();
  delay(10); // Thời gian chờ nhỏ để duy trì giao tiếp ROS
//  left = 0;
//  right = 0;
  // Điều khiển động cơ trái
  if (left >= 0) {
    digitalWrite(LEFT_MOTOR_IN1, 0); 
    digitalWrite(LEFT_MOTOR_IN2, 1);
    analogWrite(enA, left);
  }
  else if(left <= 0) {
    digitalWrite(LEFT_MOTOR_IN1, 1); 
    digitalWrite(LEFT_MOTOR_IN2, 0);
    analogWrite(enA, abs(left));
  }

  // Điều khiển động cơ phải
   if (right >= 0) {
    digitalWrite(RIGHT_MOTOR_IN1, 0); 
    digitalWrite(RIGHT_MOTOR_IN2, 1);
    analogWrite(enB, right);
  }
  else if(right <= 0) {
    digitalWrite(RIGHT_MOTOR_IN1, 1); 
    digitalWrite(RIGHT_MOTOR_IN2, 0);
    analogWrite(enB, abs(right));
  }
}
