#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import argparse
import unicodedata
from pathlib import Path
from tqdm import tqdm

import numpy as np
import pandas as pd
from PIL import Image
import matplotlib.pyplot as plt

from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    accuracy_score,
    balanced_accuracy_score,
    precision_recall_fscore_support,
)

from tensorflow.keras.models import load_model

def normalize_text(s: str) -> str:
    s = s.lower().strip()
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
    return s

def read_labels(labels_path: Path):
    if not labels_path.exists():
        return None
    with labels_path.open('r', encoding='utf-8') as f:
        labels = [line.strip() for line in f.readlines() if line.strip()]
    return labels

def infer_labels_from_folders(images_dir: Path):
    subdirs = [p.name for p in sorted(images_dir.iterdir()) if p.is_dir()]
    return subdirs

def prepare_image(img_path: Path, target_size, channels_last=True):
    img = Image.open(img_path).convert('RGB')
    img = img.resize((target_size[1], target_size[0]), Image.LANCZOS)
    arr = np.asarray(img, dtype=np.float32) / 255.0  # normalizamos a [0,1]
    if not channels_last:
        arr = np.transpose(arr, (2,0,1))
    return arr

def softmax(x):
    e = np.exp(x - np.max(x))
    return e / e.sum()

def plot_confusion_matrix(cm, labels, out_path, normalize=False):
    if normalize:
        cm_sum = cm.sum(axis=1)[:, np.newaxis]
        cm_norm = cm.astype('float') / np.where(cm_sum==0, 1, cm_sum)
        disp = cm_norm
    else:
        disp = cm

    fig, ax = plt.subplots(figsize=(max(6, len(labels)*0.5), max(6, len(labels)*0.5)))
    im = ax.imshow(disp, interpolation='nearest', cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)
    ax.set(xticks=np.arange(len(labels)),
           yticks=np.arange(len(labels)),
           xticklabels=labels, yticklabels=labels,
           ylabel='Etiqueta real',
           xlabel='Etiqueta predicha',
           title='Matriz de confusión' + (' (normalizada por fila)' if normalize else ''))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    fmt = '.2f' if normalize else 'd'
    thresh = disp.max() / 2.
    for i in range(disp.shape[0]):
        for j in range(disp.shape[1]):
            ax.text(j, i, format(disp[i, j], fmt),
                    ha="center", va="center",
                    color="white" if disp[i, j] > thresh else "black")
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches='tight', dpi=200)
    plt.close(fig)

