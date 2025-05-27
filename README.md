# ProyectoLINTI-Contenedores_inteligentes-UNLP

Este proyecto usa **Django** y está gestionado dentro de un entorno virtual creado con **Miniconda** para garantizar la reproducibilidad y evitar conflictos de dependencias.

---

## Requisitos previos

- Tener instalado [Miniconda](https://docs.conda.io/en/latest/miniconda.html).

---

## Guía rápida para instalar y ejecutar el proyecto

### 1. Clonar el repositorio

### 2. Crear y activar el entorno Conda

conda env create -f environment.yml <br>
conda activate env

### 3. Ejecutar el servidor Django

cd contenedor_inteligente_web <br>
python manage.py runserver

# Notas adicionales

### Si agregás nuevas dependencias, acordate de actualizar el archivo environment.yml con:

conda env export > environment.yml
