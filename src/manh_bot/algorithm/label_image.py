import os
import torch
import torchvision
from torchvision import transforms
from torchvision.models.segmentation import DeepLabV3_ResNet101_Weights
import numpy as np
import cv2
from PIL import Image
from tqdm import tqdm

# Load mô hình DeepLabV3 với trọng số COCO
weights = DeepLabV3_ResNet101_Weights.DEFAULT
model = torchvision.models.segmentation.deeplabv3_resnet101(weights=weights).eval()

# Hàm tiền xử lý ảnh
transform = weights.transforms()

# Đường dẫn thư mục
input_folder = '/home/hoangmanh/final_project/data/img'
output_mask_folder = '/home/hoangmanh/final_project/data/annotated_image'
output_overlay_folder = '/home/hoangmanh/final_project/data/annotated_image/overlay_image'

# Tạo thư mục nếu chưa tồn tại
os.makedirs(output_mask_folder, exist_ok=True)
os.makedirs(output_overlay_folder, exist_ok=True)

# Lớp "người" trong mô hình COCO: class ID = 15
person_class = 15

# Duyệt các ảnh trong thư mục
for filename in tqdm(os.listdir(input_folder)):
    if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        # Load ảnh gốc
        image_path = os.path.join(input_folder, filename)
        image = Image.open(image_path).convert("RGB")
        image_np = np.array(image)

        # Tiền xử lý và đưa vào model
        input_tensor = transform(image).unsqueeze(0)
        with torch.no_grad():
            output = model(input_tensor)['out'][0]
            predictions = output.argmax(0).cpu().numpy()

        # Tạo mask nhị phân cho lớp người
        binary_mask = (predictions == person_class).astype(np.uint8)

        # Resize mask về kích thước ảnh gốc
        binary_mask = cv2.resize(binary_mask, (image_np.shape[1], image_np.shape[0]), interpolation=cv2.INTER_NEAREST)

        # Tạo ảnh overlay có màu
        mask_color = np.zeros((*binary_mask.shape, 3), dtype=np.uint8)
        mask_color[binary_mask == 1] = [0, 255, 0]
        overlay = cv2.addWeighted(image_np, 0.7, mask_color, 0.3, 0)

        # Tên file xuất ra
        name_wo_ext = os.path.splitext(filename)[0]
        mask_output_path = os.path.join(output_mask_folder, f"{name_wo_ext}_mask.png")
        overlay_output_path = os.path.join(output_overlay_folder, f"{name_wo_ext}_overlay.png")

        # Lưu kết quả
        cv2.imwrite(mask_output_path, binary_mask * 255)
        cv2.imwrite(overlay_output_path, cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))
