#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de compilación para el informe de Laboratorio 06 (UNSAAC - Grupo 5).
Ejecuta las pasadas necesarias de pdflatex para resolver referencias cruzadas,
índices (TOC, LOF, LOT) y marcadores PDF.
"""

import os
import subprocess
import sys

def compilar():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)
    
    print("=" * 65)
    print(" Compilando Informe de Laboratorio 06 (UNSAAC - Grupo 5)")
    print(" Tema: Algoritmos Fundamentales de Teoria de Numeros")
    print("=" * 65)
    
    cmd = ['pdflatex', '-interaction=nonstopmode', 'main.tex']
    
    for pasada in range(1, 4):
        print(f"[{pasada}/3] Compilando con pdflatex...")
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        with open('compilacion.log', 'wb') as lf:
            lf.write(r.stdout)
        out = r.stdout.decode('utf-8', errors='replace')
        if r.returncode != 0:
            print(f"Error en pasada {pasada} (ver compilacion.log):")
            safe_tail = out[-3000:].encode('ascii', 'replace').decode('ascii')
            print(safe_tail)
            return False
        if pasada >= 2 and "Rerun to get" not in out and "undefined references" not in out:
            print(f"[OK] Indices y referencias resueltos completamente en pasada {pasada}.")
            break
        
    if os.path.exists('main.pdf'):
        size_kb = os.path.getsize('main.pdf') / 1024
        print(f"\n[OK] Documento PDF generado exitosamente: main.pdf ({size_kb:.1f} KB)")
        return True
    else:
        print("[ERROR] No se encontro el archivo main.pdf.")
        return False

if __name__ == '__main__':
    exito = compilar()
    sys.exit(0 if exito else 1)
