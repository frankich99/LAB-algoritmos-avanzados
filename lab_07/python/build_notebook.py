"""Genera el único cuaderno de entrega desde los módulos de python/.

Uso: python python/build_notebook.py [--execute]
La opción --execute requiere nbclient y un kernel python3 en el equipo local.
"""

import argparse
import tempfile
from pathlib import Path

import nbformat as nbf


SOURCE = Path(__file__).resolve().parent
OUTPUT = SOURCE.parent / "colab" / "grupo 5 guia 07.ipynb"


def markdown(text):
    return nbf.v4.new_markdown_cell(text)


def code(text):
    return nbf.v4.new_code_cell(text)


def module_parts(name, anchors=()):
    """Divide un módulo en celdas contiguas; %%writefile -a conserva el orden."""
    lines = (SOURCE / name).read_text(encoding="utf-8").splitlines(keepends=True)
    positions = [0]
    for anchor in anchors:
        matches = [i for i, line in enumerate(lines) if line.startswith(anchor)]
        if len(matches) != 1:
            raise ValueError(f"Ancla no única en {name}: {anchor}")
        positions.append(matches[0])
    if positions != sorted(set(positions)):
        raise ValueError(f"Anclas desordenadas en {name}")
    positions.append(len(lines))
    return [code(f"%%writefile {'-a ' if i else ''}{name}\n"
                 + "".join(lines[start:end]))
            for i, (start, end) in enumerate(zip(positions, positions[1:]))]


