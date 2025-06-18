import cv2
import torch
from ultralytics import YOLO

# Cargamos el modelo
model = YOLO("yolo11n.pt")

# Elegimos el dispositivo
device = "cuda" if torch.cuda.is_available() else "cpu"

# Captura de cámara (0 = cámara por defecto)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("No se pudo acceder a la cámara")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Hacemos la predicción con YOLO
    results = model.predict(frame, device=device, verbose=False)
    res = results[0]

    # Extraemos cajas, clases y confianza
    boxes = res.boxes.xyxy.cpu().numpy()
    classes = res.boxes.cls.cpu().numpy().astype(int)
    conf = res.boxes.conf.cpu().numpy()
    names = res.names

    # Dibujar los resultados
    for i, (x1, y1, x2, y2) in enumerate(boxes):
        cls = names[classes[i]]
        c = conf[i]
        label = f"{cls} {c:.2f}"
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        cv2.putText(frame, label, (int(x1), int(y1)-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Mostrar el frame con detecciones
    cv2.imshow("YOLOv8 Detection", frame)

    # Salir con tecla 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Liberar recursos
cap.release()
cv2.destroyAllWindows()
