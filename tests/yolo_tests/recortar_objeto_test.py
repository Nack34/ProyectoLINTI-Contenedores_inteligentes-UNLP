from ultralytics import YOLO
import torch
import cv2
import os

model = YOLO("yolo11n.pt")
device = "cuda" if torch.cuda.is_available() else "cpu"

#results = model.predict(source='dog.png', device=device)
results = model.predict(source='cats.png', device=device)

# Tomamos el primer resultado (una sola imagen procesada)
res = results[0]

# Obtenemos coordenadas, clases y confianza
boxes = res.boxes.xyxy.cpu().numpy()
classes = res.boxes.cls.cpu().numpy().astype(int)
conf = res.boxes.conf.cpu().numpy()
names = res.names

img = res.orig_img  # numpy array BGR o RGB según versión

os.makedirs("results", exist_ok=True)

for i, (x1, y1, x2, y2) in enumerate(boxes):
    cls = names[classes[i]]  # ej. "dog"
    c = conf[i]
    crop = img[int(y1):int(y2), int(x1):int(x2)]
    cv2.imwrite(f'results/{cls}_{i}_{c:.2f}.jpg', crop)
