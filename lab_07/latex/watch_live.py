#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vigilante en tiempo real (Live Auto-Compiler) para el informe LaTeX de Lab 07.
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
    p = subprocess.run(cmd, cwd=directorio, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = p.stdout.decode('latin-1', errors='replace')
    
    if p.returncode == 0 and ("Rerun to get" in out or "undefined references" in out):
        p = subprocess.run(cmd, cwd=directorio, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = p.stdout.decode('latin-1', errors='replace')

    if p.returncode == 0:
        pdf_path = os.path.join(directorio, 'main.pdf')
        if os.path.exists(pdf_path):
            size_kb = os.path.getsize(pdf_path) / 1024
            print(f"[{hora}] [OK] PDF actualizado exitosamente: main.pdf ({size_kb:.1f} KB).")
    else:
        print(f"[{hora}] [AVISO] pdflatex reporto errores en la sintaxis:")
        lineas_error = [l for l in out.split('\n') if l.startswith('!') or 'Error' in l]
        for l in lineas_error[:5]:
            print(f"   -> {l}")

def main():
    directorio = os.path.dirname(os.path.abspath(__file__))
    print("=" * 65)
    print(" Vigilante de Compilacion en Vivo Activado (Lab 07 - Grupo 5)")
    print(" Observando cambios en 'main.tex' y 'secciones/*.tex'...")
    print(" Presione Ctrl + C en cualquier momento para detener.")
    print("=" * 65)
    
    recompilar(directorio)
    
    tiempos_anteriores = obtener_tiempos_archivos(directorio)
    
    try:
        while True:
            time.sleep(1.2)
            tiempos_actuales = obtener_tiempos_archivos(directorio)
            
            hubo_cambios = False
            for f, mtime in tiempos_actuales.items():
                if f not in tiempos_anteriores or mtime > tiempos_anteriores[f]:
                    hubo_cambios = True
                    break
                    
            if hubo_cambios:
                recompilar(directorio)
                tiempos_anteriores = tiempos_actuales
    except KeyboardInterrupt:
        print("\n\nVigilante detenido por el usuario.")

if __name__ == '__main__':
    main()
