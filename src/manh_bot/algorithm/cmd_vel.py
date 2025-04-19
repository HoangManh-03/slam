import rospy
from geometry_msgs.msg import Twist
import sys, select, os
from std_msgs.msg import Float32MultiArray

if os.name == 'nt':
  import msvcrt
else:
  import tty, termios

# Các thông số robot (cần điều chỉnh cho robot của bạn)
WHEEL_SEPARATION = 0.2  # Khoảng cách giữa hai bánh xe (m)
WHEEL_RADIUS = 0.05     # Bán kính bánh xe (m)
MAX_LINEAR_VEL = 0.5    # Vận tốc tuyến tính tối đa (m/s)
MAX_ANGULAR_VEL = 1.0 #ận tốc góc tối đa (rad/s)


# Các thông số PWM (cần điều chỉnh cho driver động cơ của bạn)
PWM_RANGE = 255.0
MAX_WHEEL_RPM = 100.0  # Tốc độ quay tối đa của bánh xe (RPM) - cần ước tính hoặc đo
PWM_PER_RPM = PWM_RANGE / MAX_WHEEL_RPM # Hệ số chuyển đổi RPM sang PWM
pwm_msg = Float32MultiArray()

msg = """
Control Your TurtleBot3!
---------------------------
Moving around:
        w
   a    s    d
        x

CTRL-C to quit
"""

e = """
Communications Failed
"""

def getKey():
    if os.name == 'nt':
      if sys.version_info[0] >= 3:
        return msvcrt.getch().decode()
      else:
        return msvcrt.getch()

    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''

    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key

def vels(target_linear_vel, target_angular_vel):
    return "currently:\tlinear vel %s\t angular vel %s " % (target_linear_vel,target_angular_vel)

def cmd_vel_callback(twist_msg):
    linear_vel_x = twist_msg.linear.x
    angular_vel_z = twist_msg.angular.z
    vels(linear_vel_x,angular_vel_z)

    # Giới hạn vận tốc (tùy chọn)
    linear_vel_x = max(-MAX_LINEAR_VEL, min(linear_vel_x, MAX_LINEAR_VEL))
    angular_vel_z = max(-MAX_ANGULAR_VEL, min(angular_vel_z, MAX_ANGULAR_VEL))

    # Tính toán vận tốc bánh xe (rad/s)
    left_wheel_vel_rad_s = (linear_vel_x - (angular_vel_z * WHEEL_SEPARATION / 2.0)) / WHEEL_RADIUS
    right_wheel_vel_rad_s = (linear_vel_x + (angular_vel_z * WHEEL_SEPARATION / 2.0)) / WHEEL_RADIUS

    # Chuyển đổi vận tốc bánh xe (rad/s) sang RPM
    left_wheel_rpm = left_wheel_vel_rad_s * 60.0 / (2 * 3.14159)
    right_wheel_rpm = right_wheel_vel_rad_s * 60.0 / (2 * 3.14159)

    # Giới hạn tốc độ bánh xe (RPM) (tùy chọn)
    left_wheel_rpm = max(-MAX_WHEEL_RPM, min(left_wheel_rpm, MAX_WHEEL_RPM))
    right_wheel_rpm = max(-MAX_WHEEL_RPM, min(right_wheel_rpm, MAX_WHEEL_RPM))

    # Chuyển đổi RPM sang giá trị PWM (điều chỉnh dấu dựa trên hướng động cơ)
    left_pwm = int(left_wheel_rpm * PWM_PER_RPM)
    right_pwm = int(right_wheel_rpm * PWM_PER_RPM)

    # Tạo message Float32MultiArray để gửi PWM đến Arduino
    
    pwm_msg.data = [float(left_pwm), float(right_pwm)]


