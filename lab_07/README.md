# Laboratorio 07: primalidad, grupos y algoritmos probabilísticos

**UNSAAC · Algoritmos Avanzados · 2026-II · Grupo 5**  
Docente: Ing. Héctor Eduardo Ugarte Rojas  
Integrantes: Choquenaira Quispe, Noe Franklin (133962); Porroa Sivana, Yeni Ruth (120893); Quispe Rimachi, Romario (164257); Yaranga Achahui, Aldo (103179).

Guía oficial: [`Guia 07.pdf`](Guia%2007.pdf). La entrega se organiza en código y experimentos (`python/`), informe (`latex/`) y un único cuaderno ejecutable (`colab/`).

## Estructura

```text
lab_07/
├── Guia 07.pdf
├── README.md / .gitignore
├── compilar_informe.bat / modo_en_vivo.bat
├── python/
│   ├── primality.py                 biblioteca principal y reportes auditables
│   ├── ejercicios_resueltos.py      tres ejercicios de la guía
│   ├── case_generator.py            datos y semillas reproducibles
│   ├── test_primality.py            32 pruebas unittest
│   ├── experiments.py              mediciones, CSV, PNG y tablas LaTeX
│   ├── verify_results.py           auditoría automática de los CSV y PNG
│   ├── render_resueltos.py         código y salidas reales para el informe
│   ├── render_propuesto1.py        tablas de casos y trazas desde los CSV
│   ├── build_notebook.py           generador antiguo (NO usar para el cuaderno inline)
│   ├── results/                   10 CSV auditables; respaldos locales opcionales
│   └── figures/                   4 gráficos PNG
├── latex/
│   ├── main.tex / main.pdf          informe modular y PDF compilado
│   ├── compilar.py / compilar.bat
│   ├── watch_live.py / iniciar_modo_en_vivo.bat
│   ├── figuras/                    escudo y figuras copiadas de python/figures
│   └── secciones/                  portada, código/salidas de los 3 resueltos,
│                                  2 propuestos, preguntas, tablas y conclusiones
└── colab/
    └── grupo 5 guia 07.ipynb       único archivo: código y salidas incrustados
```

## Ejecución local

Python **3.11+**; `matplotlib` para los gráficos locales y `pdflatex` para el informe. El Colab solo utiliza la biblioteca estándar y la visualización propia del cuaderno. Desde `lab_07`:

```powershell
python python/ejercicios_resueltos.py
python python/test_primality.py
python python/experiments.py
python python/verify_results.py
python latex/compilar.py
```

Para usar el cuaderno, abra **solo** `colab/grupo 5 guia 07.ipynb` en Colab o Jupyter con Python 3.11+ y ejecute todas las celdas en orden. Cada cálculo, tabla y gráfico se muestra bajo su celda, sin `%%writefile`, instalación de paquetes ni archivos auxiliares. La última celda ofrece opcionalmente un ZIP de evidencias generado en memoria. **No ejecute `python/build_notebook.py`: es un generador antiguo que sobrescribiría este cuaderno inline con otra organización.**

Los posibles respaldos de ejecuciones anteriores permanecen solo en la instalación local; no son parte de la entrega ni necesarios para ejecutar el `.ipynb`.

El generador experimental local sobrescribe únicamente los CSV, PNG y fragmentos de tablas autogenerados de este laboratorio. La compilación del informe ejecuta `render_resueltos.py` y `render_propuesto1.py` para insertar código, resultados, casos y trazas actuales. Tras cambiar experimentos, copie los PNG a `latex/figuras/` antes de compilar:

```powershell
Copy-Item python/figures/*.png latex/figuras/
python latex/compilar.py
```

## Alcance y rigor experimental

