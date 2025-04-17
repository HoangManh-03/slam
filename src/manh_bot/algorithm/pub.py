#!/usr/bin/env python

import rospy
from std_msgs.msg import Float32MultiArray

def talker():
    # pub = rospy.Publisher('pwm_commands', Float32MultiArray, queue_size=10)
    pub = rospy.Publisher('reader', Float32MultiArray, queue_size=10)
    rospy.init_node('pwm_publisher', anonymous=True)
    rate = rospy.Rate(0.5)  # Publish rate (Hz)

    while not rospy.is_shutdown():
        # Thay thế các giá trị này bằng logic điều khiển PWM của bạn
        pwm_left_value = -100  # Ví dụ giá trị PWM cho encoder trái
        pwm_right_value = -100 # Ví dụ giá trị PWM cho encoder phải

        pwm_msg = Float32MultiArray()
        pwm_msg.data = [pwm_left_value, pwm_right_value]

        rospy.loginfo(f"Publishing PWM: Left={pwm_left_value}, Right={pwm_right_value}")
        pub.publish(pwm_msg)
        rate.sleep()

if __name__ == '__main__':
    try:
        talker()
    except rospy.ROSInterruptException:
        pass