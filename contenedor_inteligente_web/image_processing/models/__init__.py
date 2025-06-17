import os
#from tensorflow.keras.models import load_model
from ultralytics import YOLO

trimmer_model = os.path.join(os.path.dirname(__file__), "yolo11n.pt")
classification_model = os.path.join(os.path.dirname(__file__), "keras_model.h5")


def load_trimmer_model():
    return YOLO(trimmer_model)

#def load_classification_model():
#    return load_model(classification_model)