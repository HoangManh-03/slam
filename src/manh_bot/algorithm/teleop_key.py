# import rospy
# # from rospy.duration import Duration
# from math import inf  # Sử dụng 'Queue' cho Python 2 (ROS Noetic có thể dùng Python 2 hoặc 3)
# import time
# from geometry_msgs.msg import Twist
# from nav_msgs.msg import Odometry
# from std_msgs.msg import Float32MultiArray

# # Python mudule imports
# from math import inf # Common mathematical constant
# import queue # FIFO queue
# import time # Tracking time


# # Node class
# class RobotController(object):

#     #######################
#     '''Class constructor'''
#     #######################

#     def __init__(self):
        
#         # ROS2 infrastructure
#         rospy.init_node('robot_controller') # Create a node with name 'robot_controller'
#         self.robot_ctrl_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10) 
#         self.pub = rospy.Publisher('reader', Float32MultiArray, queue_size=10)
#         self.timer = rospy.Timer(rospy.Duration(0.1), self.robot_controller_callback) # Define timer to execute 'robot_controller_callback()' every 'timer_period' seconds
#         self.ctrl_msg = Twist() # Robot control commands (twist)
#         self.start_time = rospy.Time.now() # Record current time (rospy.Time)

#         self.turning = False
#         self.turning_time = time.time()
#         self.go_ahead_time = time.time()
#         self.turning = False
#         self.go_ahead = True
#         self.pwm_left_value = 0.0
#         self.pwm_right_value = 0.0
#         self.rate = rospy.Rate(0.5)  # Publish rate (Hz)
#         self.pwm_msg = Float32MultiArray()

#     ########################
#     '''Callback functions'''
#     ########################
    
#     def robot_controller_callback(self, timer_event):
#         DELAY = 4.0 # Time delay (s)
#         if rospy.Time.now() - self.start_time > rospy.Duration(DELAY):

#             if self.turning:
#                 TURNING_TIME = 3
#                 self.LIN_VEL = False
#                 self.ANG_VEL = True
#                 if time.time() - self.turning_time > TURNING_TIME:
                    
#                     self.turning = False
#                     self.go_ahead = True
#                     self.go_ahead_time = time.time()
#             elif self.go_ahead:
#                 GO_AHEAD_TIME = 5
#                 self.LIN_VEL = True
#                 self.ANG_VEL = False
#                 if time.time() - self.go_ahead_time > GO_AHEAD_TIME:
        
#                     self.turning = True
#                     self.go_ahead = False
#                     self.turning_time = time.time()

#             # while not rospy.is_shutdown():
#                 # Thay thế các giá trị này bằng logic điều khiển PWM của bạn
#             if self.LIN_VEL:
#                 self.pwm_left_value = 100  # Ví dụ giá trị PWM cho encoder trái
#                 self.pwm_right_value = 100 # Ví dụ giá trị PWM cho encoder phải

#             elif self.ANG_VEL:
#                 self.pwm_left_value = 0  # Ví dụ giá trị PWM cho encoder trái
#                 self.pwm_right_value = 0 # Ví dụ giá trị PWM cho encoder phải

#             self.pwm_msg.data = [self.pwm_left_value, self.pwm_right_value]

#             rospy.loginfo(f"Publishing PWM: Left={self.pwm_left_value}, Right={self.pwm_right_value}")
#             self.pub.publish(self.pwm_msg)
#             self.rate.sleep()

#         else:
#             print('Initializing...')

# if __name__ == '__main__':
#     try:
#         go_to_goal = RobotController()
#         rospy.spin()
#     except rospy.ROSInterruptException:
#         pass


#!/usr/bin/env python3

import rospy
import sys
import select
import os
from std_msgs.msg import Float32MultiArray
import threading
import sys, select, termios, tty

if os.name == 'nt':
    import msvcrt
else:
    import tty
    import termios

SPEED_PWM = 100

MSG = """
Control Your Robot!
---------------------------
Reading from the keyboard  and Publishing to Twist!
---------------------------
Moving around:
       i    
   j    k    l
       ,    

CTRL-C to quit
"""

ERROR_MSG = """
Teleop Class Failed
"""
moveBindings = {
        'i':(1,1),
        'j':(-1,1),
        'l':(1,-1),
        ',':(-1,-1),
        'k':(0,0)
    }

class TeleopKey(threading.Thread):
    def __init__(self, rate):
        super(TeleopKey, self).__init__()

        self.pub = rospy.Publisher('reader', Float32MultiArray, queue_size=10)
        # self.pwm_msg = Float32MultiArray()
        self.rate = rospy.Rate(0.5)  # Publish rate (Hz)
        self.left_pwm = 0
        self.right_pwm = 0
        self.condition = threading.Condition()
        self.done = False
        self.speed = 0
        if rate != 0.0:
            self.timeout = 1.0 / rate
        else:
            self.timeout = None

        self.start()
    
    def wait_for_subscribers(self):
        i = 0
        while not rospy.is_shutdown() and self.pub.get_num_connections() == 0:
            if i == 4:
                print("Waiting for subscriber to connect to {}".format(self.pub.name))
            rospy.sleep(0.5)
            i += 1
            i = i % 5
        if rospy.is_shutdown():
            raise Exception("Got shutdown request before subscribers connected")
        
    def update(self, left_pwm, right_pwm, speed):
        self.condition.acquire()
        self.left_pwm=left_pwm
        self.right_pwm=right_pwm
        self.speed = speed
        
        # Notify publish thread that we have a new message.
        self.condition.notify()
        self.condition.release()

    def stop(self):
        self.done = True
        self.update(0,0,0)
        self.join()

    def run(self):
        pwm_msg = Float32MultiArray()
        while not self.done:
            self.condition.acquire()
            # Wait for a new message or timeout.
            self.condition.wait(self.timeout)

            # Copy state into twist message.
            self.left_pwm=left_pwm*self.speed
            self.right_pwm=right_pwm*self.speed
            print(vels(self.left_pwm,self.right_pwm))
            self.condition.release()
            pwm_msg.data=[self.left_pwm,self.right_pwm]
            # Publish.
            self.pub.publish(pwm_msg)

        # Publish stop message when thread exits.
        pwm_msg.data=[0.0,0.0]
        self.pub.publish(pwm_msg)
    
def getKey(key_timeout):
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], key_timeout)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


def vels(left,right):
    return "currently:\tspeed %s\tturn %s " % (left,right)

   
if __name__ == '__main__':
    settings = termios.tcgetattr(sys.stdin)

    rospy.init_node('teleop_keyboard')

    speed = rospy.get_param("~speed", 100)
    repeat = rospy.get_param("~repeat_rate", 0.0)
    key_timeout = rospy.get_param("~key_timeout", 0.0)
    if key_timeout == 0.0:
        key_timeout = None

    pub_thread = TeleopKey(repeat)

    left_pwm = 0
    right_pwm = 0
    status = 0

    try:
        pub_thread.wait_for_subscribers()
        pub_thread.update(left_pwm,right_pwm,speed)

        print(MSG)
        
        while(1):
            key = getKey(key_timeout)
            if key in moveBindings.keys():
                left_pwm = moveBindings[key][0]
                right_pwm = moveBindings[key][1]
            
            else:
                # Skip updating cmd_vel if key timeout and robot already
                # stopped.
                if key == '' and left_pwm == 0 and right_pwm == 0:
                    continue
                left_pwm=0
                right_pwm=0
                if (key == '\x03'):
                    break
            
            pub_thread.update(left_pwm, right_pwm, speed)

    except Exception as e:
        print(e)

    finally:
        pub_thread.stop()

        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
