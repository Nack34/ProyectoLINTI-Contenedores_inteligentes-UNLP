from .models import load_trimmer_model
import torch
import cv2
import os

model = load_trimmer_model()
device = "cuda" if torch.cuda.is_available() else "cpu"

def recortar_img(filename, dir_img_processed):
    results = model.predict(source=filename, device=device)

    # Tomamos el primer resultado (una sola imagen procesada)
    res = results[0]

    # Obtenemos coordenadas, clases y confianza
    boxes = res.boxes.xyxy.cpu().numpy()
    classes = res.boxes.cls.cpu().numpy().astype(int)
    conf = res.boxes.conf.cpu().numpy()
    names = res.names

    img = res.orig_img  # numpy array BGR o RGB según versión

    for i, (x1, y1, x2, y2) in enumerate(boxes):
        cls = names[classes[i]]  # ej. "dog"
        c = conf[i] # Confianza
        crop = img[int(y1):int(y2), int(x1):int(x2)]
        cv2.imwrite(f'{dir_img_processed}/objeto_{i}.jpg', crop)
