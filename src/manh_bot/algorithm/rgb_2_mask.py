import os
import numpy as np
from PIL import Image
from tqdm import tqdm

def find_unique_classes_per_image(mask_dir):
    """
    Duyệt qua tất cả các file mask trong thư mục và in ra các lớp duy nhất
    được tìm thấy trong mỗi ảnh.

    Args:
        mask_dir (str): Đường dẫn đến thư mục chứa các file mask.
    """
    mask_files = [f for f in os.listdir(mask_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]

    for filename in tqdm(mask_files, desc="Đang xử lý file mask"):
        mask_path = os.path.join(mask_dir, filename)
        try:
            mask = Image.open(mask_path)
            mask_array = np.array(mask)
            unique_classes = np.unique(mask_array)
            print(f"File: {filename}, Các lớp duy nhất: {sorted(list(unique_classes))}")
        except Exception as e:
            print(f"Lỗi khi đọc file {filename}: {e}")

if __name__ == "__main__":
    mask_directory = '/home/hoangmanh/final_project/data/image'  # Thay đường dẫn này bằng đường dẫn thực tế đến thư mục mask của bạn
    find_unique_classes_per_image(mask_directory)
