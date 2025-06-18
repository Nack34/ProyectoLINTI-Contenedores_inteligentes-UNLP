from .models import load_classification_model
import torch
import numpy as np
from tensorflow.keras.preprocessing import image
from PIL import Image, ImageOps  
import os

model, class_names = load_classification_model()
device = "cuda" if torch.cuda.is_available() else "cpu"

def clasificar_img(filename, output_dir):
    # 1. Cargar y preprocesar imagen

    # Crear un array con batch=1 y las demás dimensiones del input
    input_shape = model.input_shape[1:]  # (224, 224, 3)
    data = np.ndarray(shape=(1, *input_shape), dtype=np.float32)
    # resizing the image to be at least 224x224 and then cropping from the center
    image = Image.open(filename).convert("RGB")
    size = (224, 224)
    image = ImageOps.fit(image, size, Image.Resampling.LANCZOS)
    # turn the image into a numpy array
    image_array = np.asarray(image)
    # Normalize the image
    normalized_image_array = (image_array.astype(np.float32) / 127.5) - 1
    # Load the image into the array
    data[0] = normalized_image_array

    # 2. Predicts the model
    prediction = model.predict(data)
    index = np.argmax(prediction)

    # 3. Interpretar resultado (obtener clase)
    class_name = class_names[index]
    confidence_score = prediction[0][index]

    # 4. Guardar resultado en archivo
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "prediccion.txt")

    with open(output_path, "a") as f:
        f.write(f"{class_name.strip()} {confidence_score:.4f}\n")

    return (class_name, confidence_score)









    
