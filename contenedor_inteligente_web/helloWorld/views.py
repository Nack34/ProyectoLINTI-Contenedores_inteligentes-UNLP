import io
import threading
import time

import cv2
import qrcode
import serial
import json
import serial.tools.list_ports as list_ports
from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import render
from api.models import Residuo, TipoResiduo
from django.core.signing import Signer

# from image_processing.clasificar_objetos import clasificar_img_from_array
from image_processing.recortar_objetos import recortar_img_from_frame

camera_w = 640
camera_h = 480
centro_camara = (camera_w / 2, camera_h / 2)

# Colores para las detecciones de cada clase
COLOR_MAP = {
    'TRASH': (0, 0, 255),        # Rojo
    'CARDBOARD': (42, 128, 244), # Naranja
    'GLASS': (0, 255, 0),        # Verde
    'METAL': (128, 0, 128),      # Violeta 
    'PAPER': (240, 240, 0),      # Cian
    'PLASTIC': (255, 0, 0)       # Azul
}

# Traducción de las clases del modelo
LABEL_TRANSLATIONS = {
    "CARDBOARD": "Carton",
    "GLASS": "Vidrio",
    "METAL": "Metal",
    "PAPER": "Papel",
    "PLASTIC": "Plastico",
    "TRASH": "Basura"
}

# Traducción de las clases a los LED
CLASS_TO_LED = {
    "Carton": 1,
    "Metal": 2,
    "Papel": 3,
    "Plastico": 4
}

def home(requests):
    return render(requests, "home.html")

