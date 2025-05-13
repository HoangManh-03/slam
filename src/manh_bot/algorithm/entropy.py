import cv2
import numpy as np
import matplotlib.pyplot as plt

# Đọc ảnh PGM
img = cv2.imread("/home/hoangmanh/final_project/map/map1/map.pgm", cv2.IMREAD_UNCHANGED)

# Chuyển sang ảnh màu để đánh dấu
color_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

# Pixel không rõ ràng là giá trị 89
uncertain_mask = (img == 89)

# Đánh dấu màu đỏ các pixel không rõ ràng
color_img[uncertain_mask] = [0, 0, 255]  # BGR: Red

# Hiển thị ảnh
plt.figure(figsize=(8, 8))
plt.imshow(cv2.cvtColor(color_img, cv2.COLOR_BGR2RGB))
plt.title("Uncertain Pixels (value 89) in Red")
plt.axis('off')
plt.show()


