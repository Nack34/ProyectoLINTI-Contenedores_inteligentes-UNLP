from django.shortcuts import render
from django.http import HttpResponse
import os
from django.conf import settings

def home(requests):
    return render(requests, "home.html")

from django.http import StreamingHttpResponse
import cv2
import threading
import json
from image_processing.clasificar_objetos import clasificar_img_from_array
from image_processing.recortar_objetos import recortar_img_from_frame
from collections import Counter

# This global or class will run your capture + detection loop
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

    def get_frame(self):
        with self.lock:
            if self.current_frame is None:
                return None
            ret, jpeg = cv2.imencode('.jpg', self.current_frame)
            return jpeg.tobytes()

    def update(self):
        self.detections = []
        self.total_detections = {
            "0": [],
            "1": [],
            "2": [],
            "3": [],
            "4": [],
            "5": []
        }
        self.areas = []

        frame_counter = 0
        skip_frames = 20
        last_detections = []

        def detect_async(frame):
            nonlocal last_detections
            # Run detection in separate thread
            result = model_detect(frame)
            last_detections = result  # Save for future frames

        while True:
            ret, frame = self.cap.read()
            if len(last_detections) == 0:
                last_detections = model_detect(frame)
            if not ret:
                continue

            frame_counter += 1

            if self.analyzing:
                if frame_counter % skip_frames == 0:
                    # Start detection in a separate thread
                    threading.Thread(target=detect_async, args=(frame.copy(),), daemon=True).start()

                # Draw last known detections on current frame
                iter = []
                for det in last_detections:
                    x, y, w, h = det['bbox']
                    area = calc_area(det['bbox'])
                    label = det['label']
                    self.total_detections[label[0]].append(area)

                    #iter.append((label, area))
                    label = en_to_es2(det['label'])
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(frame, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)

            with self.lock:
                self.current_frame = frame
                self.detections = last_detections

    def start_analyzing(self):
        self.analyzing = True
        threading.Timer(5.0, self.restart_analyzer).start()

    def restart_analyzer(self):
        self.analyzing = False

        max = 0
        res = ""
        for key, val in self.total_detections.items():
            prom = (Counter(val).total() + 1) / (len(val) + 1)
            aux = 0.4 * len(val) + 0.8 * prom
            if aux > max:
                max = aux
                res = key

        self.qr = True
        self.result = en_to_es(res)
        self.total_detections = {
            "0": [],
            "1": [],
            "2": [],
            "3": [],
            "4": [],
            "5": []
        }
        
        if self.result != "":
            led = str_to_num(self.result)
            if (led != 0):
                mandar(led)

    def __del__(self):
        self.cap.release()

camera_instance = None
camera_lock = threading.Lock()

def get_camera():
    """
    Initializes and returns the singleton camera object.
    """
    global camera_instance
    with camera_lock:
        if camera_instance is None:
            print("Initializing camera for the first time...")
            camera_instance = VideoCamera()
            # Start the background frame update thread
            threading.Thread(target=camera_instance.update, daemon=True).start()
            print("Camera initialized.")
    return camera_instance

def calc_area(box):
    x, y, w, h = box
    return int(w) * int(h)

def en_to_es(label):
    match label:
        case "0":
            return "Carton"
        case "1":
            return "Vidrio"
        case "2":
            return "Metal"
        case "3":
            return "Papel"
        case "4":
            return "Plastico"
        case "5":
            return "Basura"
        case _:
            return label
        
def en_to_es2(label):
    num = label[0]

    match num:
        case "0":
            return "Carton"
        case "1":
            return "Vidrio"
        case "2":
            return "Metal"
        case "3":
            return "Papel"
        case "4":
            return "Plastico"
        case "5":
            return "Basura"
        case _:
            return label

def str_to_num(label):
    match label:
        case "Carton":
            return 1
        case "Metal":
            return 2
        case "Papel":
            return 3
        case "Plastico":
            return 4
        case _:
            return 0

#camera = VideoCamera()
#threading.Thread(target=camera.update, daemon=True).start()

def gen():
    camera = get_camera()
    while True:
        frame = camera.get_frame()
        if frame:
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

def video_feed(request):
    return StreamingHttpResponse(gen(), content_type='multipart/x-mixed-replace; boundary=frame')

def start_analyzing(request):
    camera = get_camera() # Get the camera instance
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

import qrcode
import io

def qr_code_view(request):
    camera = get_camera()
    # generate QR with result
    img = qrcode.make(f"Operation ID: {camera.result}")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return HttpResponse(buffer.getvalue(), content_type="image/png")

def model_detect(frame):
    # 1) Detect object crops + boxes + initial class from detection model
    crops_info = recortar_img_from_frame(frame)  # list of dicts with bbox, crop_img, etc

    detections = []

    # 2) For each crop, run classification model
    for item in crops_info:
        crop_img = item['crop_img']
        label, conf_score = clasificar_img_from_array(crop_img)

        detections.append({
            'bbox': item['bbox'],
            'label': f"{label} ({conf_score:.2f})",
            'confidence': conf_score
        })

    return detections

import serial
import serial.tools.list_ports as list_ports
import time

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

puerto = encontrar_arduino()    
baudrate = 9600

arduino = serial.Serial(puerto, baudrate, timeout=1)

def mandar(led_num):
    # Configura el puerto y la velocidad (deben coincidir con Arduino)

    try:
        time.sleep(2)  # Esperar a que el Arduino se reinicie

        if puerto:
            print(f"Conectado a {puerto}.")
        else:
            print("No se encontró un Arduino UNO conectado.")
            return
        
        dato = led_num
        if dato == 0:
            arduino.close()
            print("Conexión cerrada.")
            return
        if int(dato) < 5:
            arduino.write((str (dato) + '\n').encode())
            print(f"Número {dato} enviado.")
        else:
            print(f"Número invalido.")
            return

    except serial.SerialException as e:
        print("Error al conectar con el puerto:", e)
