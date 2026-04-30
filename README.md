# ProyectoLINTI-Contenedores_inteligentes-UNLP

Este repositorio está enmarcado en el proyecto "Una estación de residuos inteligente: un aporte de la Inteligencia Artificial a la economía circular", que aborda la problemática de la gestión de residuos sólidos urbanos en la comunidad de la Facultad de Informática de la Universidad Nacional de La Plata y se desarrolló en un proyecto de I+D de la propia institución.

En este contexto se desarrolló un prototipo funcional de una estación física de residuos inteligente que aplica técnicas de Aprendizaje Automático específicamente una red neuronal convolucional para clasificar imágenes de residuos reciclables, la cual fue entrenada con fotos de residuos generados en la facultad.

En el repositorio se encuentra la lógica del servidor web encargado de tomar las fotos, detectar los objetos presentes, clasificarlos en las distintas clases de residuos, y retornar un resultado al usuario junto con un código QR para la acreditación de puntos del lado de la aplicación. Además, estando conectado al Arduino UNO de la estación, envía una señal con el valor de la clasificación para que este pueda encender el LED correspondiente.

Este proyecto usa **Django** y está gestionado dentro de un entorno virtual creado con **Miniconda** para garantizar la reproducibilidad y evitar conflictos de dependencias.

---

## Requisitos previos

- Tener instalado [Miniconda](https://docs.conda.io/en/latest/miniconda.html).

---

## Guía rápida para instalar y ejecutar el proyecto

### 1. Clonar el repositorio

### 2. Crear y activar el entorno Conda


- Usá el script `manage_env.sh` para manejar las dependencias. Formato del comando:
   ```bash
   bash manage_env.sh [ -p | -u | -c ] [cpu|gpu (opcional, default=cpu)]
   ```
   - `-c`: Crear el entorno (solo una vez)
   - `-p`: Subir/pushear cambios en las dependencias
   - `-u`: Actualizar tus dependencias locales luego de hacer pull

   **Ejemplos usando CPU** (por defecto se usa `cpu` si no se especifica):
   ```bash
   bash manage_env.sh -c         # Crear entorno
   bash manage_env.sh -p         # Pushear dependencias nuevas
   bash manage_env.sh -u         # Actualizar dependencias locales
   ```

   > *Nota:* Actualmente el script `manage_env.sh` solo diferencia entre CPU y GPU para `torch`. Si en el futuro hay más paquetes con esta distinción, se deberá ajustar el script.

- Para activar el entorno:
   ```bash
   conda activate env_contenedor_inteligente
   ```

### 3. Ejecutar el servidor Django
   ```bash
    cd contenedor_inteligente_web
    python manage.py runserver
   ```

## Guía rápida para instalar y ejecutar el proyecto
