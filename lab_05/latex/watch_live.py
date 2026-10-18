#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vigilante en tiempo real (Live Auto-Compiler) para el informe LaTeX de Lab 05.
Detecta cualquier modificación guardada en main.tex o en secciones/*.tex
y recompila automáticamente el PDF al instante.
"""

import os
import time
import subprocess
from datetime import datetime

def obtener_tiempos_archivos(directorio):
    tiempos = {}
    archivos_a_vigilar = ['main.tex']
    
    sec_dir = os.path.join(directorio, 'secciones')
    if os.path.exists(sec_dir):
        for f in os.listdir(sec_dir):
            if f.endswith('.tex'):
                archivos_a_vigilar.append(os.path.join('secciones', f))
                
    for rel_path in archivos_a_vigilar:
        full_path = os.path.join(directorio, rel_path)
        if os.path.exists(full_path):
            tiempos[rel_path] = os.path.getmtime(full_path)
            
    return tiempos

def recompilar(directorio):
    hora = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{hora}] Cambio detectado en el informe. Recompilando PDF en tiempo real...")
    
    cmd = ['pdflatex', '-interaction=nonstopmode', 'main.tex']
    p = subprocess.run(cmd, cwd=directorio, capture_output=True, text=True)
    
    if p.returncode == 0 and ("Rerun to get" in p.stdout or "undefined references" in p.stdout):
        p = subprocess.run(cmd, cwd=directorio, capture_output=True, text=True)

    if p.returncode == 0:
        pdf_path = os.path.join(directorio, 'main.pdf')
        if os.path.exists(pdf_path):
            size_kb = os.path.getsize(pdf_path) / 1024
            print(f"[{hora}] [OK] PDF actualizado exitosamente: main.pdf ({size_kb:.1f} KB).")
    else:
        print(f"[{hora}] [AVISO] pdflatex reportó errores en la sintaxis:")
        lineas_error = [l for l in p.stdout.split('\n') if l.startswith('!') or 'Error' in l]
        for l in lineas_error[:5]:
            print(f"   -> {l}")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print("=" * 65)
    print(" MODO VIGILANTE EN TIEMPO REAL INICIADO (LABORATORIO 05)")
    print(" Directorio: " + base_dir)
    print(" Modifica y guarda cualquier archivo .tex para ver el PDF en vivo.")
    print(" Presiona Ctrl + C para detener.")
    print("=" * 65)

    POLL_INTERVAL = 0.30
    DEBOUNCE_SECONDS = 0.60

    recompilar(base_dir)
    estado_previo = obtener_tiempos_archivos(base_dir)
    ultimo_cambio = time.monotonic()
    compilacion_pendiente = False

    try:
        while True:
            time.sleep(POLL_INTERVAL)
            estado_actual = obtener_tiempos_archivos(base_dir)
            cambio_detectado = False
            for f, mtime in estado_actual.items():
                if f not in estado_previo or mtime > estado_previo[f]:
                    cambio_detectado = True
                    break

            if cambio_detectado:
                ultimo_cambio = time.monotonic()
                compilacion_pendiente = True
                estado_previo = estado_actual

            if compilacion_pendiente and (time.monotonic() - ultimo_cambio) >= DEBOUNCE_SECONDS:
                recompilar(base_dir)
                compilacion_pendiente = False
                estado_previo = obtener_tiempos_archivos(base_dir)
    except KeyboardInterrupt:
        print("\nModo vigilante detenido por el usuario.")

if __name__ == '__main__':
    main()
