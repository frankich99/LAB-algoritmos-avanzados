# Cuaderno Interactivo y Código Experimental - Laboratorio 06
**Asignatura:** Algoritmos Avanzados (UNSAAC, Semestre 2026-II)  
**Tema:** Algoritmos Fundamentales de Teoría de Números  
**Docente:** Ing. Héctor Eduardo Ugarte Rojas  
**Equipo:** GRUPO 5  
**Integrantes:**
* Choquenaira Quispe, Noe Franklin (133962)
* Porroa Sivana, Yeni Ruth (120893)
* Quispe Rimachi, Romario (164257)
* Yaranga Achahui, Aldo (103179)

---

## 1. Contenido de esta Carpeta

* **`grupo 5 guia 06.ipynb`**: Cuaderno interactivo Jupyter / Google Colab oficial con **todas las celdas preparadas y ejecutadas**, autónomo, con salidas de consola completas, gráficos comparativos incrustados y suite de pruebas unitarias.

---

## 2. Instrucciones de Ejecución en Google Colab

1. Ingresar a [Google Colab](https://colab.research.google.com/).
2. Ir a la pestaña **Subir** (*Upload*) y seleccionar `grupo 5 guia 06.ipynb`.
3. En la barra superior, hacer clic en **Entorno de ejecución** $\to$ **Ejecutar todas** (`Ctrl + F9`).
4. El cuaderno recrea los módulos modulares (`number_theory.py`, `case_generator.py`, `test_number_theory.py`, `experiments.py`), ejecuta las 34 pruebas unitarias automatizadas y genera los 3 escenarios experimentales (A, B y C) en aproximadamente 2 a 3 minutos.
5. No requiere instalar dependencias adicionales en Colab: utiliza la biblioteca estándar (`math`, `time`, `statistics`, `csv`, `secrets`), `matplotlib` y `pandas`.

### Sobre el mensaje `Overwriting`

Al ejecutar nuevamente el cuaderno, las celdas que empiezan con
`%%writefile` muestran mensajes como `Overwriting test_number_theory.py`.
Esto solo indica que Colab está regenerando el archivo auxiliar con el contenido
actualizado de la celda; no es un error ni el resultado de una prueba.

Los resultados aparecen en la celda siguiente en un resumen ordenado: estado
general, cantidad de pruebas, fallos, errores y desglose por tema. Si aparece
un problema, solo se muestran los casos que requieren revisión. Por tanto, no
se crea un archivo distinto por cada caso: todos los casos forman parte de la
misma suite `test_number_theory.py`.
