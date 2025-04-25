#!/usr/bin/env python

import rospy
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import numpy as np
import cv2
import queue
import time
from math import inf

class PIDController:
    def __init__(self, kP, kI, kD, kS):
        self.kP = kP
        self.kI = kI
        self.kD = kD
        self.kS = kS
        self.err_int = 0
        self.err_dif = 0
        self.err_prev = 0
        self.err_hist = queue.Queue(self.kS)
        self.t_prev = time.time()

    def control(self, err, t):
        dt = t - self.t_prev
        if dt > 0.0:
            self.err_hist.put(err)
            self.err_int += err
            if self.err_hist.full():
                self.err_int -= self.err_hist.get()
            self.err_dif = (err - self.err_prev)
            u = (self.kP * err) + (self.kI * self.err_int * dt) + (self.kD * self.err_dif / dt)
            self.err_prev = err
            self.t_prev = t
            return u

class RobotController:
    def __init__(self):
        rospy.init_node('robot_controller', anonymous=True)
        self.bridge = CvBridge()
        self.depth_image = None
        self.ctrl_msg = Twist()
        self.start_time = time.time()
        self.safe_distance = 0.6
        self.turning = False
        self.turning_time = None

        self.pid_lat = PIDController(0.6, 0.01, 1.2, 10)
        self.pid_lon = PIDController(0.1, 0.001, 0.05, 10)

        self.sub = rospy.Subscriber('/camera/color/image_raw', Image, self.image_callback)
        self.pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        self.timer = rospy.Timer(rospy.Duration(0.01), self.robot_controller_callback)

    def image_callback(self, msg):
        try:
            self.depth_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="passthrough")
        except Exception as e:
            rospy.logerr("Error processing image: %s" % str(e))

    def get_distance(self, image, angle_range):
        h, w = image.shape
        center_y = h // 2
        x_start, x_end = int(w * angle_range[0]), int(w * angle_range[1])
        depth_values = image[center_y, x_start:x_end]
        depth_values = depth_values[~np.isnan(depth_values)]
        return np.mean(depth_values) if len(depth_values) > 0 else float('inf')

    def robot_controller_callback(self, event):
        DELAY = 4.0
        if time.time() - self.start_time > DELAY:
            if self.depth_image is None:
                return

            left_distance = self.get_distance(self.depth_image, (0.0, 0.3))
            right_distance = self.get_distance(self.depth_image, (0.7, 1.0))
            front_distance = self.get_distance(self.depth_image, (0.45, 0.55))
            cte = left_distance - right_distance

            if abs(cte) < 0.01:
                cte = 0
            tstamp = time.time()

            if self.turning:
                TURNING_TIME = 3
                if time.time() - self.turning_time > TURNING_TIME:
                    self.turning = False
            else:
                if front_distance > 0.3 and cte == 0:
                    LIN_VEL = 0.3
                    ANG_VEL = 0.0
                elif front_distance < 0.3:
                    LIN_VEL = 0.0
                    ANG_VEL = -0.5
                    self.turning = True
                    self.turning_time = time.time()
                elif left_distance < self.safe_distance and front_distance > 0.3:
                    LIN_VEL = 0.2
                    ANG_VEL = -0.1
                elif left_distance > self.safe_distance and front_distance > 0.3:
                    LIN_VEL = 0.2
                    ANG_VEL = 0.1

                self.ctrl_msg.linear.x = LIN_VEL
                self.ctrl_msg.angular.z = ANG_VEL
                self.pub.publish(self.ctrl_msg)

            rospy.loginfo("CTE: %.4f | Left: %.2f | Right: %.2f | Front: %.2f" % (cte, left_distance, right_distance, front_distance))
        else:
            rospy.loginfo("Initializing...")

if __name__ == '__main__':
    try:
        RobotController()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
