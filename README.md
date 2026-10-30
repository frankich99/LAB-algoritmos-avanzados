# UNSAAC - Algoritmos Avanzados (2026-II)

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![LaTeX](https://img.shields.io/badge/LaTeX-pdflatex-green?logo=latex&logoColor=white)
![UNSAAC](https://img.shields.io/badge/UNSAAC-Informatica%20y%20Sistemas-red)
![Status](https://img.shields.io/badge/Status-Activo-success)
![License](https://img.shields.io/badge/License-MIT-green)

**Universidad Nacional de San Antonio Abad del Cusco**  
*Facultad de Ingeniería Eléctrica, Electrónica, Informática y Mecánica*  
*Escuela Profesional de Ingeniería Informática y de Sistemas*

</div>

---

## 📌 Presentación del Repositorio

Este repositorio contiene el desarrollo completo, experimental y riguroso de las guías de laboratorio de la asignatura **Algoritmos Avanzados** (Semestre Académico 2026-II), a cargo del docente **Dr. Héctor Eduardo Ugarte Rojas**.

Cada laboratorio incluye:
* 📄 **Guías oficiales e informes técnicos:** Documentos formales en PDF generados con tipografía APA 7, índices interactivos completos (TOC, LOF, LOT y marcadores PDF) y paquetes compatibles con Overleaf.
* 🐍 **Implementaciones en Python desacopladas:** Código estructurado, tipado y modular listo para ejecución local o en la nube.
* 📓 **Notebooks interactivos reproducibles:** Cuadernos `.ipynb` ejecutables en JupyterLab, VS Code y Google Colab.
* 🧪 **Baterías experimentales y casos límite:** Verificación rigurosa de cotas matemáticas, razones de aproximación, invariantes y garantías teóricas.
* 📊 **Evidencia empírica respaldada:** Gráficos estadísticos en alta resolución y tablas de resultados en formato CSV.

---

## 👥 Integrantes del Equipo (Grupo 5)

| N.° | Apellidos y Nombres | Código | Correo Institucional |
| :---: | :--- | :--- | :--- |
| 1 | Choquenaira Quispe, Noe Franklin | 133962 | `133962@unsaac.edu.pe` |
| 2 | Porroa Sivana, Yeni Ruth | 120893 | `120893@unsaac.edu.pe` |
| 3 | Quispe Rimachi, Romario | 164257 | `164257@unsaac.edu.pe` |
| 4 | Yaranga Achahui, Aldo | 103179 | `103179@unsaac.edu.pe` |

---

## 📋 Resumen de Laboratorios Desarrollados

| Laboratorio | Tema Central | Algoritmos y Métodos | Garantías / Cotas |
| :---: | :--- | :--- | :--- |
| **Lab 01** | Complejidad y Análisis Empírico | Búsquedas, ordenamientos, Subset Sum recursivo vs. poda | Análisis asintótico y tiempos reales |
| **Lab 02** | Scheduling en Máquinas Paralelas ($Pm \parallel C_{\max}$) | List Scheduling (LS), Longest Processing Time (LPT), Branch & Bound exacto | Cota de Graham: $r \le 2 - \frac{1}{m}$ (LS) y $r \le \frac{4}{3} - \frac{1}{3m}$ (LPT) |
| **Lab 03** | Aproximación Avanzada: Vertex Cover y FPTAS | Algoritmo 2-Aproximado por Matching Maximal, DP por Valores, Knapsack FPTAS con escalamiento $K = \frac{\varepsilon V_{\max}}{n}$ | Vertex Cover: $|C| \le 2\,\text{OPT}$<br>FPTAS: $\text{ALG}_\varepsilon \ge (1-\varepsilon)\,\text{OPT}$, $O(n^3/\varepsilon)$ |
| **Lab 04** | Montículos de Fibonacci y Análisis Amortizado | Montículo de Fibonacci con punteros circulares, consolidación por grados, cortes en cascada, `heapq` perezoso y Dijkstra | Potencial: $\Phi(H) = t(H) + 2m(H)$<br>`insert`: $O(1)$, `decrease-key`: $O(1)$, `extract-min`: $O(\log n)$<br>Dijkstra: $O(|E| + |V|\log |V|)$ |
| **Lab 05** | Splay Trees y Árboles Dinámicos Link-Cut | Splay Tree autoajustable, partición en caminos preferidos, Link-Cut Forest con punteros virtuales (*path-parent*), reversión perezosa, sumas de camino | Potencial Sleator-Tarjan: $O(\log n)$ amortizado por operación<br>9 invariantes estructurales validadas al 100%<br>15,000 operaciones diferenciales con 0 discrepancias frente a BFS |
| **Lab 06** | Algoritmos de Teoría de Números y Aritmética Modular | MCD Euclides clásico y extendido ($ax+by=d$), Inversos modulares, Congruencias lineales, Exponenciación binaria modular ($O(\log b)$) y Teorema Chino del Resto (TCR) analítico con traza | Teorema de Lamé: $k \le 5\log_{10}(\min(a,b)) + 1$<br>Bezout: $ax \equiv d \pmod m$<br>Potencia rápida: $\le 2\lfloor\log_2 b\rfloor$ mults vs $b-1$<br>TCR: solución única $\pmod M$ con $\gcd(m_i, m_j)=1$ |
| **[Lab 07](lab_07/)** | Primalidad y algoritmos probabilísticos | División de prueba, Fermat, Miller–Rabin, generación y experimentos | Error de Miller–Rabin $\le 4^{-r}$ para compuestos impares con bases uniformes independientes; 210 probables primos y 928 comparaciones auditadas |

---

## 📂 Estructura del Repositorio

```text
UNSAAC-algoritmos-avanzados/
│
├── lab_01/                                     # Laboratorio 01: Complejidad y Experimentación
│   ├── Guia 01.pdf                             # Guía oficial del laboratorio
│   ├── INFORME_Y_GUIA_EJECUCION.md             # Informe técnico detallado
│   ├── README.md                               # Documentación rápida del Lab 01
│   ├── Laboratorio_01_Grupo5.ipynb             # Notebook Jupyter reproducible
│   ├── ejecutar_todo.py                        # Script maestro de ejecución (Python)
│   ├── ejecutar_todo.bat                       # Ejecución directa en Windows (Batch)
│   ├── resuelto_*.py                           # Ejercicios resueltos (Crecimiento, Búsquedas, Subset Sum)
│   ├── propuesto_*.py                          # Ejercicios propuestos (Ordenamientos, Límite exponencial)
│   ├── *.png                                   # Figuras generadas automáticamente
│   └── *.csv / *.json                          # Resultados experimentales exportados
│
├── lab_02/                                     # Laboratorio 02: Scheduling en Máquinas Paralelas (Pm || Cmax)
│   ├── Guia 02.pdf                             # Guía oficial del laboratorio
│   ├── informe_GUIA_02.pdf                     # Informe técnico final
│   ├── informe_GUIA_02.zip                     # Fuentes completas en LaTeX (.tex)
│   ├── README.md                               # Documentación técnica y suite de pruebas del Lab 02
│   ├── colab/                                  # Notebook para Google Colab
│   └── codigo py/                              # Suite modular de 14 scripts
│       ├── ejecutar_todo.py                    # Ejecutor maestro de los 14 scripts
│       ├── 01 a 03 (algoritmos)                # List Scheduling, LPT, Branch & Bound
│       ├── 04_pruebas_factibilidad.py          # Suite de pruebas unitarias y casos límite (300 instancias)
│       ├── 05 a 14 (experimentos)              # Complejidad, cotas de Graham, escalabilidad y dominancia
│       ├── figuras/                            # Gráficos en alta resolución
│       └── resultados/                         # Archivos CSV con métricas empíricas + instancias.json
│
├── lab_03/                                     # Laboratorio 03: Vertex Cover, PTAS y FPTAS
│   ├── Guia 03.pdf                             # Guía oficial del laboratorio
│   ├── compilar_informe.bat                    # Compilación automática del informe con 1 solo clic
│   ├── modo_en_vivo.bat                        # Compilador vigilante en tiempo real (Ctrl + S)
│   │
│   ├── codigo y notebook de lab_03/            # Código y experimentación empírica
│   │   ├── grupo 5 guia 03.ipynb               # Notebook interactivo oficial (Jupyter y Colab)
│   │   ├── generate_lab03_notebook.py          # Generador y ejecutor de la suite experimental completa
│   │   ├── README.md                           # Documentación de la suite de código
│   │   ├── resultados_lab03.zip                # Respaldo completo de resultados
│   │   ├── figuras/                            # Figuras individuales y paneles consolidados
│   │   └── resultados/                         # Datasets de salida (CSV y resumen)
│   │
│   └── informe pdf de lab_03/                  # Informe académico formal en LaTeX (APA 7)
│       ├── main.tex                            # Archivo maestro central
│       ├── main.pdf                            # Documento PDF único y definitivo
│       ├── informe_overleaf.zip                # Paquete modular listo para Overleaf
│       ├── compilar.bat / compilar.py          # Script de compilación multi-pasada
│       ├── iniciar_modo_en_vivo.bat            # Auto-compilación continua
│       ├── figuras/                            # Gráficos y escudo institucional de la UNSAAC
│       └── secciones/                          # Estructura modular correlativa
│
├── lab_04/                                     # Laboratorio 04: Montículos de Fibonacci y Análisis Amortizado
│   ├── Guia 04.pdf                             # Guía oficial del laboratorio
│   ├── compilar_informe.bat                    # Compilador directo del informe PDF
│   ├── modo_en_vivo.bat                        # Compilador en tiempo real con recarga continua
│   │
│   ├── colab/                                  # Entorno para Google Colab y Jupyter
│   │   ├── grupo 5 guia 04.ipynb               # Cuaderno interactivo con salidas incrustadas
│   │   ├── README.md                           # Guía de ejecución en la nube
│   │   └── resultados_lab04.zip                # Paquete de evidencias y tablas
│   │
│   ├── codigo py/                              # Scripts en Python puro modulares
│   │   ├── resuelto_01_potencial.py            # Ejercicio Resuelto 1: Potencial y costo amortizado
│   │   ├── resuelto_02_consolidacion.py        # Ejercicio Resuelto 2: Consolidación por grado
│   │   ├── resuelto_03_heapq_perezoso.py       # Ejercicio Resuelto 3: Cola de prioridad heapq perezosa
│   │   ├── propuesto_01_fibonacci_heap.py      # Ejercicio Propuesto 1: FibonacciHeap, 8 invariantes y 7 pruebas
│   │   ├── propuesto_02_comparacion_dijkstra.py# Ejercicio Propuesto 2: Benchmarks A, B, C y Dijkstra
│   │   ├── ejecutar_todo.py                    # Ejecutor maestro de todos los ejercicios
│   │   ├── ejecutar_todos.bat                  # Lanzador batch para Windows
│   │   ├── generate_lab04_notebook.py          # Generador del cuaderno Jupyter
│   │   ├── figuras/                            # 5 gráficos generados en 300 DPI
│   │   └── resultados/                         # Tablas CSV de resultados y métricas
│   │
│   └── latex/                                  # Informe académico en LaTeX (APA 7)
│       ├── main.tex                            # Documento maestro
│       ├── main.pdf                            # PDF compilado final
│       ├── compilar.py / compilar.bat          # Compilador automatizado 2-pass
│       ├── watch_live.py / iniciar_*.bat       # Modo en vivo con debounce
│       ├── informe_overleaf.zip                # Paquete comprimido para Overleaf
│       ├── figuras/                            # Gráficos y escudo institucional
│       └── secciones/                          # Secciones del informe (00 a 05)
│
├── lab_05/                                     # Laboratorio 05: Splay Trees y Árboles Dinámicos Link-Cut
│   ├── Guia 05.pdf                             # Guía oficial del laboratorio
│   ├── compilar_informe.bat                    # Compilador directo del informe PDF
│   ├── modo_en_vivo.bat                        # Compilador continuo en tiempo real
│   ├── README.md                               # Documentación técnica completa de Lab 05
│   │
│   ├── colab/                                  # Entorno interactivo para Google Colab y Jupyter
│   │   ├── grupo 5 guia 05.ipynb               # Cuaderno interactivo oficial con 23 celdas pre-ejecutadas
│   │   ├── generate_lab05_notebook.py          # Script generador y pre-ejecutor del cuaderno
│   │   └── README.md                           # Instrucciones de uso en Google Colab
│   │
│   ├── codigo py/                              # Suite modular en Python 3.12 puro
│   │   ├── splay_tree.py                       # Clase SplayTree con rotaciones, splay, split y join
│   │   ├── reference_forest.py                 # Modelo BFS canónico (oráculo de pruebas)
│   │   ├── link_cut_tree.py                    # Implementación integral de LinkCutForest y 9 invariantes
│   │   ├── visualizations.py                   # Generador gráfico de figuras didácticas de splay y EXPOSE
│   │   ├── lab05_pipeline.py                   # Pipeline experimental completo (Escenarios A, B y C)
│   │   ├── ejecutar_todo.py                    # Ejecutor maestro de todo el laboratorio
│   │   ├── resuelto_*.py                       # Scripts ejecutables de ejercicios resueltos 1, 2 y 3
│   │   ├── propuesto_*.py                      # Scripts ejecutables de ejercicios propuestos 1 y 2
│   │   ├── figuras/                            # Figuras de alta resolución exportadas
│   │   ├── resultados/                         # Archivos CSV de métricas experimentales
│   │   └── trazas/                             # Logs de auditoría JSONL de secuencias diferenciales
│   │
│   └── latex/                                  # Informe académico formal en LaTeX (APA 7)
│       ├── main.tex                            # Documento maestro
│       ├── main.pdf                            # PDF compilado final (1341 KB)
│       ├── compilar.py / compilar.bat          # Compilador automatizado 2-pass
│       ├── watch_live.py / iniciar_*.bat       # Modo en vivo con debounce
│       ├── figuras/                            # 20 figuras de alta resolución y escudo UNSAAC
│       └── secciones/                          # Secciones modulares del informe (00 a 06)
│
├── labo_06/                                    # Laboratorio 06: Algoritmos de Teoría de Números y Aritmética Modular
│   ├── Guia 06.pdf                             # Guía oficial del laboratorio
│   ├── compilar_informe.bat                    # Compilador directo del informe PDF
│   ├── modo_en_vivo.bat                        # Compilador continuo en tiempo real
│   ├── README.md                               # Documentación técnica y matriz de integrantes de Lab 06
│   │
│   ├── colab/                                  # Entorno interactivo para Google Colab y Jupyter
│   │   ├── grupo 5 guia 06.ipynb               # Cuaderno interactivo oficial con salidas y gráficos inline
│   │   └── README.md                           # Guía para abrir y ejecutar en Google Colab
│   │
│   ├── python/                                 # Suite modular en Python 3.12 puro
│   │   ├── number_theory.py                    # Biblioteca central (MCD, Euclides Ext, congruencias, TCR)
│   │   ├── test_number_theory.py               # Suite automatizada de 34 pruebas unitarias
│   │   ├── ejercicios_resueltos.py             # Implementación de ejercicios resueltos 1, 2 y 3
│   │   ├── case_generator.py                   # Generador determinista de casos de prueba
│   │   ├── experiments.py                      # Batería experimental completa (Escenarios A, B y C)
│   │   ├── figures/                            # 4 figuras estadísticas de alta resolución (300 DPI)
│   │   └── results/                            # Tablas CSV de resultados experimentales y trazas
│   │
│   └── latex/                                  # Informe académico formal en LaTeX (APA 7, 17 páginas)
│       ├── main.tex                            # Documento maestro
│       ├── main.pdf                            # PDF compilado final (17 páginas, sin referencias)
│       ├── compilar.py / compilar.bat          # Compilador automatizado 2-pass con pdflatex
│       ├── watch_live.py / iniciar_*.bat       # Modo en vivo con debounce continuo
│       ├── figuras/                            # Gráficos empíricos y escudo institucional
│       └── secciones/                          # Secciones modulares del informe (00 a 06)
│
├── lab_07/                                     # Laboratorio 07 en la raíz, NO dentro de LABORATORIOS/
│   ├── README.md / Guia 07.pdf                 # Guía de ejecución y enunciado
│   ├── colab/grupo 5 guia 07.ipynb             # Único cuaderno: código, tablas y figuras inline
│   ├── python/                                 # Biblioteca, 32 pruebas, experimentos, CSV y PNG
│   └── latex/main.tex / latex/main.pdf         # Fuentes e informe compilado
│
├── .gitignore                                  # Exclusión de temporales y compilados
├── requirements.txt                            # Dependencias necesarias
└── README.md                                   # Documentación principal del repositorio
```

---

## 🚀 Requisitos e Instalación

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/frankich99/LAB-algoritmos-avanzados.git
   cd LAB-algoritmos-avanzados
   ```

2. **Requisitos de Python:**
   * Python 3.10 o superior.
   * Instalar dependencias:
     ```bash
     pip install -r requirements.txt
     ```

3. **Requisitos para compilar informes LaTeX (opcional):**
   * Distribución TeX (MiKTeX o TeX Live) con `pdflatex`.
   * Alternativamente, subir los archivos `informe_overleaf.zip` directamente a [Overleaf](https://www.overleaf.com).

---

## ⚡ Ejecución Rápida por Laboratorio

### Laboratorio 01: Complejidad Empírica
```bash
cd lab_01
python ejecutar_todo.py
```

### Laboratorio 02: Scheduling en Máquinas Paralelas
```bash
cd "lab_02/codigo py"
python ejecutar_todo.py
python 04_pruebas_factibilidad.py
```

### Laboratorio 03: Vertex Cover, PTAS y FPTAS
```bash
cd "lab_03/codigo y notebook de lab_03"
python generate_lab03_notebook.py
```
* **Compilar informe PDF:** Doble clic en `lab_03/compilar_informe.bat`.

### Laboratorio 04: Montículos de Fibonacci y Análisis Amortizado
```bash
cd "lab_04/codigo py"
python ejecutar_todo.py
```
* **Ejecución modular de ejercicios:**
  ```bash
  python resuelto_01_potencial.py
  python resuelto_02_consolidacion.py
  python resuelto_03_heapq_perezoso.py
  python propuesto_01_fibonacci_heap.py
  python propuesto_02_comparacion_dijkstra.py
  ```
* **Compilar informe PDF:** Doble clic en `lab_04/compilar_informe.bat` o `lab_04/modo_en_vivo.bat`.

### Laboratorio 05: Splay Trees y Árboles Dinámicos Link-Cut
```bash
cd "lab_05/codigo py"
python ejecutar_todo.py
```
* **Ejecución modular de ejercicios:**
  ```bash
  python resuelto_01_splay_instrumentado.py
  python resuelto_02_splay_operaciones.py
  python resuelto_03_bosque_referencia.py
  python propuesto_01_link_cut_tree.py
  python propuesto_02_pruebas_experimentos.py
  python visualizacion_splay.py
  python visualizacion_expose.py
  ```
* **Cuaderno interactivo oficial:** Abrir `lab_05/colab/grupo 5 guia 05.ipynb` en Google Colab o JupyterLab (23 celdas completamente pre-ejecutadas con gráficos y tablas inline).
* **Compilar informe PDF:** Doble clic en `lab_05/compilar_informe.bat` o `lab_05/modo_en_vivo.bat`.

### Laboratorio 06: Algoritmos Fundamentales de Teoría de Números
```bash
cd "labo_06/python"
python test_number_theory.py
python experiments.py
python ejercicios_resueltos.py
```
* **Cuaderno interactivo oficial:** Abrir `labo_06/colab/grupo 5 guia 06.ipynb` en Google Colab o JupyterLab (autónomo, con suite de 34 pruebas y gráficos inline).
* **Compilar informe PDF:** Doble clic en `labo_06/compilar_informe.bat` o `labo_06/modo_en_vivo.bat`.

### Laboratorio 07: Primalidad y algoritmos probabilísticos
La entrega está en **[`lab_07/`](lab_07/README.md)**, directamente en la raíz del repositorio. Consulte el [cuaderno con salidas](lab_07/colab/grupo%205%20guia%2007.ipynb) o el [informe PDF](lab_07/latex/main.pdf). El cuaderno funciona en Colab y Jupyter con Python 3.11+; ejecute sus celdas en orden, sin dependencias locales ni generadores auxiliares. **No ejecute `python/build_notebook.py`**: es un generador anterior que sobrescribe el cuaderno inline.

```bash
cd lab_07
python python/test_primality.py
python python/verify_results.py
python latex/compilar.py
```

Las ramas `lab07/franki-biblioteca`, `lab07/yeni-pruebas`, `lab07/romario-experimentos` y `lab07/aldo-informe-colab` organizan áreas de revisión. Son ramas preparadas para los integrantes, **no evidencia de autoría personal**; cada integrante deberá registrar allí sus propios cambios y commits.

---

## 🔬 Aspectos Teóricos Clave Evaluados en Lab 04, Lab 05 y Lab 06

### 1. Montículos de Fibonacci y Análisis Amortizado (Lab 04)
* **Función de Potencial Contable:** Definida como $\Phi(H) = t(H) + 2m(H)$, donde $t(H)$ es el número de árboles en la lista de raíces y $m(H)$ la cantidad de nodos internos marcados.
* **Compensación de Reestructuraciones:** Cada inserción aporta $+1$ de potencial que amortiza los enlaces durante la consolidación de `extract-min`. Cada nodo marcado acumula $+2$, financiando su corte futuro y desmarcado cuando sufre un corte en cascada ($\Delta \Phi = -1$).
* **Cotas Garantizadas:**
  $$\hat{c}_{\text{insert}} \in O(1), \quad \hat{c}_{\text{union}} \in O(1), \quad \hat{c}_{\text{decrease-key}} \in O(1), \quad \hat{c}_{\text{extract-min}} \in O(\log n)$$

### 2. Splay Trees y Bosques Dinámicos Link-Cut (Lab 05)
* **Descomposición en Caminos Preferidos y Árboles Auxiliares:** El bosque representado se particiona en caminos dirigidos disjuntos en vértices. Cada camino se almacena en un Splay Tree auxiliar cuyo recorrido *in-order* preserva la profundidad relativa de menor a mayor.
* **Punteros Virtuales (*path-parent*):** El puntero `parent` cumple un doble papel fundamental: enlaza nodos dentro del árbol auxiliar y, cuando el padre no reconoce al nodo como hijo (`_is_aux_root`), actúa como conexión virtual hacia el árbol auxiliar superior en el bosque representado.
* **Operación `EXPOSE(v)` y Cota Amortizada $O(\log n)$:** Reconfigura las aristas preferidas para conectar el camino desde la raíz representada hasta $v$ en un único árbol auxiliar con $v$ en su raíz auxiliar. Mediante el análisis potencial de Sleator-Tarjan, cualquier secuencia válida de operaciones sobre el Link-Cut Forest (`link`, `cut`, `connected`, `path_sum`, `make_root`) posee costo amortizado $O(\log n)$.
* **Validación Diferencial Rigurosa:** Contrastación de **15,000 operaciones aleatorias** sobre grafos dinámicos frente a un oráculo canónico BFS (`ReferenceForest`), reportando **0 discrepancias** y garantizando la preservación estricta de **9 invariantes estructurales** en cada paso.

### 3. Teoría de Números, Aritmética Modular y Teorema Chino del Resto (Lab 06)
* **Algoritmo de Euclides Extendido e Identidad de Bézout:** Determina $d = \gcd(a, b)$ y los coeficientes enteros $x, y$ tales que $ax + by = d$. Si $d = 1$, $x$ representa el inverso multiplicativo modular $a^{-1} \pmod b$.
* **Cota de Lamé y Complejidad Logarítmica:** El número de divisiones del algoritmo de Euclides está acotado superiormente por $k \le 5\log_{10}(\min(a,b)) + 1$, alcanzándose el peor caso estrictamente en pares consecutivos de Fibonacci ($F_{k+1}, F_k$), donde todos los cocientes son $q_i = 1$.
* **Exponenciación Binaria Modular (*Square-and-Multiply*):** Reduce el cálculo de $a^b \pmod m$ de $b-1$ multiplicaciones a lo sumo $2\lfloor\log_2 b\rfloor$ multiplicaciones, manteniendo los operandos acotados mediante reducción modular en cada paso y permitiendo cómputos con exponentes de 1024 bits en microsegundos.
* **Teorema Chino del Resto (TCR) Analítico:** Resuelve sistemas de congruencias $x \equiv a_i \pmod{m_i}$ con módulos coprimos dos a dos mediante la construcción de bases ortogonales $e_i = M_i \cdot (M_i^{-1} \pmod{m_i})$, garantizando una solución única módulo $M = \prod m_i$.
