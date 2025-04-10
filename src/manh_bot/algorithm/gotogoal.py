import rclpy
import math
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry

class GoToGoal(Node):
    def __init__(self):
        super().__init__('go_to_goal')
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)
        self.subscription = self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        self.timer = self.create_timer(0.1, self.move_to_goal)

        self.goal_x = -2.0  # Toạ độ X đích
        self.goal_y = -2.0  # Toạ độ Y đích

        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0  # Góc quay của robot

        self.ctrl_msg = Twist()

    def odom_callback(self, msg):
        """Lấy vị trí hiện tại của robot từ /odom"""
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y

        # Tính góc quay hiện tại từ quaternion
        q = msg.pose.pose.orientation
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        self.yaw = math.atan2(siny_cosp, cosy_cosp)

    def move_to_goal(self):
        """Di chuyển robot đến tọa độ (goal_x, goal_y)"""
        dx = self.goal_x - self.x
        dy = self.goal_y - self.y

        distance = math.sqrt(dx**2 + dy**2)  # Khoảng cách đến đích
        angle_to_goal = math.atan2(dy, dx)  # Góc cần quay đến mục tiêu

        if distance > 0.1:  # Nếu chưa đến mục tiêu
            if abs(angle_to_goal - self.yaw) > 0.1:  # Cần xoay trước
                self.ctrl_msg.linear.x = 0.0
                self.ctrl_msg.angular.z = 0.3 if angle_to_goal > self.yaw else -0.3
            else:  # Di chuyển thẳng
                self.ctrl_msg.linear.x = 0.2
                self.ctrl_msg.angular.z = 0.0
        else:  # Nếu đã đến nơi, dừng robot
            self.ctrl_msg.linear.x = 0.0
            self.ctrl_msg.angular.z = 0.0

        self.publisher_.publish(self.ctrl_msg)

def main(args=None):
    rclpy.init(args=args)
    node = GoToGoal()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
