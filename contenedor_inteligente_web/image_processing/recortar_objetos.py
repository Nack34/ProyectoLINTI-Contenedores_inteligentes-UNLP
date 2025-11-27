from .models import load_trimmer_model
import torch
import cv2
import os
import threading

model = None
model_loaded = threading.Event()
inference_lock = threading.Lock()  # <--- NEW: Lock to prevent crashes

def load_model_in_background():
    global model
    model = load_trimmer_model()
    model_loaded.set()

threading.Thread(target=load_model_in_background, daemon=True).start()

device = "cuda" if torch.cuda.is_available() else "cpu"

def recortar_img(filename, dir_img_processed):
    model_loaded.wait()
    # Protect inference with lock
    with inference_lock:
        results = model.predict(source=filename, device=device, show_labels=False, show_conf=False, show_boxes=False)

    # Tomamos el primer resultado (una sola imagen procesada)
    res = results[0]

    # Obtenemos coordenadas, clases y confianza
    boxes = res.boxes.xyxy.cpu().numpy()
    classes = res.boxes.cls.cpu().numpy().astype(int)
    conf = res.boxes.conf.cpu().numpy()
    names = res.names

    img = res.orig_img

    for i, (x1, y1, x2, y2) in enumerate(boxes):
        cls = names[classes[i]]
        c = conf[i]
        crop = img[int(y1):int(y2), int(x1):int(x2)]
        cv2.imwrite(f'{dir_img_processed}/objeto_{i}.jpg', crop)

def recortar_img_from_frame(img):
    model_loaded.wait()
    
    # NEW: Lock the model during prediction to prevent segmentation faults
    with inference_lock:
        results = model.predict(source=img, device=device)

    # Take first result (single image)
    res = results[0]

    # Extract bounding boxes, classes, confidence, names
    boxes = res.boxes.xyxy.cpu().numpy()       # shape (N,4): x1,y1,x2,y2
    classes = res.boxes.cls.cpu().numpy().astype(int)
    conf = res.boxes.conf.cpu().numpy()
    names = res.names

    crops = []
    for i, (x1, y1, x2, y2) in enumerate(boxes):
        cls_name = names[classes[i]]
        confidence = conf[i]
        # Crop the image array, ensure indices are int and within bounds
        crop_img = img[int(y1):int(y2), int(x1):int(x2)]
        crops.append({
            'bbox': (int(x1), int(y1), int(x2 - x1), int(y2 - y1)),
            'class_name': cls_name,
            'confidence': confidence,
            'crop_img': crop_img
        })
    return crops