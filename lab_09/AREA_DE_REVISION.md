# Áreas de Revisión por Integrante — Laboratorio 09

**UNSAAC · Algoritmos Avanzados · 2026-II · Grupo 5**

---

## 1. Biblioteca Central de Compresión (`CMP9`) y CLI
* **Rama:** `lab09/franki-biblioteca` (`ramaFranki`)
* **Integrante:** Noe Franklin Choquenaira Quispe (133962)
* **Archivos principales:**
  * `python/compression.py`: interfaz `Compressor`, cálculo de entropía, Huffman canónico, RLE binario y LZ77 con ventana deslizante.
  * `python/cli.py`: compresión, descompresión, inspección de encabezados y comprobación automática SHA-256.
  * `python/ejercicios_resueltos.py`: los tres casos resueltos de la sección 8 (`b"AAAABBCD"`, longitudes canónicas y RLE `Sc = 8 + 3r`).
* **Comprobación sugerida:**
  ```powershell
  python python/ejercicios_resueltos.py
  python python/cli.py roundtrip --alg lz77 -i python/datasets/05_texto_espanol.txt
  ```

---

## 2. Corpus de Prueba y Suite Automatizada
* **Rama:** `lab09/yeni-pruebas` (`ramaYeni`)
* **Integrante:** Yeni Ruth Porroa Sivana (120893)
* **Archivos principales:**
  * `python/case_generator.py` y `python/datasets/`: 9 archivos de prueba (vacío, 1 byte, pocos bytes, símbolo único, texto español, patrones repetitivos, uniforme 256, aleatorio y PNG zlib) con licencia CC0 (`PROCEDENCIA_Y_LICENCIAS.md`).
  * `python/test_compression.py`: 24 pruebas `unittest` cubriendo los 14 casos mínimos de la sección 16 y truncamientos exhaustivos.
* **Comprobación sugerida:**
  ```powershell
  python python/test_compression.py
  ```

---

## 3. Campaña Experimental, Visualizaciones y Auditoría
* **Rama:** `lab09/romario-experimentos` (`RamaRomario`)
* **Integrante:** Romario Quispe Rimachi (164257)
* **Archivos principales:**
  * `python/experiments.py`: 10 repeticiones en núcleo en memoria, medición separada E2E en disco, sensibilidad LZ77 y memoria pico con `tracemalloc`.
  * `python/visualize.py`: visualizaciones didácticas paso a paso para Huffman canónico y LZ77.
  * `python/verify_results.py`: validación automática de los 7 CSV en `python/results/` y las 6 figuras PNG en `python/figures/`.
* **Comprobación sugerida:**
  ```powershell
  python python/experiments.py
  python python/verify_results.py
  ```

---

## 4. Informe Académico APA 7 y Cuaderno Colab
* **Rama:** `lab09/aldo-informe-colab` (`ramaAldo`)
* **Integrante:** Aldo Yaranga Achahui (103179)
* **Archivos principales:**
  * `latex/`: informe modular APA 7 (`main.tex` -> `main.pdf`), tablas `booktabs`, figuras y compilador `pdflatex`.
  * `python/render_report.py`: unifica generación de código/salidas resueltas, tablas desde CSV y control de 250–350 palabras en conclusiones.
  * `python/build_notebook.py` y `colab/grupo 5 guia 09.ipynb`: cuaderno autónomo inline con outputs, tablas HTML y SVG pre-evaluados.
* **Comprobación sugerida:**
  ```powershell
  python python/build_notebook.py --execute
  python latex/compilar.py
  ```