class VideoCamera:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.lock = threading.Lock()
        self.current_frame = None
        self.detections = []
        self.total_detections = []
        self.analyzing = False
        self.result = ""
        self.qr = False
        self.initial_prediction_done = False
        self.id_residuo = None
        self.puntos_residuo = 0

    def release(self):
        """ Libera la cámara. """
        if self.cap.isOpened():
            self.cap.release()

    def get_frame(self):
        with self.lock:
            if self.current_frame is None:
                return None
            ret, jpeg = cv2.imencode('.jpg', self.current_frame)
            return jpeg.tobytes()

    def update(self):
        self.detections = []
        self.total_detections = {
            "PLASTIC": [], "PAPER": [], "METAL": [], "GLASS": [], "CARDBOARD": [], "TRASH": []
        }
        self.areas = []

        frame_counter = 0
        skip_frames = 20
        last_detections = []

        def detect_async(camera_obj, frame):
            nonlocal last_detections
            # Run detection in separate thread
            result = model_detect(frame)
            last_detections = result  # Save for future frames
            if not camera_obj.initial_prediction_done:
                camera_obj.initial_prediction_done = True

        # Hago una primera clasificación
        ret, frame = self.cap.read()
        threading.Thread(target=detect_async, args=(self, frame.copy(),), daemon=True).start()

        while True:
            ret, frame = self.cap.read()
            if not ret:
                continue

            frame_counter += 1

            if self.analyzing:
                if frame_counter % skip_frames == 0:
                    # Start detection in a separate thread
                    threading.Thread(target=detect_async, args=(self, frame.copy(),), daemon=True).start()

                for det in last_detections:
                    x, y, w, h = det['bbox']
                    area = calc_area(det['bbox'])
                    dist = calc_dist(det['bbox'])
                    label, confidence = det['label'].split(' ')
                    self.total_detections[label].append((area, dist))

                    color = COLOR_MAP.get(label, (255, 255, 255))
                    label = LABEL_TRANSLATIONS.get(label, label)

                    # Agrego los rectángulos y nombres de clases
                    cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)

                    (text_width, text_height), baseline = cv2.getTextSize(f"{label} {confidence}", cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
                    cv2.rectangle(frame, (x, y - text_height - 15), (x + text_width, y), color, -1)
                    cv2.putText(frame, f"{label} {confidence}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            with self.lock:
                self.current_frame = frame
                self.detections = last_detections

    def start_analyzing(self):
        self.analyzing = True
        threading.Timer(5.0, self.restart_analyzer).start()

    def restart_analyzer(self):
        self.analyzing = False

        frame_area = 640 * 480
        total_detections = sum(len(v) for v in self.total_detections.values())

        if total_detections == 0:
            self.result = ""
            self.qr = False
            self.total_detections = {
                "PLASTIC": [], "PAPER": [], "METAL": [], "GLASS": [], "CARDBOARD": [], "TRASH": []
            }
            return

        max_score = -1
        res = ""
        for key, val in self.total_detections.items():
            frequency = len(val)
            if frequency == 0:
                continue

            areas = []
            dists = []
            for v in val:
                areas.append(v[0])
                dists.append(v[1])

            average_area = sum(areas) / frequency
            average_dist = sum(dists) / frequency

            # Normalizo los valores
            normalized_frequency = frequency / total_detections
            normalized_area = average_area / frame_area
            normalized_dist = average_dist / (camera_w * camera_h)

            # Calculo el score
            score = (0.4 * normalized_frequency) + (0.8 * (1 - normalized_dist))
            
            if score > max_score:
                max_score = score
                res = key

        self.result = LABEL_TRANSLATIONS.get(res, res)
        tipo_residuo = TipoResiduo.objects.get(nombre=self.result) # Busco el tipo de residuo
        nuevo_residuo = Residuo.objects.create(tipo_residuo=tipo_residuo) # Creo un nuevo residuo
        self.puntos_residuo = tipo_residuo.puntos # Asigno los puntos del residuo
        signer = Signer()
        self.id_residuo = signer.sign(nuevo_residuo.id) # Firmo el ID del residuo antes de enviarlo en el qr
        self.qr = True

        self.total_detections = {
            "PLASTIC": [], "PAPER": [], "METAL": [], "GLASS": [], "CARDBOARD": [], "TRASH": []
        }
        
        if self.result != "":
            led = CLASS_TO_LED.get(self.result, 0)
            if (led != 0):
                mandar(led)

    def __del__(self):
        self.cap.release()

camera_instance = None
camera_lock = threading.Lock()

def get_camera():
    """ Retorna la instancia de la cámara. Si no está inicializada, la inicializa. """
    global camera_instance
    with camera_lock:
        if camera_instance is None:
            print("Initializing camera for the first time...")
            camera_instance = VideoCamera()
            threading.Thread(target=camera_instance.update, daemon=True).start()
            print("Camera initialized.")
    return camera_instance

def calc_area(box):
    """ Calcula el área de la caja. """
    x, y, w, h = box
    return int(w) * int(h)

def calc_dist(box):
    """ Calcula la distancia entra el centro de la cámara y la esquina superior izquierda de la caja. """
    x, y, w, h = box
    distancia = ((centro_camara[0] - x) ** 2 + (centro_camara[1] - y) ** 2)
    return distancia

def gen():
    camera = get_camera()
    while True:
        frame = camera.get_frame()
        if frame:
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

def video_feed(request):
    return StreamingHttpResponse(gen(), content_type='multipart/x-mixed-replace; boundary=frame')

def start_analyzing(request):
    camera = get_camera()
    camera.start_analyzing()
    return HttpResponse(200)

def stream_result(request):
    """Stream result updates via SSE"""
    def event_stream():
        camera = get_camera()
        last_value = None
        while True:
            if camera.result != last_value:
                last_value = camera.result
                yield f"data: {camera.result}\n\n"
            time.sleep(1)  # check every second

    return StreamingHttpResponse(event_stream(), content_type="text/event-stream")

def stream_qr(request):
    """Stream qr updates via SSE"""
    def event_stream():
        camera = get_camera()
        while True:
            if camera.qr:
                yield f"data: {camera.qr}\n\n"
                camera.qr = False
            time.sleep(1)  # check every second

    return StreamingHttpResponse(event_stream(), content_type="text/event-stream")

def stream_initial_prediction_status(request):
    """Stream initial prediction status via SSE"""
    def event_stream():
        camera = get_camera()
        while True:
            if camera.initial_prediction_done:
                yield f"data: true\n\n"
                break # Stop sending after first time
            time.sleep(0.5)

    return StreamingHttpResponse(event_stream(), content_type="text/event-stream")

def qr_code_view(request):
    camera = get_camera()
    # generate QR with result

    python_dict = {
        "ID Residuo": camera.id_residuo,
        "Puntos": camera.puntos_residuo,
    }

    json_string = json.dumps(python_dict)
    img = qrcode.make(json_string)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return HttpResponse(buffer.getvalue(), content_type="image/png")

def model_detect(frame):
    detections_from_yolo = recortar_img_from_frame(frame)
    
    detections = []
    for item in detections_from_yolo:
        detections.append({
            'bbox': item['bbox'],
            'label': f"{item['class_name']} ({item['confidence']:.2f})",
            'confidence': item['confidence']
        })
        
    return detections

def encontrar_arduino():
    # VID y PID del Arduino Uno original y otros
    dispositivos_arduino = [
        ("2341", "0043"),  # Arduino Uno original
        ("2341", "0001"),  # Otra variante oficial
        ("1A86", "7523"),  # CH340 clones
    ]
    
    for puerto in list_ports.comports():
        vid = f"{puerto.vid:04X}" if puerto.vid else None
        pid = f"{puerto.pid:04X}" if puerto.pid else None

        if (vid, pid) in dispositivos_arduino:
            return puerto.device  # Ej: "COM7"
    
    return None

arduino_instance = None
arduino_lock = threading.Lock()

def get_arduino():
    """
    Retorna la instancia de arduino y se conecta a uno, si no está conectado.
    """
    global arduino_instance
    with arduino_lock:
        if arduino_instance is None:
            try:
                puerto = encontrar_arduino()
                if puerto:
                    print(f"Conectando a {puerto}...")
                    arduino_instance = serial.Serial(puerto, 9600, timeout=1)
                    print("Conectado.")
                else:
                    print("No se encontró un Arduino UNO conectado.")
            except serial.SerialException as e:
                print("Error al conectar con el puerto:", e)
    return arduino_instance

def mandar(led_num):
    """
    Envía un número entre 1 y 4 al Arduino, para prender el LED correspondiente.
    """
    arduino = get_arduino()
    if not arduino:
        return

    try:
        time.sleep(2)
        dato = led_num
        if dato == 0:
            arduino.close()
            print("Conexión cerrada.")
            return
        if int(dato) < 5:
            arduino.write((str(dato) + '\n').encode())
            print(f"Número {dato} enviado.")
        else:
            print(f"Número invalido.")
    except serial.SerialException as e:
        print("Error al enviar datos:", e)