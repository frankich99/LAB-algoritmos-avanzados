# Laboratorio 08 — FFT, polinomios y transformadas sobre campos finitos

UNSAAC · Algoritmos Avanzados · 2026-II · Grupo 5 · Guía oficial: [`Guia 08.pdf`](Guia%2008.pdf)

Docente: Héctor Eduardo Ugarte Rojas. Integrantes: Choquenaira Quispe, Noe Franklin
(133962); Porroa Sivana, Yeni Ruth (120893); Quispe Rimachi, Romario (164257);
Yaranga Achahui, Aldo (103179).

## Árbol de entrega

```text
lab_08/
├── Guia 08.pdf                  guía original, sin cambios
├── README.md / AREA_DE_REVISION.md / .gitignore
├── compilar_informe.bat         lanzador opcional Windows
├── python/
│   ├── transforms.py           biblioteca y contadores (FFT/NTT)
│   ├── case_generator.py       casos y semillas reproducibles
│   ├── ejercicios_resueltos.py tres ejercicios y NTT cuadrática de referencia
│   ├── test_transforms.py      pruebas unitarias y diferenciales
│   ├── experiments.py          escenarios A/B/C, mediciones y figuras
│   ├── verify_results.py       auditoría de evidencia
│   ├── render_report.py        fragmentos LaTeX desde código/CSV
│   ├── build_notebook.py       generador del único notebook autónomo
│   ├── results/               diez CSV
│   └── figures/               tres PNG (sin copias en latex/)
├── latex/
│   ├── main.tex / main.pdf     informe fuente + PDF final (20 páginas)
│   ├── compilar.py            validación, renderizado y pdflatex
│   ├── figuras/               escudo oficial UNSAAC y tres gráficos PNG
│   └── secciones/             portada, teoría, resueltos, biblioteca,
│                             experimentos, 12 preguntas y conclusiones
└── colab/
    └── grupo 5 guia 08.ipynb  único cuaderno autónomo con salidas inline
```

## Ejecución (desde `lab_08/`)

Python 3.11+; `matplotlib` para experimentos/Colab; `pdflatex` para informe;
`nbformat`, `nbclient`, `ipykernel` e `IPython` solo para generar/ejecutar el
cuaderno localmente. En Colab ya están disponibles las dependencias habituales.

```powershell
python python/ejercicios_resueltos.py
python python/test_transforms.py
python python/experiments.py --max-k 14 --repetitions 10
python python/verify_results.py
python latex/compilar.py
python python/build_notebook.py --execute
```

**Precaución:** `experiments.py` actualiza deliberadamente solo los diez CSV y
tres PNG de este laboratorio; los tiempos cambian con CPU, sistema y carga.
`render_report.py` actualiza solo `02_resueltos_generados.tex` y
`04_tablas_generadas.tex`. `build_notebook.py` actualiza solo el notebook de
`colab/`; **es el generador vigente**, no hay generador legado que sobrescriba
otro formato. Para abrir el notebook existente no hace falta ejecutar ningún
script ni subir archivos: `Runtime > Run all` genera los CSV, gráficos y ZIP
en un directorio temporal de la sesión.

## Decisiones matemáticas y experimentales

- Coeficientes ascendentes; `[]` para producto con entrada vacía; `[0,0]` no
  pierde su longitud. Longitud de salida `m+n-1`, padding a potencia de dos.
- FFT positiva `exp(2πi/N)` con IFFT por conjugación y `1/N`. FFT iterativa
  modifica la lista; `multiply_fft` crea copias antes de llamarla.
- Módulos: `17` con generador `3` para `N<=16` (raíz `4` de orden 4 en el
  ejercicio resuelto) y `998244353=119·2^23+1` con generador `3` para las
  longitudes grandes. `multiply_ntt` valida el generador y deriva la raíz de
  orden exacto `N`; `ntt` recibe directamente esa raíz.
- Una NTT entrega *residuos* exactos, no coeficientes enteros: para
  reconstrucción con signo y `|c_k|<=M` se requiere `p>2M` o varios módulos
  cuyo producto supere `2M` (CRT). No se presenta un resultado modular como
  entero si esta condición no se cumple.
- Contadores: cada mariposa cuenta dos multiplicaciones (factor y avance),
  dos sumas/restas; se incluyen productos punto a punto y escalado inverso.
  `etapas` suma las de las tres transformadas, no nodos recursivos. Se excluyen
  inversiones, `pow`, permutación de bits, asignaciones y preparación.
- Escenario A: tamaños 8–128 para tres rangos; semilla por caso. La FFT puede
  fallar para `[0,p-1]`: se **documenta** la discrepancia con entrada y salida
  en CSV, en vez de ocultarla. NTT se compara siempre módulo `p`.
- Escenario B: tamaños `2^3`–`2^14`; 10 repeticiones por método y caso; la
  directa se mide hasta `n=2048` (no se extrapolan mediciones). Se verifica
  equivalencia **antes** de cronometrar; durante la medición solo se ejecuta
  el método con entradas ya generadas. Se reporta min, mediana, max, semillas,
  CPU/sistema/Python y contadores.
- Escenario C: tamaños 8–1024 y magnitudes 10–10^9; se mide error real e
  imaginario antes de redondear, se registra el primer fallo y se verifica NTT
  módulo `p` contra la referencia entera en cada caso.

## Informe y cuaderno

El informe toma los resultados de los CSV actuales: el compilador audita la
evidencia, ejecuta los tres resueltos, genera las tablas en formato booktabs y compila `main.pdf`.
Las 12 preguntas están respondidas en profundidad en `latex/secciones/05_preguntas_analisis.tex`; las
conclusiones grupales (250–350 palabras) en `06_conclusiones.tex`. La carpeta `latex/figuras/` contiene
el escudo oficial de la UNSAAC y todas las gráficas analíticas del informe.

El cuaderno `colab/grupo 5 guia 08.ipynb` es completamente autónomo e interactivo:
- **Sin `%%writefile`:** cada celda contiene código ejecutable en Python puro y muestra sus salidas inmediatamente debajo (tablas HTML estilizadas, salidas estándar de unittest y gráficos vectoriales SVG de alta fidelidad).
- **Independiente de archivos locales:** mantiene los datasets y figuras en memoria (`DATASETS` y `CHARTS`), permitiendo su ejecución de principio a fin en Google Colab o Jupyter sin subir archivos ni instalar dependencias pesadas.
- **Estructura modular:** dividido en módulos lógicos que cubren preparación, convolución directa, FFT/IFFT compleja, NTT modular, tres ejercicios resueltos, suite de pruebas automatizadas, experimentos A/B/C y descarga de evidencias en ZIP.
