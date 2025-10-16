import os
from tensorflow.keras.models import load_model
from ultralytics import YOLO
from tensorflow.keras.applications.efficientnet_v2 import preprocess_input

trimmer_name = "best.pt"

trimmer_model = os.path.join(os.path.dirname(__file__), os.path.join("trimmer", trimmer_name))
labels_txt = os.path.join(os.path.dirname(__file__), os.path.join("classification", "labels.txt"))


def load_trimmer_model():
    return YOLO(trimmer_model)

"""
def load_classification_model():
    # MODIFIED: Define the custom_objects dictionary and pass it to load_model
    custom_objects = {'preprocess_input': preprocess_input}
    model = load_model(
        classification_model, 
        custom_objects=custom_objects, 
        compile=False
    )
    
    with open(labels_txt, "r") as f:
        class_names = f.readlines()
        
    return (model, class_names)
"""