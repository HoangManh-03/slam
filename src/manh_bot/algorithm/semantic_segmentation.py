import torch
import torchvision.transforms as T
import torchvision.models.segmentation as segmentation
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import cv2

# Tải mô hình DeepLabV3 với MobileNetV3 Large backbone đã được huấn luyện trước trên COCO
model = segmentation.deeplabv3_mobilenet_v3_large(pretrained=True).eval()

# Các lớp COCO (91 lớp, bao gồm background)
COCO_CLASSES = [
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

# Các màu tương ứng cho mỗi lớp
def get_coco_palette(num_cls):
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

coco_palette = get_coco_palette(len(COCO_CLASSES))

# Hàm để tiền xử lý ảnh
def preprocess_image(image_path):
    img = Image.open(image_path).convert('RGB')
    transform = T.Compose([
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    input_tensor = transform(img).unsqueeze(0)
    return input_tensor, np.array(img)

# Hàm để thực hiện semantic segmentation và hiển thị kết quả overlay
def segment_and_overlay(model, input_tensor, original_image_np, classes, palette):
    with torch.no_grad():
        output = model(input_tensor)['out'][0].cpu()
    output_predictions = torch.argmax(output, dim=0).byte().numpy()

    # Tạo mask màu
    colored_mask = Image.fromarray(output_predictions.astype(np.uint8)).convert('P')
    colored_mask.putpalette(palette)
    colored_mask = np.array(colored_mask.convert('RGB'))

    # Resize mask cho khớp với kích thước ảnh gốc
    resized_mask = cv2.resize(colored_mask, (original_image_np.shape[1], original_image_np.shape[0]), interpolation=cv2.INTER_LINEAR)

    # Tạo overlay
    alpha = 0.5
    overlayed_image = cv2.addWeighted(original_image_np, 1 - alpha, resized_mask, alpha, 0)
    overlayed_image_rgb = cv2.cvtColor(overlayed_image, cv2.COLOR_BGR2RGB)

    # Hiển thị ảnh gốc và ảnh đã overlay
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    plt.imshow(original_image_np)
    plt.title('Original Image')
    plt.axis('off')

    plt.subplot(1, 2, 2)
    plt.imshow(overlayed_image_rgb)
    plt.title('Image with Mask Overlay')
    plt.axis('off')

    plt.tight_layout()
    plt.show()

    # In các lớp được phát hiện (chỉ các lớp không phải background)
    unique_classes = np.unique(output_predictions)
    present_classes = [classes[i] for i in unique_classes if i != 0 and i < len(classes)]
    return output_predictions, present_classes

if __name__ == '__main__':
    image_path = '/home/hoangmanh/Desktop/living_room.jpg' # Thay thế bằng đường dẫn ảnh trong nhà của bạn
    input_tensor, original_image_np = preprocess_image(image_path)
    segmentation_mask, present_classes = segment_and_overlay(model, input_tensor, original_image_np, COCO_CLASSES, coco_palette)
    print("Các lớp ngữ nghĩa được phát hiện:", present_classes)