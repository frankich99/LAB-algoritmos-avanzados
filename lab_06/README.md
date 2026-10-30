# Laboratorio 06: Algoritmos Fundamentales de Teoría de Números
**Asignatura:** Algoritmos Avanzados (UNSAAC, Semestre 2026-II)  
**Docente:** Ing. Héctor Eduardo Ugarte Rojas  
**Equipo:** GRUPO 5  
**Integrantes:**
* Choquenaira Quispe, Noe Franklin (133962)
* Porroa Sivana, Yeni Ruth (120893)
* Quispe Rimachi, Romario (164257)
* Yaranga Achahui, Aldo (103179)

---

## 👥 Distribución del Trabajo por Integrante y Ramas Git

Para garantizar la trazabilidad individual y el trabajo en equipo exigido por la cátedra, el desarrollo del Laboratorio 06 se encuentra estructurado en 4 módulos distribuidos en sus respectivas ramas de GitHub:

| N.° | Integrante | Código | Rama Git | Módulo Asignado | Componentes y Archivos Principales |
| :---: | :--- | :---: | :---: | :--- | :--- |
| 1 | **Quispe Rimachi, Romario** | 164257 | `RamaRomario` | **Ejercicios Resueltos y Algoritmos Base** | `lab_06/python/ejercicios_resueltos.py` (Resueltos 1, 2 y 3: Euclides clásico vs extendido, inversos modulares y exponenciación modular). |
| 2 | **Porroa Sivana, Yeni Ruth** | 120893 | `ramaYeni` | **Biblioteca Central y Pruebas Unitarias** | `lab_06/python/number_theory.py` (MCD, Euclides extendido, congruencias, TCR analítico con traza) y `lab_06/python/test_number_theory.py` (Suite de 34 pruebas automatizadas). |
| 3 | **Yaranga Achahui, Aldo** | 103179 | `ramaAldo` | **Experimentos, Resultados e Informe LaTeX** | `lab_06/python/experiments.py`, `case_generator.py`, `results/`, `figures/` e informe LaTeX en `lab_06/latex/` (secciones 00 a 06, figuras, scripts de compilación). |
| 4 | **Choquenaira Quispe, Noe Franklin** | 133962 | `ramaFranki` | **Google Colab, Informe Final e Integración** | `lab_06/colab/` (Cuaderno `grupo 5 guia 06.ipynb` pre-ejecutado con salidas inline), `lab_06/latex/main.pdf` (17 páginas) e integración completa en `main`. |

---

## Estructura del Proyecto

```text
lab_06/
├── colab/
│   ├── grupo 5 guia 06.ipynb        # Cuaderno Google Colab con salidas y gráficos incrustados
│   └── README.md                    # Instrucciones de ejecución en la nube
├── latex/
│   ├── main.tex                     # Archivo raíz LaTeX estructurado bajo estándar APA 7
│   ├── main.pdf                     # Informe final compilado de alta calidad
│   ├── compilar.py                  # Script automatizado de compilación con pdflatex
│   ├── compilar.bat                 # Lanzador de compilación en Windows
│   ├── watch_live.py                # Servidor de compilación en tiempo real (auto-recompile)
│   ├── iniciar_modo_en_vivo.bat     # Lanzador del modo en vivo
│   ├── figuras/                     # Gráficos y diagramas vectoriales/PNG generados
│   │   ├── escudo.png
│   │   ├── fig1_euclides_divisiones.png
│   │   ├── fig2_potencia_operaciones.png
│   │   ├── fig3_directo_vs_binario.png
│   │   └── fig4_unos_tiempo.png
│   └── secciones/                   # Capítulos modulares del informe académico
│       ├── 00_portada.tex
│       ├── 01_trabajo_preparatorio.tex
│       ├── 02_ejercicios_resueltos.tex
│       ├── 03_propuesto_biblioteca_tcr.tex
│       ├── 04_propuesto_experimentos.tex
│       ├── 05_preguntas_analisis.tex
│       └── 06_conclusiones.tex
├── python/
│   ├── number_theory.py             # Biblioteca modular de teoría de números
│   ├── ejercicios_resueltos.py      # Implementación de los ejercicios resueltos 1, 2 y 3
│   ├── test_number_theory.py        # Suite de 34 pruebas unitarias y de propiedades
│   ├── case_generator.py            # Generador reproducible de casos de prueba
│   ├── experiments.py               # Módulo experimental para los escenarios A, B y C
│   ├── results/                     # Registros en CSV de experimentos y trazas
│   └── figures/                     # Gráficos generados
├── compilar_informe.bat             # Compilador rápido desde raíz
└── modo_en_vivo.bat                 # Modo en vivo desde raíz
```

---

## Verificación Rápida y Reproducibilidad

1. **Ejecutar Pruebas Automatizadas:**
   ```bash
   cd python
   python test_number_theory.py
   ```
2. **Ejecutar Batería de Experimentos:**
   ```bash
   cd python
   python experiments.py
   ```
3. **Compilar Informe en PDF:**
   ```bash
   cd latex
   python compilar.py
   ```