def create():
    primalidad = module_parts("primality.py", (
        "def decompose(", "def _presieve_divisor(", "def generate_candidate("))
    pruebas = module_parts("test_primality.py", (
        "class TestFermat(", "class TestMillerRabin(",
        "class TestPruebasRepetidas(", "class TestGeneracion("))
    experimentos = module_parts("experiments.py", (
        "def liars_and_error(", "def generate_primes(",
        "def compare_methods(", "def plot_timing(", "def latex_tables(", "def main("))
    cells = [
        markdown("# Guía de laboratorio 07 — Primalidad, grupos y algoritmos probabilísticos\n"
                 "**UNSAAC · Algoritmos Avanzados · 2026-II · Grupo 5**\n\n"
                 "**Integrantes:** Choquenaira Quispe, Noe Franklin (133962); "
                 "Porroa Sivana, Yeni Ruth (120893); Quispe Rimachi, Romario (164257); "
                 "Yaranga Achahui, Aldo (103179).\n\n"
                 "Ejecute **todas las celdas, desde el inicio**, en Google Colab o Jupyter "
                 "con Python 3.11+. El cuaderno contiene código, pruebas, resultados y "
                 "gráficos. No requiere archivos del repositorio: los módulos se crean "
                 "en un directorio temporal de la sesión, no junto a este `.ipynb`. "
                 "La celda inicial instala `matplotlib` y `pandas` solo si faltan."),
        markdown("## Preparación del entorno y fundamentos (guía, secciones 2–6)\n"
                 "Se usan `random.Random` y semillas fijas únicamente para reproducir "
                 "experimentos. La generación sin semilla utiliza `secrets.SystemRandom`; "
                 "una prueba superada no certifica primalidad de enteros grandes. "
                 "Una base que rechaza en Fermat o Miller–Rabin prueba composición. "
                 "La cota $4^{-r}$ supone un compuesto impar y $r$ bases independientes "
                 "uniformes. La división de prueba es determinista pero necesita hasta "
                 "$O(2^{L/2})$ divisiones para entradas de $L$ bits."),
        code("import importlib.util, os, platform, subprocess, sys, tempfile\n"
             "from pathlib import Path\n"
             "if sys.version_info < (3, 11):\n"
             "    raise RuntimeError('La Guía 07 requiere Python 3.11 o posterior. Cambie el kernel.')\n"
             "missing = [p for p in ('matplotlib', 'pandas') if importlib.util.find_spec(p) is None]\n"
             "if missing:\n"
             "    print('Instalando dependencias faltantes:', ', '.join(missing))\n"
             "    subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing])\n"
             "import matplotlib, pandas\n"
             "# Los archivos de la ejecución no modifican la carpeta del cuaderno.\n"
             "# Al repetir 'Ejecutar todas', conservamos la sesión previa hasta cerrar el kernel.\n"
             "if 'session' in globals():\n"
             "    session_history = globals().get('session_history', [])\n"
             "    session_history.append(session)\n"
             "    sys.path = [p for p in sys.path if p != str(WORK)]\n"
             "    for name in ('primality', 'case_generator', 'ejercicios_resueltos',\n"
             "                 'test_primality', 'experiments', 'verify_results'):\n"
             "        sys.modules.pop(name, None)\n"
             "session = tempfile.TemporaryDirectory(prefix='lab07_')\n"
             "WORK = Path(session.name)\n"
             "os.chdir(WORK)\n"
             "sys.path.insert(0, str(WORK))\n"
             "print('Entorno listo:', platform.python_version(), '| matplotlib', "
             "matplotlib.__version__, '| pandas', pandas.__version__)"),
        markdown("## 8. Ejercicios resueltos — biblioteca compartida\n"
                 "Primero se definen las funciones usadas en los tres casos de la guía. "
                 "Cada celda agrega una parte a `primality.py`; no se necesita subir "
                 "ningún módulo. Las funciones se comprueban por separado más abajo."),
        markdown("### 8.1 División de prueba y Fermat\n"
                 "La división llega hasta `isqrt(n)`; Fermat usa bases válidas y "
                 "comprueba coprimalidad."),
        primalidad[0],
        markdown("### 8.2 Descomposición y ronda Miller–Rabin\n"
                 "Se registran $n$, base, $s$, $d$, residuos y cuadrados modulares."),
        primalidad[1],
        markdown("### 8.3 Rondas repetidas y precribado\n"
                 "El informe distingue compuesto, primo pequeño certificado y "
                 "probable primo con número de rondas y cota condicional."),
        primalidad[2],
        markdown("### Biblioteca compartida: candidatos y clasificación de bases\n"
                 "Se añaden candidatos impares de longitud exacta, búsqueda con "
                 "precribado y clasificación exhaustiva de bases pequeñas."),
        primalidad[3],
        markdown("### 8.1–8.3 Código ejecutable de los tres resueltos"),
        *module_parts("ejercicios_resueltos.py"),
        markdown("#### Resuelto 1: división de prueba y Fermat\n"
                 "341 = 11 × 31 supera Fermat con base 2, pero es compuesto."),
        code("from ejercicios_resueltos import resuelto_1, resuelto_2, resuelto_3\n"
             "resuelto_1()"),
        markdown("#### Resuelto 2: Miller–Rabin con traza (221, base 2)\n"
                 "$220=2^2\\cdot55$; residuos esperados $[128,30]$."),
        code("resuelto_2()"),
        markdown("#### Resuelto 3: cinco rondas sobre 1009 y candidato de 32 bits\n"
                 "1009 no se acepta por precribado: se ejecutan realmente cinco "
                 "rondas. Semilla 2026 solo para reproducir el ejemplo, no para claves."),
        code("resuelto_3()"),
        markdown("## 9.1 Validación de la biblioteca\n"
                 "Las pruebas comprueban casos especiales, todas las bases válidas "
                 "de primos pequeños, una criba independiente y 1000 aleatorios "
                 "menores que $10^6$ frente a división de prueba."),
        *module_parts("case_generator.py"),
        markdown("### Pruebas de división y Fermat"),
        pruebas[0], pruebas[1],
        markdown("### Pruebas de Miller–Rabin y trazas"),
        pruebas[2],
        markdown("### Pruebas de rondas, cotas y reproducibilidad"),
        pruebas[3],
        markdown("### Pruebas de generación de 16 a 1024 bits"),
        pruebas[4],
        code("import unittest, test_primality\n"
              "suite = unittest.defaultTestLoader.loadTestsFromModule(test_primality)\n"
              "outcome = unittest.TextTestRunner(verbosity=1).run(suite)\n"
              "assert outcome.wasSuccessful(), 'Fallaron las pruebas automatizadas'"),
        markdown("### 9.1 Evidencia de clasificación de cada base\n"
                 "Para el compuesto 25 se muestran todas las bases válidas: una base "
                 "mentirosa fuerte no transforma al compuesto en primo."),
        code("import pandas as pd\nfrom IPython.display import Image, display\n"
             "from primality import classify_bases\n"
             "clasificacion = classify_bases(25)\n"
             "display(pd.DataFrame([{'n': 25, 'base': a,\n"
             "                       'clase': 'mentiroso_fuerte' if a in clasificacion['mentirosos_fuertes'] "
             "else 'testigo'} for a in range(2, 24)]))"),
        markdown("## 9.2 Ejercicio propuesto 2: comparación experimental\n"
                 "### Metodología de medición (sección 10 de la guía)\n"
                 "Entradas y 20 bases por entrada se preparan antes de medir. Se usan "
                 "siete repeticiones sin imprimir ni escribir archivos durante el "
                 "intervalo cronometrado. Semillas: 20260701, 20260702, 20260703. "
                 "Se generan 30 probables primos por cada una de siete longitudes; "
                 "la división de prueba solo se cronometra hasta 32 bits."),
        markdown("### Código del experimento: casos, trazas y medición"),
        experimentos[0],
        markdown("### Código del experimento: bases testigo y tasa de error"),
        experimentos[1],
        markdown("### Código del experimento: generación de 210 candidatos aceptados"),
        experimentos[2],
        markdown("### Código del experimento: comparación con bases compartidas"),
        experimentos[3],
        markdown("### Código del experimento: cuatro gráficos construidos desde los datos"),
        experimentos[4],
        markdown("### Código del experimento: siete fragmentos LaTeX reproducibles"),
        experimentos[5], experimentos[6],
        markdown("## 11. Resultados: casos conocidos y trazas (propuesto 1)\n"
                 "La ronda de Miller–Rabin rechaza a 221, 341 y 561 con base 2. "
                 "Las tablas siguientes se crean en esta misma celda."),
        code("import experiments as exp\n"
             "for folder in (exp.RESULTS, exp.FIGURES, exp.LATEX):\n"
             "    folder.mkdir(parents=True, exist_ok=True)\n"
             "casos, trazas = exp.known_and_traces()\n"
             "display(pd.DataFrame(casos))\n"
             "display(pd.DataFrame(trazas).query('n in [221, 341, 561]'))"),
        markdown("### Generación: 30 probables primos por longitud\n"
                 "La tabla aparece inmediatamente después del código. Los de 16 y 32 "
                 "bits se validan además con división de prueba."),
        code("primes_by_bits, generation = exp.generate_primes()\n"
             "display(pd.DataFrame(generation))"),
        markdown("### Figura 3: candidatos necesarios frente a bits"),
        code("exp.plot_candidates(generation)\n"
             "display(Image(filename='figures/fig3_candidatos_vs_bits.png'))"),
        markdown("### Comparación: Fermat, Miller–Rabin y división de prueba\n"
                 "Se muestran los tiempos medianos por método y una muestra con "
                 "mínimo, mediana, máximo, rondas y cuadrados."),
        code("comparison_rows, comparison = exp.compare_methods(primes_by_bits)\n"
             "display(pd.DataFrame(comparison).query(\"tipo_entrada != 'compuesto_construido'\")"
             ".pivot(index='bits', columns=['metodo', 'rondas'], values='tiempo_mediano_us'))\n"
             "display(pd.DataFrame(comparison_rows).query("
             "\"bits == 16 and indice == 0 and tipo_entrada == 'primo_verificado'\")"
             "[['metodo', 'rondas_solicitadas', 'rondas_ejecutadas', "
             "'cuadrados_modulares', 'min_ns', 'mediana_ns', 'max_ns', 'resultado']])"),
        markdown("### Figura 1: tiempo por longitud binaria"),
        code("exp.plot_timing(comparison)\n"
             "display(Image(filename='figures/fig1_tiempo_vs_bits.png'))"),
        markdown("### Figura 2: cuadrados modulares y rondas"),
        code("exp.plot_squares(comparison)\n"
             "display(Image(filename='figures/fig2_cuadrados_vs_bits.png'))"),
        markdown("### Testigos, mentirosos fuertes y frecuencia de error\n"
                 "La tasa empírica se compara con la tasa exacta para cada compuesto "
                 "y la cota teórica universal."),
        code("liars, rates = exp.liars_and_error()\n"
             "display(pd.DataFrame(liars).query('n in [25, 91, 121, 221, 341, 561]'))\n"
             "display(pd.DataFrame(rates).query('n == 25'))"),
        markdown("### Figura 4: errores observados y cota teórica\n"
                 "`0/3000` indica cero aceptaciones observadas, no probabilidad nula."),
        code("exp.plot_error(rates)\n"
             "display(Image(filename='figures/fig4_error_empirico.png'))"),
        markdown("### Tablas para el informe y auditoría de los archivos generados"),
        code("exp.latex_tables(generation, comparison, rates, liars, comparison_rows)\n"
             "print('Tablas LaTeX:', ', '.join(sorted(p.name for p in exp.LATEX.glob('*.tex'))))"),
        *module_parts("verify_results.py"),
        code("import verify_results\nverify_results.verify()"),
        markdown("## 12. Análisis (respuestas breves)\n"
                 "1. Todo compuesto $n=ab$ tiene un factor $\\leq\\sqrt n$: "
                 "si ambos fueran mayores, su producto excedería $n$.\n"
                 "2. En $L$ bits, $\\sqrt n=\\Theta(2^{L/2})$, exponencial en $L$.\n"
                 "3. Si Fermat falla, $n$ es compuesto; si pasa, $n$ puede ser pseudoprimo.\n"
                 "4. Un pseudoprimo pasa una base coprima; Carmichael pasa todas las coprimas.\n"
                 "5. La descomposición $n-1=2^sd$ permite buscar $-1$ "
                 "en la cadena de cuadrados.\n"
                 "6. Una raíz no trivial de $1$ módulo $n$ implica composición.\n"
                 "7. Testigo: rechaza un compuesto; mentiroso fuerte: lo acepta.\n"
                 "8. Un primo nunca es rechazado por una base válida: error unilateral.\n"
                 "9. $4^{-r}$ requiere bases uniformes independientes para compuesto impar.\n"
                 "10. Una semilla fija permite reconstruir claves; para ellas, usar "
                 "fuente segura.\n"
                 "11. El precribado elimina factores pequeños antes de rondas costosas.\n"
                 "12. Cero errores en una muestra finita no prueba probabilidad cero."),
        markdown("## 13. Archivos de entrega\n"
                 "El PDF del informe se compila por separado en `latex/main.pdf`. "
                 "Aquí se empaquetan código, diez CSV, cuatro figuras y los fragmentos "
                 "LaTeX. En Colab se descarga automáticamente; en Jupyter aparece un "
                 "enlace de descarga directamente en esta celda, sin buscar rutas "
                 "temporales. El cuaderno conserva sus resultados incrustados."),
        code("from zipfile import ZIP_DEFLATED, ZipFile\n"
             "archive = WORK / 'lab07_resultados.zip'\n"
             "with ZipFile(archive, 'w', ZIP_DEFLATED) as zf:\n"
             "    for folder in ('results', 'figures', 'latex_tables'):\n"
             "        for path in sorted(Path(folder).glob('*')):\n"
             "            if path.is_file():\n"
             "                zf.write(path)\n"
             "    for name in ('primality.py', 'case_generator.py', 'experiments.py', "
             "'test_primality.py', 'ejercicios_resueltos.py', 'verify_results.py'):\n"
             "        zf.write(name)\n"
             "print('Archivo preparado: lab07_resultados.zip')\n"
             "try:\n"
             "    from google.colab import files\n"
             "except ImportError:\n"
             "    from base64 import b64encode\n"
             "    from IPython.display import HTML\n"
             "    encoded = b64encode(archive.read_bytes()).decode('ascii')\n"
             "    display(HTML('<a download=\"lab07_resultados.zip\" '"
             "'href=\"data:application/zip;base64,' + encoded + '\">Descargar resultados (ZIP)</a>'))\n"
             "else:\n"
             "    files.download(str(archive))"),
    ]
    return nbf.v4.new_notebook(cells=cells, metadata={
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"}, "colab": {"provenance": []},
    })


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="Guardar salidas incrustadas")
    args = parser.parse_args()
    notebook = create()
    if args.execute:
        from nbclient import NotebookClient
        with tempfile.TemporaryDirectory(prefix="lab07_build_") as scratch:
            notebook = NotebookClient(notebook, timeout=1800, kernel_name="python3",
                                       resources={"metadata": {"path": scratch}}).execute()
    nbf.write(notebook, OUTPUT)
    print(f"Cuaderno generado: {OUTPUT} ({len(notebook.cells)} celdas)")


if __name__ == "__main__":
    main()
