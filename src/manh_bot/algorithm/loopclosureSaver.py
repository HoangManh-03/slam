import rospy
from sensor_msgs.msg import Image
from sensor_msgs.msg import CompressedImage  # Có thể cần nếu rtabmap publish ảnh compressed
from rtabmap_msgs.msg import Info, RGBDImage
from cv_bridge import CvBridge
import cv2
import os

class LoopClosureImageSaver:
    def __init__(self):
        rospy.init_node('loop_closure_image_saver')

        self.bridge = CvBridge()
        self.latest_image = None
        self.loop_closure_detected = False
        self.image_sub = rospy.Subscriber('/rtabmap/rgbd_image', RGBDImage, self.rgbd_image_callback)        
        # Hoặc nếu rtabmap publish ảnh compressed:
        #self.image_sub = rospy.Subscriber('/rtabmap/rgbd_image/compressed', CompressedImage, self.compressed_image_callback)

        self.info_sub = rospy.Subscriber('/rtabmap/info', Info, self.info_callback)

        self.save_dir = '/home/hoangmanh/final_project/slam/src/manh_bot/algorithm/loopclosure_saver'  # Thư mục để lưu ảnh
        os.makedirs(self.save_dir, exist_ok=True)

        rospy.spin()

    def rgbd_image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg.rgb, "bgr8")  # Truy cập trường ảnh rgb
            self.latest_image = cv_image
        except Exception as e:
            rospy.logerr(f"Error converting RGB image from RGBDImage: {e}")

        if self.loop_closure_detected and self.latest_image is not None:
            self.save_loop_closure_image()
            self.loop_closure_detected = False # Reset flag

    def compressed_image_callback(self, msg):
        try:
            np_arr = np.frombuffer(msg.data, np.uint8)
            cv_image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            self.latest_image = cv_image
        except Exception as e:
            rospy.logerr(f"Error converting compressed image: {e}")

        if self.loop_closure_detected and self.latest_image is not None:
            self.save_loop_closure_image()
            self.loop_closure_detected = False # Reset flag

    def info_callback(self, msg):
        if msg.loopClosureId > 0:
            rospy.loginfo(f"Loop Closure Detected (ID: {msg.loopClosureId}), saving processed image...")
            self.loop_closure_detected = True

    def save_loop_closure_image(self):
        if self.latest_image is not None:
            timestamp = rospy.Time.now().to_sec()
            filename = os.path.join(self.save_dir, f"loop_closure_processed_{timestamp}.png")
            cv2.imwrite(filename, self.latest_image)
            rospy.loginfo(f"Saved processed loop closure image to: {filename}")
        else:
            rospy.warn("No processed image received before loop closure detection.")

if __name__ == '__main__':
    try:
        LoopClosureImageSaver()
    except rospy.ROSInterruptException:
        pass