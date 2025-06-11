# ProyectoLINTI-Contenedores_inteligentes-UNLP

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
