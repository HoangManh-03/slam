import rospy
# from rospy.duration import Duration
from math import inf  # Sử dụng 'Queue' cho Python 2 (ROS Noetic có thể dùng Python 2 hoặc 3)
import time
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import Float32MultiArray

# Python mudule imports
from math import inf # Common mathematical constant
import queue # FIFO queue
import time # Tracking time
import cv2
import numpy as np


# Node class
class RobotController(object):

    #######################
    '''Class constructor'''
    #######################

    def __init__(self):
        
        # ROS2 infrastructure
        rospy.init_node('robot_controller') # Create a node with name 'robot_controller'
        self.robot_ctrl_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10) 
        self.pub = rospy.Publisher('reader', Float32MultiArray, queue_size=10)
        self.timer = rospy.Timer(rospy.Duration(0.1), self.robot_controller_callback) # Define timer to execute 'robot_controller_callback()' every 'timer_period' seconds
        self.ctrl_msg = Twist() # Robot control commands (twist)
        self.start_time = rospy.Time.now() # Record current time (rospy.Time)

        self.turning = False
        self.turning_time = time.time()
        self.go_ahead_time = time.time()
        self.turning = False
        self.go_ahead = True
        self.pwm_left_value = False
        self.pwm_right_value = False
        self.rate = rospy.Rate(0.5)  # Publish rate (Hz)
        self.pwm_msg = Float32MultiArray()

    ########################
    '''Callback functions'''
    ########################
    
    def robot_controller_callback(self, timer_event):
        DELAY = 4.0 # Time delay (s)
        if rospy.Time.now() - self.start_time > rospy.Duration(DELAY):

            if self.turning:
                TURNING_TIME = 3
                self.LIN_VEL = False
                self.ANG_VEL = True
                if time.time() - self.turning_time > TURNING_TIME:
                    
                    self.turning = False
                    self.go_ahead = True
                    self.go_ahead_time = time.time()
            elif self.go_ahead:
                GO_AHEAD_TIME = 5
                self.LIN_VEL = True
                self.ANG_VEL = False
                if time.time() - self.go_ahead_time > GO_AHEAD_TIME:
        
                    self.turning = True
                    self.go_ahead = False
                    self.turning_time = time.time()

            while not rospy.is_shutdown():
                # Thay thế các giá trị này bằng logic điều khiển PWM của bạn
                if self.LIN_VEL:
                    self.pwm_left_value = 100  # Ví dụ giá trị PWM cho encoder trái
                    self.pwm_right_value = 100 # Ví dụ giá trị PWM cho encoder phải

                elif self.ANG_VEL:
                    self.pwm_left_value = 100  # Ví dụ giá trị PWM cho encoder trái
                    self.pwm_right_value = -70 # Ví dụ giá trị PWM cho encoder phải
                    
                self.pwm_msg.data = [self.pwm_left_value, self.pwm_right_value]

                rospy.loginfo(f"Publishing PWM: Left={self.pwm_left_value}, Right={self.pwm_right_value}")
                self.pub.publish(self.pwm_msg)
                self.rate.sleep()
            # self.ctrl_msg.linear.x = self.LIN_VEL # Set linear velocity
            # self.ctrl_msg.angular.z = self.ANG_VEL # Set angular velocity
            # self.robot_ctrl_pub.publish(self.ctrl_msg) # Publish robot controls message
            # print(f"turning = {self.turning}, go_ahead = {self.go_ahead}")
            # print(f"LIN_VEL = {self.LIN_VEL}, ANG_VEL = {self.ANG_VEL}")
        else:
            print('Initializing...')

if __name__ == '__main__':
    try:
        go_to_goal = RobotController()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass