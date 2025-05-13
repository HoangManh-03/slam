#!/usr/bin/env python3

import rospy
import pyrealsense2 as rs
from sensor_msgs.msg import Image, CameraInfo
import tf
from cv_bridge import CvBridge
import numpy as np
import cv2

class RealsensePublisher:
    def __init__(self):
        rospy.init_node('realsense_d435_publisher', anonymous=True)

        # Topics
        self.rgb_topic = rospy.get_param('~rgb_topic', '/camera/color/image_raw')
        self.depth_topic = rospy.get_param('~depth_topic', '/camera/depth/image_rect_raw')
        self.rgb_info_topic = rospy.get_param('~rgb_info_topic', '/camera/color/camera_info')
        self.depth_info_topic = rospy.get_param('~depth_info_topic', '/camera/depth/camera_info')
        self.aligned_depth_topic = rospy.get_param('~aligned_depth_topic', '/camera/aligned_depth_to_color/image_raw')

        # Publishers
        self.rgb_pub = rospy.Publisher(self.rgb_topic, Image, queue_size=10)
        self.depth_pub = rospy.Publisher(self.depth_topic, Image, queue_size=10)
        self.rgb_info_pub = rospy.Publisher(self.rgb_info_topic, CameraInfo, queue_size=10)
        self.depth_info_pub = rospy.Publisher(self.depth_info_topic, CameraInfo, queue_size=10)
        self.aligned_depth_pub = rospy.Publisher(self.aligned_depth_topic, Image, queue_size=10)

        # RealSense
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        self.config.enable_stream(rs.stream.depth, 848, 480, rs.format.z16, 30)
        self.align = rs.align(rs.stream.color)

        self.bridge = CvBridge()
        self.broadcaster = tf.TransformBroadcaster()

        # Camera Info
        self.rgb_info = CameraInfo(
            width=640, height=480,
            K=[615.8276977539062, 0.0, 321.8806457519531,
               0.0, 615.6688232421875, 240.3068389892578,
               0.0, 0.0, 1.0],
            P=[615.8276977539062, 0.0, 321.8806457519531, 0.0,
               0.0, 615.6688232421875, 240.3068389892578, 0.0,
               0.0, 0.0, 1.0, 0.0],
            D=[0.0, 0.0, 0.0, 0.0, 0.0],
            distortion_model='plumb_bob'
        )
        self.rgb_info.header.frame_id = "camera_color_optical_frame"

        self.depth_info = CameraInfo(
            width=848, height=480,
            K=[424.46441650390625, 0.0, 423.5723571777344,
               0.0, 424.46441650390625, 239.52735900878906,
               0.0, 0.0, 1.0],
            P=[424.46441650390625, 0.0, 423.5723571777344, 0.0,
               0.0, 424.46441650390625, 239.52735900878906, 0.0,
               0.0, 0.0, 1.0, 0.0],
            D=[0.0, 0.0, 0.0, 0.0, 0.0],
            distortion_model='plumb_bob'
        )
        self.depth_info.header.frame_id = "camera_depth_optical_frame"

        try:
            self.pipeline.start(self.config)
            rospy.loginfo("Realsense D435 camera started.")
        except rs.error as e:
            rospy.logerr(f"Failed to start Realsense: {e}")
            rospy.signal_shutdown("Camera error")

    def publish_transforms(self):
        now = rospy.Time.now()

        # Publish static transform camera_link → camera_color_frame (no rotation)
        self.broadcaster.sendTransform(
            (0, 0, 0),
            (0, 0, 0, 1),
            now,
            "camera_color_frame",
            "camera_link"
        )

        # Publish static transform camera_color_frame → camera_color_optical_frame (rotate -90 deg X, -90 deg Z)
        quat_optical = tf.transformations.quaternion_from_euler(-np.pi/2, 0, -np.pi/2)
        self.broadcaster.sendTransform(
            (0, 0, 0),
            quat_optical,
            now,
            "camera_color_optical_frame",
            "camera_color_frame"
        )

        # Publish static transform camera_link → camera_depth_frame
        self.broadcaster.sendTransform(
            (0, 0, 0),
            (0, 0, 0, 1),
            now,
            "camera_depth_frame",
            "camera_link"
        )

        # Publish static transform camera_depth_frame → camera_depth_optical_frame
        self.broadcaster.sendTransform(
            (0, 0, 0),
            quat_optical,
            now,
            "camera_depth_optical_frame",
            "camera_depth_frame"
        )

    def publish_data(self):
        frames = self.pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        depth_frame = frames.get_depth_frame()
        aligned_frames = self.align.process(frames)
        aligned_depth_frame = aligned_frames.get_depth_frame()

        if not color_frame or not depth_frame:
            return

        now = rospy.Time.now()

        # Color image
        color_image = np.asanyarray(color_frame.get_data())
        rgb_msg = self.bridge.cv2_to_imgmsg(color_image, encoding="bgr8")
        rgb_msg.header.stamp = now
        rgb_msg.header.frame_id = "camera_color_optical_frame"
        self.rgb_pub.publish(rgb_msg)

        # Depth image
        depth_image = np.asanyarray(depth_frame.get_data())
        depth_msg = self.bridge.cv2_to_imgmsg(depth_image, encoding="16UC1")
        depth_msg.header.stamp = now
        depth_msg.header.frame_id = "camera_depth_optical_frame"
        self.depth_pub.publish(depth_msg)

        # Aligned depth
        aligned_depth_image = np.asanyarray(aligned_depth_frame.get_data())
        aligned_depth_msg = self.bridge.cv2_to_imgmsg(aligned_depth_image, encoding="16UC1")
        aligned_depth_msg.header.stamp = now
        aligned_depth_msg.header.frame_id = "camera_color_optical_frame"
        self.aligned_depth_pub.publish(aligned_depth_msg)

        # Camera Info
        self.rgb_info.header.stamp = now
        self.rgb_info_pub.publish(self.rgb_info)

        self.depth_info.header.stamp = now
        self.depth_info_pub.publish(self.depth_info)

        # Publish TFs
        self.publish_transforms()

    def run(self):
        rate = rospy.Rate(10)
        while not rospy.is_shutdown():
            self.publish_data()
            rate.sleep()

    def on_shutdown(self):
        rospy.loginfo("Shutting down Realsense Publisher.")
        self.pipeline.stop()

if __name__ == '__main__':
    try:
        publisher = RealsensePublisher()
        rospy.on_shutdown(publisher.on_shutdown)
        publisher.run()
    except rospy.ROSInterruptException:
        pass
