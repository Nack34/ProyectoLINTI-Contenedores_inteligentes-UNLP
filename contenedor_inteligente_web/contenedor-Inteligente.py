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

# Configura el puerto y la velocidad (deben coincidir con Arduino)
puerto = encontrar_arduino()     
baudrate = 9600

try:
    arduino = serial.Serial(puerto, baudrate, timeout=1)
    time.sleep(2)  # Esperar a que el Arduino se reinicie

    if puerto:
        print(f"Conectado a {puerto}.")
    else:
        print("No se encontró un Arduino UNO conectado.")
    
    while True:
        dato = input("Ingresá un número del 1 al 4 para enviar al Arduino (o '0' para terminar): ")
        if dato.lower() == '0':
            break
        if dato.isdigit():  # Solo permite números positivos
            if int(dato) < 5:
                arduino.write((dato + '\n').encode())
                print(f"Número {dato} enviado.")
            else:
                 print(f"Número invalido.")
        else:
            print("Por favor ingresá solo números enteros.")

    arduino.close()
    print("Conexión cerrada.")

except serial.SerialException as e:
    print("Error al conectar con el puerto:", e)
