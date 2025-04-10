
import rclpy # ROS2 client library (rcl) for Python (built on rcl C API)
from rclpy.node import Node # Node class for Python nodes
from geometry_msgs.msg import Twist # Twist (linear and angular velocities) message class
from sensor_msgs.msg import Image 
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy # Ouality of Service (tune communication between nodes)
from rclpy.duration import Duration # Time duration class
from cv_bridge import CvBridge
# Python mudule imports
from math import inf # Common mathematical constant
import queue # FIFO queue
import time # Tracking time
import cv2
import numpy as np
# PID controller class
class PIDController:
    '''
    Generates control action taking into account instantaneous error (proportional action),
    accumulated error (integral action) and rate of change of error (derivative action).
    '''
    def __init__(self, kP, kI, kD, kS):
        self.kP       = kP # Proportional gain
        self.kI       = kI # Integral gain
        self.kD       = kD # Derivative gain
        self.kS       = kS # Saturation constant (error history buffer size)
        self.err_int  = 0 # Error integral
        self.err_dif  = 0 # Error difference
        self.err_prev = 0 # Previous error
        self.err_hist = queue.Queue(self.kS) # Limited buffer of error history
        self.t_prev   = 0 # Previous time

    def control(self, err, t):
        '''
        Generate PID controller output.
        :param err: Instantaneous error in control variable w.r.t. setpoint
        :param t  : Current timestamp
        :return u: PID controller output
        '''
        dt = t - self.t_prev # Timestep
        if dt > 0.0:
            self.err_hist.put(err) # Update error history
            self.err_int += err # Integrate error
            if self.err_hist.full(): # Jacketing logic to prevent integral windup
                self.err_int -= self.err_hist.get() # Rolling FIFO buffer
            self.err_dif = (err - self.err_prev) # Error difference
            u = (self.kP * err) + (self.kI * self.err_int * dt) + (self.kD * self.err_dif / dt) # PID control law
            self.err_prev = err # Update previos error term
            self.t_prev = t # Update timestamp
            return u # Control signal

