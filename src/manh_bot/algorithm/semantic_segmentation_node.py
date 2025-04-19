#!/usr/bin/env python3

import rospy
import torch
import torchvision.transforms as T
import torchvision.models.segmentation as segmentation
from sensor_msgs.msg import Image as ROSImage  # Alias cho message ROS Image
from PIL import Image as PILImage      # Alias cho PIL Image
from cv_bridge import CvBridge
import cv2
import numpy as np
import matplotlib.pyplot as plt  # Chỉ dùng để tạo colormap

class SemanticSegmentationNode:
    def __init__(self):
        rospy.init_node('semantic_segmentation_node')
        self.image_sub = rospy.Subscriber('/camera/color/image_raw', ROSImage, self.image_callback)
        self.segmentation_pub = rospy.Publisher('/semantic_segmentation/image', ROSImage, queue_size=1)
        self.bridge = CvBridge()
        self.model = segmentation.deeplabv3_mobilenet_v3_large(pretrained=True).eval().to(self.get_device())
        self.coco_classes = [
            '__background__', 'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
            'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep',
            'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
            'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard',
            'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich',
            'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed',
            'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven',
            'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
            'toothbrush'
        ]
        self.coco_palette = self.get_coco_palette(len(self.coco_classes))
        rospy.loginfo("Semantic Segmentation Node initialized.")

    def get_device(self):
        if torch.cuda.is_available():
            return torch.device('cuda')
        else:
            return torch.device('cpu')

    def get_coco_palette(self, num_cls):
        n = num_cls
        palette = [0] * (n * 3)
        for j in range(0, n):
            lab = j
            palette[j * 3 + 0] = 0
            palette[j * 3 + 1] = 0
            palette[j * 3 + 2] = 0
            i = 0
            while lab > 0:
                palette[j * 3 + 0] |= (((lab >> 0) & 1) << (7 - i))
                palette[j * 3 + 1] |= (((lab >> 1) & 1) << (7 - i))
                palette[j * 3 + 2] |= (((lab >> 2) & 1) << (7 - i))
                i += 1
                lab >>= 3
        return palette


    def preprocess_image(self, cv_image):
        img = PILImage.fromarray(cv_image).convert('RGB')
        transform = T.Compose([
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        input_tensor = transform(img).unsqueeze(0).to(next(self.model.parameters()).device)
        return input_tensor
    def segment_image(self, input_tensor, original_image_np):
        with torch.no_grad():
            output = self.model(input_tensor)['out'][0].cpu()
        output_predictions = torch.argmax(output, dim=0).byte().numpy()

        colored_mask = PILImage.fromarray(output_predictions.astype(np.uint8)).convert('P') # Sử dụng PILImage
        colored_mask.putpalette(self.coco_palette)
        colored_mask = np.array(colored_mask.convert('RGB'))

        resized_mask = cv2.resize(colored_mask, (original_image_np.shape[1], original_image_np.shape[0]), interpolation=cv2.INTER_LINEAR)
        alpha = 0.5
        overlayed_image = cv2.addWeighted(original_image_np, 1 - alpha, resized_mask, alpha, 0).astype(np.uint8)
        return overlayed_image, output_predictions

    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except CvBridgeError as e:
            rospy.logerr(f"CvBridge error: {e}")
            return

        input_tensor = self.preprocess_image(cv_image)
        overlayed_image, segmentation_mask = self.segment_image(input_tensor, cv_image)

        try:
            mask_msg = self.bridge.cv2_to_imgmsg(overlayed_image, encoding="rgb8")
            mask_msg.header = msg.header
            self.segmentation_pub.publish(mask_msg)
            unique_classes = np.unique(segmentation_mask)
            present_classes = [self.coco_classes[i] for i in unique_classes if i != 0 and i < len(self.coco_classes)]
            rospy.loginfo(f"Detected classes: {present_classes}")
        except CvBridgeError as e:
            rospy.logerr(f"CvBridge error: {e}")

if __name__ == '__main__':
    try:
        segmentation_node = SemanticSegmentationNode()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass