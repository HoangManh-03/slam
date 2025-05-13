import os
import torch
import torchvision
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from PIL import Image

# ======================= CONFIG =======================
NUM_CLASSES = 2  # sửa lại số class nếu khác
NUM_EPOCHS = 25
BATCH_SIZE = 4
LEARNING_RATE = 1e-4
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

IMAGE_DIR = '/home/hoangmanh/final_project//data/image'  # Thư mục chứa ảnh RGB
MASK_DIR = '/home/hoangmanh/final_project/data/annotated_image'    # Thư mục chứa mask (1 channel, giá trị pixel là class index)

# ==================== CUSTOM DATASET ====================
class SegmentationDataset(Dataset):
    def __init__(self, image_dir, mask_dir, transform=None, target_transform=None):
        self.image_dir = image_dir
        self.mask_dir = mask_dir
        self.images = sorted(os.listdir(image_dir))
        self.transform = transform
        self.target_transform = target_transform

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img_path = os.path.join(self.image_dir, self.images[idx])
        mask_path = os.path.join(self.mask_dir, self.images[idx].replace(".jpg", ".png"))

        image = Image.open(img_path).convert("RGB")
        mask = Image.open(mask_path).convert("L")

        if self.transform:
            image = self.transform(image)
        if self.target_transform:
            mask = self.target_transform(mask)

        mask = mask.squeeze().long()  # 1xHxW -> HxW
        return image, mask

# ==================== TRANSFORMS ====================
image_transform = transforms.Compose([
    transforms.Resize((480, 640)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

mask_transform = transforms.Compose([
    transforms.Resize((480, 640), interpolation=Image.NEAREST),
    transforms.PILToTensor()
])

# ==================== DATA LOADER ====================
dataset = SegmentationDataset(IMAGE_DIR, MASK_DIR, image_transform, mask_transform)
dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

# ==================== MODEL + LOSS ====================
model = torchvision.models.segmentation.fcn_resnet18(weights=None)
model.classifier[4] = nn.Conv2d(512, NUM_CLASSES, kernel_size=1)  # Sửa lại lớp cuối


criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

# ==================== TRAIN LOOP ====================
for epoch in range(NUM_EPOCHS):
    model.train()
    total_loss = 0

    for images, masks in dataloader:
        images, masks = images.to(DEVICE), masks.to(DEVICE)

        outputs = model(images)['out']
        loss = criterion(outputs, masks)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    avg_loss = total_loss / len(dataloader)
    print(f"Epoch [{epoch+1}/{NUM_EPOCHS}] - Loss: {avg_loss:.4f}")

# ==================== SAVE MODEL ====================
torch.save(model.state_dict(), "fcn_resnet18_custom.pth")
print("Model saved to fcn_resnet18_custom.pth")