if __name__=="__main__":
    if os.name != 'nt':
        settings = termios.tcgetattr(sys.stdin)

    pwm_pub = rospy.Publisher('arduino_pwm', Float32MultiArray, queue_size=10) # Publish PWM lên topic 'arduino_pwm'

    rospy.init_node('turtlebot3_teleop')
    cmd_vel_sub = rospy.Subscriber('/cmd_vel', Twist, cmd_vel_callback)

    target_linear_vel   = 0.0
    target_angular_vel  = 0.0
    control_linear_vel  = 0.0
    control_angular_vel = 0.0

    try:
        print(msg)
        while(1):
            key = getKey()
            if key == 'w' :
                target_linear_vel = MAX_LINEAR_VEL
                
                print(vels(target_linear_vel,target_angular_vel))
            elif key == 'x' :
                target_linear_vel = -MAX_LINEAR_VEL
              
                print(vels(target_linear_vel,target_angular_vel))
            elif key == 'a' :
                target_angular_vel = MAX_ANGULAR_VEL
             
                print(vels(target_linear_vel,target_angular_vel))
            elif key == 'd' :
                target_angular_vel = -MAX_ANGULAR_VEL
              
                print(vels(target_linear_vel,target_angular_vel))
            elif key == ' ' or key == 's' :
                target_linear_vel   = 0.0
                control_linear_vel  = 0.0
                target_angular_vel  = 0.0
                control_angular_vel = 0.0
                print(vels(target_linear_vel, target_angular_vel))
            else:
                if (key == '\x03'):
                    break
            
            pwm_pub.publish(pwm_msg)
            rospy.loginfo(f"Publishing PWM: Left={left_pwm}, Right={right_pwm}")
            

    except:
        print(e)

    finally:
        twist = Twist()
        twist.linear.x = 0.0; twist.linear.y = 0.0; twist.linear.z = 0.0
        twist.angular.x = 0.0; twist.angular.y = 0.0; twist.angular.z = 0.0
        cmd_vel_sub.publish(twist)

    if os.name != 'nt':
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)


#!/usr/bin/env python3

from __future__ import print_function

import threading
import math
import roslib; roslib.load_manifest('teleop_twist_keyboard')
import rospy

from geometry_msgs.msg import Twist

import sys, select, termios, tty

# Các thông số robot (cần điều chỉnh cho robot của bạn)
WHEEL_SEPARATION = 0.1665  # Khoảng cách giữa hai bánh xe (m)
WHEEL_RADIUS = 0.06     # Bán kính bánh xe (m)
MAX_LINEAR_VEL = 0.5    # Vận tốc tuyến tính tối đa (m/s)
MAX_ANGULAR_VEL = 1.0 #Vận tốc góc tối đa (rad/s)


# Các thông số PWM (cần điều chỉnh cho driver động cơ của bạn)
PWM_RANGE = 255.0
MAX_WHEEL_RPM = 100.0  # Tốc độ quay tối đa của bánh xe (RPM) - cần ước tính hoặc đo
PWM_PER_RPM = PWM_RANGE / MAX_WHEEL_RPM # Hệ số chuyển đổi RPM sang PWM
pwm_msg = Float32MultiArray()

msg = """
Reading from the keyboard  and Publishing to Twist!
---------------------------
Moving around:
        i    
    j    k    l
        ,    


CTRL-C to quit
"""

moveBindings = {
        'i':(1,1),
        'j':(-1,1),
        'l':(1,-1),
        ',':(-1,-1),
        'k':(0,0)
    }


