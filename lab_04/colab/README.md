# Cuaderno Interactivo y Código Experimental - Laboratorio 04
**Asignatura:** Algoritmos Avanzados (UNSAAC, Semestre 2026-II)  
**Tema:** Montículos de Fibonacci y Análisis Amortizado  
**Docente:** Ing. Héctor Eduardo Ugarte Rojas  
**Equipo:** GRUPO 5  

---

## 1. Contenido de esta Carpeta

* **`grupo 5 guia 04.ipynb`**: Cuaderno interactivo Jupyter / Google Colab oficial con **todas las celdas ya ejecutadas**, salidas de consola completas y gráficos analíticos incrustados.
* **`generate_lab04_notebook.py`**: Script en Python puro para recrear o validar el cuaderno de forma estructurada y automatizada.
* **`ejecutar_experimentos_lab04.py`**: Motor experimental independiente para reproducir los benchmarks de consola y regenerar las tablas CSV y figuras.
* **`figuras/`**: Gráficos generados en alta resolución (DPI 200/300):
  * `fig_propuesto_1_potencial.png`: Dinámica del potencial $\Phi(H) = t(H) + 2m(H)$ y balance contable de costo real frente a amortizado.
  * `fig_escenario_a_tiempos.png`: Tiempos de inserción y extracción frente a $n$.
  * `fig_escenario_b_disminuciones.png`: Tiempo de cómputo frente a $q = 10n$ disminuciones de clave sobre elementos activos.
  * `fig_escenario_b_tamano_heapq.png`: Inflación del tamaño físico en `heapq` por acumulación de entradas obsoletas frente a entradas activas.
  * `fig_escenario_c_dijkstra.png`: Tiempos de ejecución en Dijkstra diferenciando grafos dispersos ($3|V|$) e intermedios ($10|V|$).
* **`resultados/`**: Tablas en formato CSV y resumen ejecutivo:
  * `tabla_escenario_a.csv`: Tiempos de inserción y extracción para $n \in \{1\,000, 5\,000, 10\,000, 25\,000\}$ con 10 repeticiones estadísticas.
  * `tabla_escenario_b.csv`: Carga intensiva de disminuciones válidas ($q = 10n$), estadísticas de cortes, cascadas y sobrecosto físico en memoria.
  * `tabla_dijkstra.csv`: Tiempos de Dijkstra y validación de distancias 100% concordantes.
  * `resumen_ejecucion.txt`: Métricas globales, especificaciones de hardware (OS, CPU, RAM) y confirmación del 100% de invariantes y aserciones.
* **`resultados_lab04.zip`**: Paquete comprimido con todas las evidencias para la entrega del laboratorio.

---

## 2. Instrucciones para Google Colab

1. Ingresar a [Google Colab](https://colab.research.google.com/).
2. Ir a la pestaña **Subir** (*Upload*) y seleccionar `grupo 5 guia 04.ipynb`.
3. En la barra superior, hacer clic en **Entorno de ejecución** $\to$ **Ejecutar todas** (`Ctrl + F9`).
4. La totalidad de las pruebas de invariantes, los 3 escenarios experimentales (A, B y C) y la generación de gráficos se completan en aproximadamente 30 a 60 segundos sin necesidad de instalar librerías externas adicionales.
5. Al finalizar la última celda, se descargará automáticamente el archivo `resultados_lab04.zip` con las evidencias generadas.
6. La constante `SEMILLA_GLOBAL = 2026` asegura que las entradas, secuencias de operaciones y métricas estructurales (enlaces, cortes, grados y distancias de Dijkstra) son $100\%$ idénticas y reproducibles, mientras que los tiempos de ejecución de CPU se reportan mediante medidas de dispersión estadística (mediana, mínimo y máximo).
