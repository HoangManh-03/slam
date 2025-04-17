import torch
import torchvision.transforms as T
import torchvision
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import random

# Chọn một mô hình semantic segmentation tiền huấn luyện (ví dụ: DeepLabV3 với backbone ResNet101)
model = torchvision.models.segmentation.fcn_resnet101(pretrained=True).eval()

# Các lớp ngữ nghĩa (COCO Stuff 164 classes)
# Bạn có thể tùy chỉnh danh sách này nếu mô hình bạn chọn khác
CLASSES = [
    'background', 'aeroplane', 'bicycle', 'bird', 'boat', 'bottle', 'bus', 'car', 'cat', 'chair', 'cow',
    'diningtable', 'dog', 'horse', 'motorbike', 'person', 'pottedplant', 'sheep', 'sofa', 'train', 'tvmonitor'
]

# Hàm để tiền xử lý ảnh
def preprocess_image(image_path):
    img = Image.open(image_path).convert('RGB')
    transform = T.Compose([
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    input_tensor = transform(img).unsqueeze(0)
    return input_tensor, img

# Hàm để thực hiện semantic segmentation và hiển thị kết quả
def segment_image(input_tensor, original_image):
    with torch.no_grad():
        output = model(input_tensor)['out'][0]
    output_predictions = output.argmax(0)

    # Tạo mask màu cho các lớp
    segmentation_mask = output_predictions.byte().cpu().numpy()
    n_classes = len(CLASSES)
    cmap = plt.cm.get_cmap('tab20', n_classes)
    colored_mask = cmap(segmentation_mask)

    # Hiển thị ảnh gốc và mask
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    plt.imshow(original_image)
    plt.title('Original Image')
    plt.axis('off')

    plt.subplot(1, 2, 2)
    plt.imshow(colored_mask)
    plt.title('Semantic Segmentation Mask')
    plt.axis('off')

    plt.tight_layout()
    plt.show()

    # Trả về mask và danh sách các lớp hiện diện
    unique_classes = np.unique(segmentation_mask)
    present_classes = [CLASSES[i] for i in unique_classes if i != 0] # Loại bỏ background
    return segmentation_mask, present_classes

if __name__ == '__main__':
    image_path = '/home/hoangmanh/Desktop/city.jpg' # Thay thế bằng đường dẫn ảnh của bạn
    input_tensor, original_image = preprocess_image(image_path)
    segmentation_mask, present_classes = segment_image(input_tensor,  original_image)
    print("Các lớp ngữ nghĩa được phát hiện:", present_classes)