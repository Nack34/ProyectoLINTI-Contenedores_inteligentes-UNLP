import io
import time
import json
import base64
import threading
import numpy as np
import cv2
import qrcode
import serial
import serial.tools.list_ports as list_ports

# REMOVED: StreamingHttpResponse (this fixes the warning)
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from api.models import Residuo, TipoResiduo
from django.core.signing import Signer
from django.views.decorators.csrf import csrf_exempt

# from image_processing.clasificar_objetos import clasificar_img_from_array
from image_processing.recortar_objetos import recortar_img_from_frame

camera_w = 640
camera_h = 480
centro_camara = (camera_w / 2, camera_h / 2)

COLOR_MAP = {
    'TRASH': (0, 0, 255),        
    'CARDBOARD': (42, 128, 244), 
    'GLASS': (0, 255, 0),        
    'METAL': (128, 0, 128),       
    'PAPER': (240, 240, 0),      
    'PLASTIC': (255, 0, 0)       
}

LABEL_TRANSLATIONS = {
    "CARDBOARD": "Carton",
    "GLASS": "Vidrio",
    "METAL": "Metal",
    "PAPER": "Papel",
    "PLASTIC": "Plastico",
    "TRASH": "Basura"
}

CLASS_TO_LED = {
    "Carton": 1,
    "Metal": 2,
    "Papel": 3,
    "Plastico": 4
}

# --- State Management ---
class ClassificationState:
    def __init__(self):
        self.lock = threading.Lock()
        self.reset()

    def reset(self):
        self.analyzing = False
        self.start_time = 0
        self.total_detections = {
            "PLASTIC": [], "PAPER": [], "METAL": [], "GLASS": [], "CARDBOARD": [], "TRASH": []
        }
        self.result = ""
        self.id_residuo = None
        self.puntos_residuo = 0
        self.qr_ready = False

    def start_analysis(self):
        with self.lock:
            self.reset()
            self.analyzing = True
            self.start_time = time.time()

classifier_state = ClassificationState()

# --- Views ---

def home(requests):
    return render(requests, "home.html")