class PublishThread(threading.Thread):
    def __init__(self, rate):
        super(PublishThread, self).__init__()
        self.publisher = rospy.Publisher('cmd_vel', Twist, queue_size = 1)
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.th = 0.0
        self.speed = 0.0
        self.turn = 0.0
        self.condition = threading.Condition()
        self.done = False
        

        # Set timeout to None if rate is 0 (causes new_message to wait forever
        # for new data to publish)
        if rate != 0.0:
            self.timeout = 1.0 / rate
        else:
            self.timeout = None

        self.start()

    def wait_for_subscribers(self):
        i = 0
        while not rospy.is_shutdown() and self.publisher.get_num_connections() == 0:
            if i == 4:
                print("Waiting for subscriber to connect to {}".format(self.publisher.name))
            rospy.sleep(0.5)
            i += 1
            i = i % 5
        if rospy.is_shutdown():
            raise Exception("Got shutdown request before subscribers connected")

    def cmd_vel_callback(twist_msg):
        linear_vel_x = twist_msg.linear.x
        angular_vel_z = twist_msg.angular.z
        vels(linear_vel_x,angular_vel_z)

        # Giới hạn vận tốc (tùy chọn)
        linear_vel_x = max(-MAX_LINEAR_VEL, min(linear_vel_x, MAX_LINEAR_VEL))
        angular_vel_z = max(-MAX_ANGULAR_VEL, min(angular_vel_z, MAX_ANGULAR_VEL))

        # Tính toán vận tốc bánh xe (rad/s)
        left_wheel_vel_rad_s = (linear_vel_x - (angular_vel_z * WHEEL_SEPARATION / 2.0)) / WHEEL_RADIUS
        right_wheel_vel_rad_s = (linear_vel_x + (angular_vel_z * WHEEL_SEPARATION / 2.0)) / WHEEL_RADIUS

        # Chuyển đổi vận tốc bánh xe (rad/s) sang RPM
        left_wheel_rpm = left_wheel_vel_rad_s * 60.0 / (2 * math.pi)
        right_wheel_rpm = right_wheel_vel_rad_s * 60.0 / (2 * math.pi)

        # Giới hạn tốc độ bánh xe (RPM) (tùy chọn)
        left_wheel_rpm = max(-MAX_WHEEL_RPM, min(left_wheel_rpm, MAX_WHEEL_RPM))
        right_wheel_rpm = max(-MAX_WHEEL_RPM, min(right_wheel_rpm, MAX_WHEEL_RPM))

        # Chuyển đổi RPM sang giá trị PWM (điều chỉnh dấu dựa trên hướng động cơ)
        left_pwm = int(left_wheel_rpm * PWM_PER_RPM)
        right_pwm = int(right_wheel_rpm * PWM_PER_RPM)

        # Tạo message Float32MultiArray để gửi PWM đến Arduino
        
        pwm_msg.data = [float(left_pwm), float(right_pwm)]

    def update(self, x, y, z, th, speed, turn):
        self.condition.acquire()
        self.x = x
        self.y = y
        self.z = z
        self.th = th
        self.speed = speed
        self.turn = turn
        # Notify publish thread that we have a new message.
        self.condition.notify()
        self.condition.release()

    def stop(self):
        self.done = True
        self.update(0, 0, 0, 0, 0, 0)
        self.join()

    def run(self):
        twist = Twist()
        while not self.done:
            self.condition.acquire()
            # Wait for a new message or timeout.
            self.condition.wait(self.timeout)

            # Copy state into twist message.
            twist.linear.x = self.x * self.speed
            twist.linear.y = self.y * self.speed
            twist.linear.z = self.z * self.speed
            twist.angular.x = 0
            twist.angular.y = 0
            twist.angular.z = self.th * self.turn

            self.condition.release()

            # Publish.
            self.publisher.publish(twist)

        # Publish stop message when thread exits.
        twist.linear.x = 0
        twist.linear.y = 0
        twist.linear.z = 0
        twist.angular.x = 0
        twist.angular.y = 0
        twist.angular.z = 0
        self.publisher.publish(twist)


def getKey(key_timeout):
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], key_timeout)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


def vels(speed, turn):
    return "currently:\tspeed %s\tturn %s " % (speed,turn)

if __name__=="__main__":
    settings = termios.tcgetattr(sys.stdin)

    rospy.init_node('teleop_twist_keyboard')

    speed = rospy.get_param("~speed", 0.5)
    turn = rospy.get_param("~turn", 1.0)
    repeat = rospy.get_param("~repeat_rate", 0.0)
    key_timeout = rospy.get_param("~key_timeout", 0.0)
    if key_timeout == 0.0:
        key_timeout = None

    pub_thread = PublishThread(repeat)

    x = 0
    y = 0
    z = 0
    th = 0
    status = 0

    try:
        pub_thread.wait_for_subscribers()
        pub_thread.update(x, y, z, th, speed, turn)

        print(msg)
        print(vels(speed,turn))
        while(1):
            key = getKey(key_timeout)
            if key in moveBindings.keys():
                x = moveBindings[key][0]
                y = moveBindings[key][1]
                z = moveBindings[key][2]
                th = moveBindings[key][3]

            else:
                # Skip updating cmd_vel if key timeout and robot already
                # stopped.
                if key == '' and x == 0 and y == 0 and z == 0 and th == 0:
                    continue
                x = 0
                y = 0
                z = 0
                th = 0
                if (key == '\x03'):
                    break
 
            pub_thread.update(x, y, z, th, speed, turn)

    except Exception as e:
        print(e)

    finally:
        pub_thread.stop()

        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)