# Node class
class RobotController(Node):

    #######################
    '''Class constructor'''
    #######################

    def __init__(self):
        # Information and debugging
        info = '\nMake the robot follow walls by maintaining equal distance from them.\n'
        print(info)
        # ROS2 infrastructure
        super().__init__('robot_controller') # Create a node with name 'robot_controller'
        qos_profile = QoSProfile( # Ouality of Service profile
        reliability=QoSReliabilityPolicy.RMW_QOS_POLICY_RELIABILITY_RELIABLE, # Reliable (not best effort) communication
        history=QoSHistoryPolicy.RMW_QOS_POLICY_HISTORY_KEEP_LAST, # Keep/store only up to last N samples
        depth=10 # Queue size/depth of 10 (only honored if the “history” policy was set to “keep last”)
        )
        self.bridge = CvBridge()
        self.robot_scan_sub = self.create_subscription(Image, '/camera/depth/image_raw', self.image_callback, qos_profile) # Subscriber which will subscribe to LaserScan message on the topic '/scan' adhering to 'qos_profile' QoS profile
        self.robot_scan_sub # Prevent unused variable warning
        self.robot_ctrl_pub = self.create_publisher(Twist, '/cmd_vel', qos_profile) # Publisher which will publish Twist message to the topic '/cmd_vel' adhering to 'qos_profile' QoS profile
        timer_period = 0.001 # Node execution time period (seconds)
        self.timer = self.create_timer(timer_period, self.robot_controller_callback) # Define timer to execute 'robot_controller_callback()' every 'timer_period' seconds
        self.depth_image = None # Initialize variable to capture the laserscan
        self.ctrl_msg = Twist() # Robot control commands (twist)
        self.start_time = self.get_clock().now() # Record current time in seconds
        self.pid_lat = PIDController(0.6, 0.01, 1.2, 10) # Lateral PID controller object initialized with kP, kI, kD, kS
        self.pid_lon = PIDController(0.1, 0.001, 0.05, 10) # Longitudinal PID controller object initialized with kP, kI, kD, kS
        self.safe_distance = 0.6
        self.turning = False
        self.turning_time = None
    ########################
    '''Callback functions'''
    ########################

    def image_callback(self, msg):
        """ Nhận ảnh từ camera RGB-D và chuyển đổi sang OpenCV """
        try:
            self.depth_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="passthrough")

        except Exception as e:
            self.get_logger().error(f"Error processing image: {e}")

    def get_distance(self, image, angle_range):
        """ Tính khoảng cách trung bình trong một vùng ảnh """
        h, w = image.shape
        center_y = h // 2  # Chọn hàng giữa ảnh
        x_start, x_end = int(w * angle_range[0]), int(w * angle_range[1])
        depth_values = image[center_y, x_start:x_end]  # Lấy dải chiều sâu
        depth_values = depth_values[~np.isnan(depth_values)]  # Bỏ giá trị NaN
        
        if len(depth_values) > 0:
            return np.mean(depth_values)  # Trả về khoảng cách trung bình
        else:
            return np.inf  # Nếu không có dữ liệu, trả về vô cực

    def robot_controller_callback(self):
        DELAY = 4.0 # Time delay (s)
        if self.get_clock().now() - self.start_time > Duration(seconds=DELAY):
            # Lấy khoảng cách từ camera
            left_distance = self.get_distance(self.depth_image, (0.0, 0.3))  # Vùng bên trái
            right_distance = self.get_distance(self.depth_image, (0.7, 1.0))  # Vùng bên phải
            front_distance = self.get_distance(self.depth_image, (0.45, 0.55))  # Trước mặt
            cte = left_distance - right_distance # Compute error (distance from either walls)

            if abs(cte) < 0.01:  # Nếu sai số dưới 1cm thì xem như CTE = 0
                cte = 0
            tstamp = time.time() # Current timestamp (s)
            # if front_distance < 0.7:
            #     LIN_VEL = 0.0 # Linear velocity (m/s) from longitudinal PID controller
            #     ANG_VEL = 0.15 # Angular velocity (rad/s)
            # elif front_distance < 0.7: 
            #     LIN_VEL = 0.0 # Linear velocity (m/s) from longitudinal PID controller
            #     ANG_VEL = -0.15 # Angular velocity (rad/s)
            # elif cte > 0:
            #     LIN_VEL = self.pid_lon.control(min(3.5, self.get_distance(self.depth_image, (0.4, 0.6))), tstamp) # Linear velocity (m/s) from longitudinal PID controller
            #     ANG_VEL = 0.15 # Angular velocity (rad/s)
            #     self.get_logger().info("Too close to right wall, turning left")
            # elif cte < 0:
            #     LIN_VEL = self.pid_lon.control(min(3.5, self.get_distance(self.depth_image, (0.4, 0.6))), tstamp) # Linear velocity (m/s) from longitudinal PID controller
            #     ANG_VEL = -0.15 # Angular velocity (rad/s)
            #     self.get_logger().info("Too close to left wall, turning right")
            # else:
            #     LIN_VEL = self.pid_lon.control(min(3.5, self.get_distance(self.depth_image, (0.4, 0.6))), tstamp) # Linear velocity (m/s) from longitudinal PID controller
            #     ANG_VEL = min(0.15, self.pid_lat.control(cte, tstamp)) # Angular velocity (rad/s) from lateral PID controller

            if self.turning:
                TURNING_TIME = 3
                if time.time() - self.turning_time > TURNING_TIME:
                    self.turning = False
            
            else: 
                if front_distance > 0.3 and cte == 0:
                    LIN_VEL = 0.3
                    ANG_VEL = 0.0
                elif front_distance < 0.3:  # Nếu có tường phía trước
                    LIN_VEL = 0.0
                    ANG_VEL = -0.5
                    # if left_distance > right_distance:
                    #     ANG_VEL = 0.5  # Quay trái nếu tường gần bên phải hơn
                    # else:
                    #     ANG_VEL = -0.5  # Quay phải nếu tường gần bên trái hơn
                    self.turning = True
                    self.turning_time = time.time()
                elif left_distance < self.safe_distance and front_distance > 0.3:  # Nếu quá gần tường
                    LIN_VEL = 0.2
                    ANG_VEL = -0.1  # Điều chỉnh nhẹ sang phải
                elif left_distance > self.safe_distance and front_distance > 0.3:  # Nếu quá xa tường
                    LIN_VEL = 0.2
                    ANG_VEL = 0.1  # Điều chỉnh nhẹ sang trái

                self.ctrl_msg.linear.x = LIN_VEL # Set linear velocity
                self.ctrl_msg.angular.z = ANG_VEL # Set angular velocity
                self.robot_ctrl_pub.publish(self.ctrl_msg) # Publish robot controls message
            self.get_logger().info(f'CTE: {cte:.4f} m | Left: {left_distance:.2f} | Right: {right_distance:.2f} | Front: {front_distance:.2f}')
        else:
            print('Initializing...')

def main(args=None):
    rclpy.init(args=args) # Start ROS2 communications
    node = RobotController() # Create node
    rclpy.spin(node) # Execute node
    node.destroy_node() # Destroy node explicitly (optional - otherwise it will be done automatically when garbage collector destroys the node object)
    rclpy.shutdown() # Shutdown ROS2 communications

if __name__ == "__main__":
    main()