- Casos: 0, 1, 2, 3, pares, cuadrados de primos, 341, 561, 1105 y 1729. Los valores 0 y 1 no son primos **ni** compuestos.
- Validación: 32 pruebas; criba independiente hasta 10 000; 1000 aleatorios menores de `10^6` frente a división de prueba; bases válidas exhaustivas para compuestos impares de 5 a 199 y 221, 341, 561.
- Generación: `30 × 7 = 210` probables primos; 16 y 32 bits verificados además por división de prueba; los mayores **no** se consideran primalidad certificada.
- Comparación: mismas entradas y mismas 20 bases pre-generadas para Fermat y Miller–Rabin (1, 5, 10, 20 rondas); 8 probables primos y 8 compuestos construidos por tamaño; 7 mediciones por caso; división de prueba solo hasta 32 bits.
- `results/entradas_y_bases.csv` identifica los 20 valores de base usados por cada entrada; permite auditar y repetir cada fila de comparación.
- Semillas: generación `20260701`, comparación `20260702`, testigos y simulación `20260703`. Resultados y contadores reproducibles; los tiempos cambian según máquina/carga.
- Precribado activo durante generación; desactivado únicamente al comparar el costo de cada método sin sesgo de descarte temprano.
- Probabilidad: `4^-r` aplica a bases uniformes independientes para un compuesto impar. Una ejecución de semilla fija no hereda garantía criptográfica; `random.Random` solo para reproducir el laboratorio. La función sin `rng` usa `secrets.SystemRandom`.
- `cuadrados_modulares` cuenta operaciones efectivamente realizadas por la exponenciación binaria propia y por la cadena de Miller–Rabin. No interpreta el interior de `pow()`.
- En `results/tasa_error_empirica.csv`: tasa observada de 3000 simulaciones por caso, probabilidad exacta `(mentirosos/bases)^r` y cota universal `4^-r`. Cero errores observados **no** significa error imposible.

## Productos de la guía

Código de tres resueltos y dos propuestos; `primality.py`; pruebas; generador reproducible; CSV y gráficos; PDF con metodología, experimentos, doce respuestas y conclusiones grupales de 250–350 palabras. El archivo `latex/main.pdf` se genera a partir de los datos reales; el cuaderno Colab reproduce el flujo sin depender del informe local.

## 👥 Distribución del Trabajo por Integrante y Ramas Git

Para garantizar la trazabilidad individual y el trabajo en equipo exigido por la cátedra, el desarrollo del Laboratorio 07 se encuentra estructurado en 4 módulos distribuidos en sus respectivas ramas de GitHub:

| N.° | Integrante | Código | Rama Git | Módulo Asignado | Componentes y Archivos Principales |
| :---: | :--- | :---: | :---: | :--- | :--- |
| 1 | **Choquenaira Quispe, Noe Franklin** | 133962 | `lab07/franki-biblioteca` (`ramaFranki`) | **Biblioteca Central y Algoritmos de Primalidad** | `python/primality.py` (División de prueba, Fermat, Miller–Rabin con conteo de cuadrados, generación de probables primos e integración general en `main`). |
| 2 | **Porroa Sivana, Yeni Ruth** | 120893 | `lab07/yeni-pruebas` (`ramaYeni`) | **Casos Deterministas, Resueltos y Pruebas Unitarias** | `python/case_generator.py` (Semillas reproducibles), `python/ejercicios_resueltos.py` (Resueltos 1, 2 y 3) y `python/test_primality.py` (Suite de 32 pruebas automatizadas). |
| 3 | **Quispe Rimachi, Romario** | 164257 | `lab07/romario-experimentos` (`RamaRomario`) | **Batería Experimental, Mediciones y Auditoría** | `python/experiments.py` (Generación de 210 probables primos, comparaciones con 20 bases), `python/verify_results.py`, datasets en `results/` y figuras en `figures/`. |
| 4 | **Yaranga Achahui, Aldo** | 103179 | `lab07/aldo-informe-colab` (`ramaAldo`) | **Cuaderno Interactivo Colab e Informe Académico LaTeX** | `colab/grupo 5 guia 07.ipynb` (Cuaderno interactivo oficial con salidas inline y gráficos incrustados), `render_resueltos.py`, `render_propuesto1.py` e informe en `latex/` (`main.pdf`). |

---

## 🔄 Integración en la Rama `main`

El desarrollo modular de cada integrante fue verificado e integrado en la rama principal `main`, garantizando la reproducibilidad completa de todos los experimentos, la suite de 32 pruebas al 100% y la sincronización entre el informe académico y el cuaderno interactivo.
