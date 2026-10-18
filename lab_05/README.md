# Laboratorio 05: Splay Trees y Árboles Dinámicos Link-Cut

**Asignatura:** Algoritmos Avanzados (UNSAAC, Semestre 2026-II)  
**Docente:** Ing. Héctor Eduardo Ugarte Rojas  
**Equipo:** GRUPO 5  
**Integrantes:**
- Choquenaira Quispe, Noe Franklin (133962)
- Porroa Sivana, Yeni Ruth (120893)
- Quispe Rimachi, Romario (164257)
- Yaranga Achahui, Aldo (103179)

---

## 👥 Distribución del Trabajo por Integrante y Ramas Git

Para garantizar la trazabilidad individual y el trabajo en equipo exigido por la cátedra, el desarrollo del Laboratorio 05 se encuentra dividido en 4 módulos distribuidos en sus respectivas ramas de GitHub:

| N.° | Integrante | Código | Rama Git | Módulo Asignado | Componentes y Archivos Principales |
| :---: | :--- | :---: | :---: | :--- | :--- |
| 1 | **Choquenaira Quispe, Noe Franklin** | 133962 | `ramaFranki` | **Google Colab y Entorno Interactivo** | `lab_05/colab/` (Cuaderno `grupo 5 guia 05.ipynb` pre-ejecutado con salidas inline, generador `generate_lab05_notebook.py`, `colab/README.md`). |
| 2 | **Quispe Rimachi, Romario** | 164257 | `RamaRomario` | **Splay Trees y Ejercicios Resueltos** | `lab_05/codigo py/splay_tree.py`, `resuelto_01_splay_instrumentado.py`, `resuelto_02_splay_operaciones.py`, `visualizacion_splay.py`, figuras Splay. |
| 3 | **Porroa Sivana, Yeni Ruth** | 120893 | `ramaYeni` | **Link-Cut Trees y Pruebas Unitarias** | `lab_05/codigo py/link_cut_tree.py`, `reference_forest.py`, `resuelto_03_bosque_referencia.py`, `propuesto_01_link_cut_tree.py`, `pruebas/`, figuras Link-Cut. |
| 4 | **Yaranga Achahui, Aldo** | 103179 | `ramaAldo` | **Experimentos, Benchmarks e Informe LaTeX** | `lab_05/codigo py/lab05_pipeline.py`, `propuesto_02_pruebas_experimentos.py`, `resultados/`, `trazas/`, `lab_05/latex/` (informe formal de 13 páginas APA 7), scripts de compilación. |

---

## 1. Estructura del Repositorio

El proyecto mantiene la misma organización modular y rigor de entrega del Laboratorio 04:

```text
lab_05/
├── Guia 05.pdf                   # Guía oficial de laboratorio
├── compilar_informe.bat          # Compila el informe LaTeX a PDF con un clic
├── modo_en_vivo.bat              # Modo de compilación continua en vivo
├── README.md                     # Documento de descripción general
├── codigo py/                    # Código fuente en Python 3.12+
│   ├── splay_tree.py             # Splay Tree con split, join y rotaciones O(1)
│   ├── reference_forest.py       # Bosque dinámico BFS para pruebas diferenciales
│   ├── link_cut_tree.py          # Bosque Link-Cut completo con agregación path_sum
│   ├── visualizations.py         # Visualizador didáctico paso a paso de splay y EXPOSE
│   ├── lab05_pipeline.py         # Suite experimental, determinista y benchmarks
│   ├── resuelto_01_splay_instrumentado.py
│   ├── resuelto_02_splay_operaciones.py
│   ├── resuelto_03_bosque_referencia.py
│   ├── propuesto_01_link_cut_tree.py
│   ├── propuesto_02_pruebas_experimentos.py
│   ├── visualizacion_splay.py
│   ├── visualizacion_expose.py
│   ├── ejecutar_todo.py          # Script maestro unificado
│   ├── ejecutar_todos.bat        # Acceso directo para ejecutar todo
│   ├── pruebas/                  # Suite de pruebas unitarias automatizadas (unittest)
│   ├── figuras/                  # Gráficos estadísticos y paneles visuales en alta resolución
│   ├── resultados/               # Tablas en formato CSV y manifiesto de evidencias
│   └── trazas/                   # Trazas JSONL con secuencias reproducibles (semilla 2026)
├── colab/                        # Cuaderno Google Colab autónomo y autosuficiente
│   ├── grupo 5 guia 05.ipynb     # Cuaderno Jupyter con todas las celdas y gráficos inline
│   ├── generate_lab05_notebook.py# Generador determinista del cuaderno
│   └── README.md                 # Guía para abrir y ejecutar en Google Colab
└── latex/                        # Código fuente del informe académico en LaTeX (13 páginas)
    ├── main.tex                  # Documento principal (Times, A4, márgenes 2.54 cm)
    ├── main.pdf                  # Informe PDF final compilado (13 páginas exactas)
    ├── compilar.py               # Compilador multi-paso inteligente
    ├── compilar.bat              # Acceso directo local de compilación
    ├── watch_live.py             # Monitor de compilación en tiempo real
    ├── figuras/                  # Figuras y escudo institucional para compilación
    ├── rendered_preview/         # Capturas de las 13 páginas del informe
    └── secciones/                # Capítulos modulares del informe (portada, resueltos, propuestos, etc.)
```

---

## 2. Instrucciones de Ejecución

### Pruebas Unitarias
```bash
cd "codigo py"
python -m unittest discover -s pruebas -p "test_*.py" -v
```

### Ejecución Completa de Experimentos y Generación de Evidencias
```bash
cd "codigo py"
python ejecutar_todo.py
```
O simplemente doble clic en `codigo py/ejecutar_todos.bat`.

### Compilación del Informe en PDF
```bash
python latex/compilar.py
```
O simplemente doble clic en `compilar_informe.bat`.
El informe PDF se generará en `latex/main.pdf`.
