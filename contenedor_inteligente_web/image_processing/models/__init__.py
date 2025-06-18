import os
from tensorflow.keras.models import load_model
from ultralytics import YOLO

trimmer_name = "yolo11n.pt"
classification_name = "keras_model.h5"

trimmer_model = os.path.join(os.path.dirname(__file__), os.path.join("trimmer", trimmer_name))
classification_model = os.path.join(os.path.dirname(__file__), os.path.join("classification", classification_name))
labels_txt = os.path.join(os.path.dirname(__file__), os.path.join("classification", "labels.txt"))


def load_trimmer_model():
    return YOLO(trimmer_model)

def load_classification_model():
    return (load_model(classification_model, compile=False), open(labels_txt, "r").readlines())