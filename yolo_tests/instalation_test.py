import torch
from ultralytics import YOLO
import torch


print(torch.cuda.is_available())   # debe ser True si usas GPU
print(torch.version.cuda)          
print(torch.cuda.get_device_name(0))

device = "cuda" if torch.cuda.is_available() else "cpu"

model = YOLO("yolo11n.pt")
results = model.predict(source='dog.png', device=device)
print(results)
