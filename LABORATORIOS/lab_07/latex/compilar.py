#!/usr/bin/env python3
"""Compila el informe de la Guía 07 con pdflatex y verifica referencias."""

import subprocess
import sys
from pathlib import Path


def compilar():
    base = Path(__file__).resolve().parent
    if not (base / "secciones" / "04_tab_generacion.tex").exists():
        print("Faltan tablas: ejecute primero python/experiments.py")
        return False
    for generator in ("render_resueltos.py", "render_propuesto1.py"):
        resultado = subprocess.run([sys.executable, str(base.parent / "python" / generator)],
                                   cwd=base.parent, check=False)
        if resultado.returncode:
            print(f"No se pudieron generar las evidencias: {generator}")
            return False
    command = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"]
    for run in range(1, 4):
        try:
            process = subprocess.run(command, cwd=base, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, check=False)
        except FileNotFoundError:
            print("pdflatex no está disponible en PATH")
            return False
        (base / "compilacion.log").write_bytes(process.stdout)
        output = process.stdout.decode("utf-8", errors="replace")
        if process.returncode:
            print(f"Error en pasada {run}; ver latex/compilacion.log")
            print(output[-1800:])
            return False
        print(f"Pasada {run}/3: correcta")
        if run >= 2 and "Rerun to get" not in output and "undefined references" not in output:
            break
    pdf = base / "main.pdf"
    if not pdf.exists():
        print("No se generó main.pdf")
        return False
    print(f"Informe generado: {pdf} ({pdf.stat().st_size / 1024:.1f} KiB)")
    return True


if __name__ == "__main__":
    sys.exit(0 if compilar() else 1)