def main(args):
    images_dir = Path(args.images_dir)
    model_path = Path(args.model)
    labels_path = Path(args.labels) if args.labels else None
    metrics_dir = Path(args.metrics_dir)

    if not model_path.exists():
        print(f"ERROR: modelo no encontrado en {model_path}", file=sys.stderr)
        sys.exit(1)
    if not images_dir.exists():
        print(f"ERROR: carpeta de imágenes no encontrada en {images_dir}", file=sys.stderr)
        sys.exit(1)
    metrics_dir.mkdir(parents=True, exist_ok=True)

    print("Cargando modelo:", model_path)
    model = load_model(str(model_path))
    # intentar inferir tamaño de entrada
    input_shape = model.input_shape  # e.g. (None, H, W, C) or (None, C, H, W)
    print("input_shape detectado:", input_shape)

    # resolver target_size y channel ordering
    if len(input_shape) == 4:
        _, a, b, c = input_shape
        if a is None:
            # caso raro: (None, None, None, 3)
            target_size = (224, 224, 3)
        else:
            target_size = (a, b, c)
    else:
        # fallback
        target_size = (224, 224, 3)

    channels_last = True
    if target_size[2] not in (1,3):
        # posible formato (None, C, H, W)
        channels_last = False
        # rearrange target size to (H,W,C)
        target_size = (target_size[1], target_size[2], target_size[0])

    H, W, C = target_size
    print(f"Usando tamaño de entrada: H={H} W={W} C={C}  channels_last={channels_last}")

    labels = None
    if labels_path:
        labels = read_labels(labels_path)
    if not labels:
        print("labels.txt no encontrado o vacío. Infiriendo etiquetas desde subcarpetas de images_dir.")
        labels = infer_labels_from_folders(images_dir)
    labels = [l for l in labels]
    n_classes = len(labels)
    print(f"Etiquetas ({n_classes}): {labels}")

    # crear diccionario de normalización para comparar nombres de carpeta con labels.txt
    norm_to_index = {normalize_text(lbl): idx for idx, lbl in enumerate(labels)}

    rows = []
    y_true = []
    y_pred = []
    skipped_for_metrics = 0

    # recorrer subcarpetas (cada subcarpeta se asume etiqueta real)
    subfolders = [p for p in images_dir.iterdir() if p.is_dir()]
    # Orden determinístico
    subfolders = sorted(subfolders, key=lambda p: p.name)

    for folder in subfolders:
        true_label_name = folder.name
        true_norm = normalize_text(true_label_name)
        true_index = norm_to_index.get(true_norm, None)

        image_files = [p for p in folder.rglob('*') if p.is_file() and p.suffix.lower() in ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tif', '.tiff')]
        for img_path in tqdm(sorted(image_files), desc=f"Procesando {folder.name}", unit="img"):
            try:
                arr = prepare_image(img_path, (H, W, C), channels_last=channels_last)
                batch = np.expand_dims(arr, axis=0).astype(np.float32)
                preds = model.predict(batch)
                # modelo puede devolver vector (1, n) o (1,)
                probs = preds[0]
                if probs.ndim == 0:
                    probs = np.array([probs])
                # si no se normaliza a 1, aplicamos softmax
                if not np.isclose(np.sum(probs), 1.0):
                    probs = softmax(probs)
                pred_index = int(np.argmax(probs))
                pred_label = labels[pred_index] if pred_index < len(labels) else str(pred_index)

                prob_dict = {f"p_{lbl}": float(probs[i]) if i < len(probs) else None for i, lbl in enumerate(labels)}

                rows.append({
                    "image": str(img_path),
                    "true_label_folder": true_label_name,
                    "true_index": int(true_index) if true_index is not None else None,
                    "pred_index": pred_index,
                    "pred_label": pred_label,
                    **prob_dict
                })

                if true_index is None:
                    skipped_for_metrics += 1
                    # no añadimos a lista para métricas porque no sabemos el índice
                else:
                    y_true.append(true_index)
                    y_pred.append(pred_index)

            except Exception as e:
                print(f"WARNING: fallo procesando imagen {img_path}: {e}", file=sys.stderr)

    # Guardar CSV con todas las predicciones
    df = pd.DataFrame(rows)
    csv_path = metrics_dir / "predictions.csv"
    df.to_csv(csv_path, index=False, encoding='utf-8')
    print("Predicciones guardadas en", csv_path)

    if len(y_true) == 0:
        print("No hay ejemplos con etiqueta verdadera mapeada a índices -> no se pueden calcular métricas.", file=sys.stderr)
        return

    # calcular métricas
    y_true = np.array(y_true, dtype=int)
    y_pred = np.array(y_pred, dtype=int)

    acc = float(accuracy_score(y_true, y_pred))
    bacc = float(balanced_accuracy_score(y_true, y_pred))
    precision, recall, f1, support = precision_recall_fscore_support(y_true, y_pred, labels=range(n_classes), zero_division=0)

    # classification report
    report = classification_report(y_true, y_pred, labels=range(n_classes), target_names=labels, zero_division=0)
    with (metrics_dir / "classification_report.txt").open('w', encoding='utf-8') as f:
        f.write(report)
    print("Classification report guardado.")

    # confusion matrix
    cm = confusion_matrix(y_true, y_pred, labels=range(n_classes))
    cm_csv_path = metrics_dir / "confusion_matrix.csv"
    pd.DataFrame(cm, index=labels, columns=labels).to_csv(cm_csv_path, encoding='utf-8')
    print("Matriz de confusión (csv) guardada en", cm_csv_path)

    # guardar imagen de matriz de confusión (absoluta y normalizada)
    cm_png = metrics_dir / "confusion_matrix.png"
    plot_confusion_matrix(cm, labels, cm_png, normalize=False)
    cm_png_norm = metrics_dir / "confusion_matrix_normalized.png"
    plot_confusion_matrix(cm, labels, cm_png_norm, normalize=True)
    print("Matriz de confusión (png) guardada en", cm_png, "y", cm_png_norm)

    metrics_summary = {
        "accuracy": acc,
        "balanced_accuracy": bacc,
        "num_images_total": len(rows),
        "num_images_with_mapped_true_label": int(len(y_true)),
        "num_skipped_due_to_unmapped_true_label": int(skipped_for_metrics),
        "n_classes": n_classes,
        "labels": labels,
        "per_class": [
            {"label": labels[i], "precision": float(precision[i]), "recall": float(recall[i]), "f1": float(f1[i]), "support": int(support[i])}
            for i in range(n_classes)
        ]
    }

    with (metrics_dir / "metrics.json").open('w', encoding='utf-8') as f:
        json.dump(metrics_summary, f, ensure_ascii=False, indent=2)

    print("Resumen de métricas guardado en", metrics_dir / "metrics.json")
    print("Hecho. Revisa la carpeta:", metrics_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluar modelo Keras sobre carpetas de imágenes y generar métricas.")
    parser.add_argument("--model", "-m", default="keras_model.h5", help="Ruta al archivo keras_model.h5")
    parser.add_argument("--labels", "-l", default="labels.txt", help="Ruta a labels.txt (una etiqueta por línea). Si falta, inferirá desde subcarpetas de images/.")
    parser.add_argument("--images-dir", "-i", default="images", help="Carpeta que contiene subcarpetas por clase con imágenes.")
    parser.add_argument("--metrics-dir", "-o", default="métricas", help="Carpeta donde se guardarán métricas (por defecto 'métricas').")
    args = parser.parse_args()
    main(args)