@csrf_exempt
def process_frame(request):
    """
    Receives a Base64 image from frontend, processes it ONLY if analyzing, and returns detections.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        image_data = data.get('image')
        
        if not image_data:
            return JsonResponse({'error': 'No image data'}, status=400)
            
        # Decode Base64
        header, encoded = image_data.split(",", 1)
        data = base64.b64decode(encoded)
        np_arr = np.frombuffer(data, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is None:
            return JsonResponse({'error': 'Failed to decode image'}, status=400)

        detections = []
        final_result = None
        qr_ready = False
        
        with classifier_state.lock:
            # 1. STOP CLASSIFYING IF NOT ANALYZING
            if classifier_state.analyzing:
                detections = model_detect(frame)

                for det in detections:
                    raw_label = det['raw_label'] 
                    if raw_label in classifier_state.total_detections:
                        area = calc_area(det['bbox'])
                        dist = calc_dist(det['bbox'])
                        classifier_state.total_detections[raw_label].append((area, dist))
                
                if time.time() - classifier_state.start_time > 5.0:
                    classifier_state.analyzing = False
                    finalize_result()
                    final_result = classifier_state.result
                    qr_ready = classifier_state.qr_ready
            
            elif classifier_state.result:
                final_result = classifier_state.result
                qr_ready = classifier_state.qr_ready

        response_data = {
            'detections': detections, 
            'final_result': final_result,
            'qr_ready': qr_ready
        }
        return JsonResponse(response_data)

    except Exception as e:
        print(f"Error processing frame: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def start_analyzing(request):
    classifier_state.start_analysis()
    return HttpResponse(200)

def qr_code_view(request):
    if not classifier_state.id_residuo:
        return HttpResponse("No result available", status=404)

    python_dict = {
        "ID Residuo": classifier_state.id_residuo,
        "Puntos": classifier_state.puntos_residuo,
    }

    json_string = json.dumps(python_dict)
    img = qrcode.make(json_string)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return HttpResponse(buffer.getvalue(), content_type="image/png")

# --- Helper Logic ---

def model_detect(frame):
    detections_from_yolo = recortar_img_from_frame(frame)
    detections = []
    
    for item in detections_from_yolo:
        label_key = item['class_name']
        color = COLOR_MAP.get(label_key, (255, 255, 255))
        translated_label = LABEL_TRANSLATIONS.get(label_key, label_key)
        
        detections.append({
            'bbox': item['bbox'], 
            'label': f"{translated_label} ({item['confidence']:.2f})",
            'raw_label': label_key,
            'confidence': float(item['confidence']),
            'color': color 
        })
        
    return detections

def finalize_result():
    frame_area = camera_w * camera_h 
    
    total_count = sum(len(v) for v in classifier_state.total_detections.values())

    if total_count == 0:
        classifier_state.result = "No detectado"
        classifier_state.qr_ready = False
        return

    max_score = -1
    best_label = ""

    for key, val in classifier_state.total_detections.items():
        frequency = len(val)
        if frequency == 0:
            continue

        areas = [v[0] for v in val]
        dists = [v[1] for v in val]

        average_area = sum(areas) / frequency
        average_dist = sum(dists) / frequency

        normalized_frequency = frequency / total_count
        normalized_area = average_area / frame_area
        normalized_dist = average_dist / (camera_w * camera_h)

        score = (0.4 * normalized_frequency) + (0.8 * (1 - normalized_dist))
        
        if score > max_score:
            max_score = score
            best_label = key

    classifier_state.result = LABEL_TRANSLATIONS.get(best_label, best_label)
    
    try:
        tipo_residuo = TipoResiduo.objects.get(nombre=classifier_state.result)
        nuevo_residuo = Residuo.objects.create(tipo_residuo=tipo_residuo)
        classifier_state.puntos_residuo = tipo_residuo.puntos
        signer = Signer()
        classifier_state.id_residuo = signer.sign(nuevo_residuo.id)
        classifier_state.qr_ready = True
        
        led = CLASS_TO_LED.get(classifier_state.result, 0)
        if led != 0:
            threading.Thread(target=mandar, args=(led,)).start()
            
    except Exception as e:
        print(f"Error saving result or triggering arduino: {e}")
        classifier_state.result = f"Error: {str(e)}"

def calc_area(box):
    x, y, w, h = box
    return int(w) * int(h)

def calc_dist(box):
    x, y, w, h = box
    distancia = ((centro_camara[0] - x) ** 2 + (centro_camara[1] - y) ** 2)
    return distancia

# --- Arduino Logic ---

def encontrar_arduino():
    dispositivos_arduino = [
        ("2341", "0043"),
        ("2341", "0001"),
        ("1A86", "7523"),
    ]
    for puerto in list_ports.comports():
        vid = f"{puerto.vid:04X}" if puerto.vid else None
        pid = f"{puerto.pid:04X}" if puerto.pid else None
        if (vid, pid) in dispositivos_arduino:
            return puerto.device 
    return None

arduino_instance = None
arduino_lock = threading.Lock()

def get_arduino():
    global arduino_instance
    with arduino_lock:
        if arduino_instance is None:
            try:
                puerto = encontrar_arduino()
                if puerto:
                    print(f"Conectando a {puerto}...")
                    arduino_instance = serial.Serial(puerto, 9600, timeout=1)
                else:
                    print("No se encontró un Arduino UNO conectado.")
            except serial.SerialException as e:
                print("Error al conectar con el puerto:", e)
    return arduino_instance

def mandar(led_num):
    arduino = get_arduino()
    if not arduino:
        return
    try:
        time.sleep(2) 
        dato = led_num
        if dato == 0:
            arduino.close()
            return
        if int(dato) < 5:
            arduino.write((str(dato) + '\n').encode())
            print(f"Número {dato} enviado.")
    except serial.SerialException as e:
        print("Error al enviar datos:", e)