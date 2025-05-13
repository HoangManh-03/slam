#!/usr/bin/env python
import rospy
import message_filters
import numpy as np
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
from image_geometry import PinholeCameraModel

class PixelTo3DNode:
    def __init__(self):
        rospy.init_node('pixel_to_3d_node')
        self.bridge = CvBridge()
        self.cam_model = PinholeCameraModel()

        # Subscribing to camera info and depth image
        info_sub = message_filters.Subscriber("/camera/depth/camera_info", CameraInfo)
        depth_sub = message_filters.Subscriber("/camera/aligned_depth_to_color/image_raw", Image)
        ts = message_filters.ApproximateTimeSynchronizer([info_sub, depth_sub], 10, 0.1)
        ts.registerCallback(self.callback)

        rospy.loginfo("Pixel to 3D node started.")
        rospy.spin()

    def callback(self, cam_info, depth_img):
        self.cam_model.fromCameraInfo(cam_info)
        cv_depth = self.bridge.imgmsg_to_cv2(depth_img, desired_encoding="passthrough")

        # Chọn một pixel cụ thể (ví dụ giữa ảnh)
        u, v = int(cv_depth.shape[1]/2), int(cv_depth.shape[0]/2)
        depth = cv_depth[v, u] * 0.001  # Convert mm to meters if necessary

        if depth == 0:
            rospy.logwarn("No depth data at selected pixel.")
            return

        ray = self.cam_model.projectPixelTo3dRay((u, v))  # đơn vị hướng
        point_3d = [depth * r for r in ray]

        rospy.loginfo("Pixel (%d, %d) --> 3D Position: [%.3f, %.3f, %.3f] (meters)", u, v, *point_3d)

if __name__ == '__main__':
    try:
        PixelTo3DNode()
    except rospy.ROSInterruptException:
        pass
