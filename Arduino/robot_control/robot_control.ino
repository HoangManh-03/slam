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

// Hàm khởi tạo
void setup() {
  // Cấu hình Serial2 để giao tiếp với HC-05
  Serial2.begin(9600);  // HC-05 giao tiếp qua Serial2
  Serial.begin(9600);   // Debug qua Serial Monitor

  // Cấu hình chân động cơ
  pinMode(LEFT_MOTOR_IN1, OUTPUT);
  pinMode(RIGHT_MOTOR_IN2, OUTPUT);
  pinMode(LEFT_MOTOR_IN1, OUTPUT);
  pinMode(RIGHT_MOTOR_IN2, OUTPUT);

  Serial.println("🚀 Arduino Mega đã sẵn sàng!");
}

// Hàm điều khiển động cơ
void motor(float left, float right) {
  // Điều khiển động cơ trái
  if (left > 0) {
    digitalWrite(LEFT_MOTOR_IN1, LOW); // Quay theo chiều thuật
    int v_left = int(constrain(left, 0, MAX_PWM));
    Serial.println(v_left);
    analogWrite(LEFT_MOTOR_IN2, v_left);
 
  } else {
    digitalWrite(LEFT_MOTOR_IN2, LOW); // Quay theo chiều ngược
    int v_left = int(constrain(-left, 0, MAX_PWM));
    Serial.println(v_left);
    analogWrite(LEFT_MOTOR_IN1, v_left);

  }

  // Điều khiển động cơ phải
  if (right > 0) {
    digitalWrite(RIGHT_MOTOR_IN1, LOW); // Quay theo chiều thuận
    int v_right = int(constrain(right, 0, MAX_PWM));
    Serial.println(v_right);
    analogWrite(RIGHT_MOTOR_IN2, v_right);

  } else {
    digitalWrite(RIGHT_MOTOR_IN2, LOW); // Quay theo chiều ngược
    int v_right = int(constrain(-right, 0, MAX_PWM));
    //int real_v_right = (-255) + v_right;
    Serial.println(v_right);
    analogWrite(RIGHT_MOTOR_IN1, v_right);
    

  }
}

// Hàm chính
void loop() {
  static String receivedData = ""; // Biến lưu dữ liệu nhận được
  char incomingChar;

  // Kiểm tra nếu có dữ liệu đến từ HC-05
  if (Serial2.available()) {
    incomingChar = Serial2.read();  // Đọc ký tự một lần từ Bluetooth
    
    // Thêm ký tự vào chuỗi nhận
    receivedData += incomingChar;
    
    // Nếu nhận được ký tự '#', xử lý chuỗi
    if (incomingChar == '#') {
      // In ra dữ liệu đã nhận
      Serial.println("📥 Dữ liệu nhận: " + receivedData);

      // Tách dữ liệu tại dấu ';'
      int firstSemicolon = receivedData.indexOf(';');
      int secondSemicolon = receivedData.indexOf(';', firstSemicolon + 1);

      if (firstSemicolon >= 0 && secondSemicolon > firstSemicolon) {
        // Lấy các phần số
        String wlStr = receivedData.substring(0, firstSemicolon);
        String wrStr = receivedData.substring(firstSemicolon + 1, secondSemicolon);

        // Chuyển các phần tử chuỗi thành số
        WL = wlStr.toFloat();
        WR = wrStr.toFloat();

        // Debug thông tin
        Serial.print("🚀 Tốc độ bánh trái (WL): ");
        Serial.println(WL);
        Serial.print("🚀 Tốc độ bánh phải (WR): ");
        Serial.println(WR);

        // Điều khiển động cơ
        motor(WL, WR);
      }

      // Xóa chuỗi để chuẩn bị nhận dữ liệu tiếp theo
      receivedData = "";
    }
  }
}