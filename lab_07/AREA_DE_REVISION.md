# Áreas de Revisión por Integrante - Laboratorio 07

**UNSAAC · Algoritmos Avanzados · 2026-II · Grupo 5**

---

## 1. Biblioteca Central y Algoritmos de Primalidad
* **Rama:** `lab07/franki-biblioteca` (`ramaFranki`)
* **Integrante:** Noe Franklin Choquenaira Quispe (133962)
* **Archivos principales:**
  * `python/primality.py`: división de prueba, Fermat, Miller–Rabin y generación de primos.
  * `python/ejercicios_resueltos.py`: contratos y resultados de los casos 221, 341 y 1009.
* **Comprobación sugerida:**
  ```powershell
  python python/test_primality.py
  python python/ejercicios_resueltos.py
  ```

---

## 2. Casos Deterministas, Resueltos y Pruebas Unitarias
* **Rama:** `lab07/yeni-pruebas` (`ramaYeni`)
* **Integrante:** Yeni Ruth Porroa Sivana (120893)
* **Archivos principales:**
  * `python/case_generator.py`: semillas, casos conocidos y compuestos construidos.
  * `python/ejercicios_resueltos.py`: salidas de los tres ejercicios.
  * `python/test_primality.py`: suite de 32 pruebas automatizadas y propiedades de la guía.
* **Comprobación sugerida:**
  ```powershell
  python python/ejercicios_resueltos.py
  python python/test_primality.py
  ```

---

## 3. Batería Experimental, Mediciones y Auditoría
* **Rama:** `lab07/romario-experimentos` (`RamaRomario`)
* **Integrante:** Romario Quispe Rimachi (164257)
* **Archivos principales:**
  * `python/experiments.py`: mediciones de generación y comparación de métodos.
  * `python/verify_results.py`: comprobación de CSV, parámetros y conteos.
  * `python/results/` y `python/figures/`: evidencia experimental (10 CSV y 4 gráficos PNG).
* **Comprobación sugerida:**
  ```powershell
  python python/experiments.py
  python python/verify_results.py
  ```

---

## 4. Informe Académico en LaTeX y Cuaderno Google Colab
* **Rama:** `lab07/aldo-informe-colab` (`ramaAldo`)
* **Integrante:** Aldo Yaranga Achahui (103179)
* **Archivos principales:**
  * `latex/`: informe modular APA 7, tablas, gráficos y compilador pdflatex (`main.pdf`).
  * `colab/grupo 5 guia 07.ipynb`: ejecución completa autónoma con salidas inline.
  * `python/render_resueltos.py` y `python/render_propuesto1.py`: generadores de fragmentos LaTeX.
* **Comprobación sugerida:**
  ```powershell
  python latex/compilar.py
  ```
