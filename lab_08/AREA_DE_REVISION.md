# Áreas de Revisión por Integrante — Laboratorio 08

**UNSAAC · Algoritmos Avanzados · 2026-II · Grupo 5**

---

## 1. Biblioteca Central y Algoritmos FFT/NTT
* **Rama:** `lab08/franki-biblioteca` (`ramaFranki`)
* **Integrante:** Noe Franklin Choquenaira Quispe (133962)
* **Archivos principales:**
  * `python/transforms.py`: convolución directa, FFT/IFFT recursiva, FFT iterativa *in-place*, aritmética modular y NTT en $\mathbb{F}_p$.
  * `python/ejercicios_resueltos.py`: contratos y resultados de los tres ejercicios de la guía (directa, FFT y NTT en $\mathbb{F}_{17}$).
* **Comprobación sugerida:**
  ```powershell
  python python/ejercicios_resueltos.py
  python python/test_transforms.py
  ```

---

## 2. Casos Deterministas, Resueltos y Pruebas Unitarias
* **Rama:** `lab08/yeni-pruebas` (`ramaYeni`)
* **Integrante:** Yeni Ruth Porroa Sivana (120893)
* **Archivos principales:**
  * `python/case_generator.py`: semillas reproducibles, casos de frontera y generador de polinomios.
  * `python/test_transforms.py`: suite completa de pruebas automatizadas y validación de propiedades mínimas (padding, raíces, oráculos).
* **Comprobación sugerida:**
  ```powershell
  python python/test_transforms.py
  ```

---

## 3. Batería Experimental, Mediciones y Auditoría
* **Rama:** `lab08/romario-experimentos` (`RamaRomario`)
* **Integrante:** Romario Quispe Rimachi (164257)
* **Archivos principales:**
  * `python/experiments.py`: escenarios A, B y C (tiempos $2^3 \dots 2^{14}$, 10 repeticiones, conteo de mariposas y errores de redondeo).
  * `python/verify_results.py`: auditoría y validación estricta de CSV y figuras.
  * `python/results/` y `python/figures/`: evidencia experimental (10 CSV y 3 figuras PNG).
* **Comprobación sugerida:**
  ```powershell
  python python/experiments.py --max-k 14 --repetitions 10
  python python/verify_results.py
  ```

---

## 4. Informe Académico en LaTeX y Cuaderno Google Colab
* **Rama:** `lab08/aldo-informe-colab` (`ramaAldo`)
* **Integrante:** Aldo Yaranga Achahui (103179)
* **Archivos principales:**
  * `latex/`: informe modular bajo estándar APA 7, tablas booktabs, figuras (`latex/figuras/`), y compilador pdflatex (`main.pdf`).
  * `colab/grupo 5 guia 08.ipynb`: cuaderno autónomo con salidas inline (tablas HTML y gráficos SVG), sin uso de `%%writefile`.
  * `python/render_report.py`: generador de fragmentos y tablas LaTeX a partir de la evidencia experimental.
  * `python/build_notebook.py`: constructor del notebook interactivo con outputs pre-evaluados.
* **Comprobación sugerida:**
  ```powershell
  python python/build_notebook.py
  python latex/compilar.py
  ```
