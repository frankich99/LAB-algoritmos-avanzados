"""Comprueba que los archivos generados satisfacen los mínimos de la Guía 07.

Ejecutar después de experiments.py: python python/verify_results.py
No reemplaza la suite unittest ni prueba primalidad de los números grandes.
"""

import csv
import json
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA = BASE / "results"
SIZES = (16, 32, 64, 128, 256, 512, 1024)


def rows(filename):
    with (DATA / filename).open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def verify():
    known = {int(row["n"]): row for row in rows("casos_conocidos.csv")}
    assert {0, 1, 2, 3, 221, 341, 561, 1105, 1729} <= known.keys()
    assert all(known[n]["clasificacion"] == "no_primo_ni_compuesto" for n in (0, 1))
    assert all(known[n]["fermat_base_2"] == "True" and
               known[n]["miller_rabin_base_2"] == "False"
               for n in (341, 561, 1105, 1729))

    traces = {(int(r["n"]), int(r["a"])): r
              for r in rows("trazas_miller_rabin.csv")}
    for n, residues in ((221, [128, 30]), (341, [32, 1]),
                        (561, [263, 166, 67, 1])):
        assert json.loads(traces[n, 2]["residuos"]) == residues

    generated = rows("generacion_210_probables_primos.csv")
    counts = Counter(int(r["bits"]) for r in generated)
    assert counts == Counter({bits: 30 for bits in SIZES})
    for row in generated:
        bits, n = int(row["bits"]), int(row["n"])
        assert n.bit_length() == bits and n % 2 == 1
        assert int(row["candidatos"]) > 0
        assert row["resultado"] == ("primo_verificado" if bits <= 32 else "probable_primo")
        assert int(row["descartes_precribado"]) < int(row["candidatos"])
        assert int(row["rondas_finales"]) == 20

    generation_summary = rows("resumen_generacion.csv")
    assert {int(r["bits"]) for r in generation_summary} == set(SIZES)
    for r in generation_summary:
        assert int(r["candidatos_total"]) == sum(int(g["candidatos"]) for g in generated
                                                  if g["bits"] == r["bits"])
        assert float(r["tiempo_min_ms"]) <= float(r["tiempo_mediano_ms"]) <= float(r["tiempo_max_ms"])

    inputs = rows("entradas_y_bases.csv")
    assert len(inputs) == 7 * 2 * 8
    for r in inputs:
        bases = json.loads(r["bases_20"])
        n = int(r["n"])
        assert len(bases) == 20 and all(2 <= a <= n - 2 for a in bases)

    comparison = rows("comparacion_metodos.csv")
    assert len(comparison) == 928
    assert {int(r["bits"]) for r in comparison} == set(SIZES)
    assert {int(r["rondas_solicitadas"]) for r in comparison} == {0, 1, 5, 10, 20}
    for r in comparison:
        assert int(r["min_ns"]) <= float(r["mediana_ns"]) <= int(r["max_ns"])
        if r["metodo"] == "division_prueba":
            assert int(r["bits"]) <= 32

    summary = rows("resumen_testigos_mentirosos.csv")
    classifications = rows("clasificacion_bases.csv")
    assert {221, 341, 561} <= {int(r["n"]) for r in summary}
    assert len(classifications) == sum(int(r["bases_validas"]) for r in summary)
    for r in summary:
        assert int(r["bases_validas"]) == int(r["testigos"]) + int(r["mentirosos_fuertes"])
        assert int(r["mentirosos_fuertes"]) / int(r["bases_validas"]) <= 0.25

    rates = rows("tasa_error_empirica.csv")
    assert len(rates) == 5 * 4
    for r in rates:
        assert int(r["muestras"]) == 3000
        assert float(r["cota_teorica"]) == 4.0 ** (-int(r["rondas"]))
        assert 0 <= float(r["tasa_exacta_bases_aleatorias"]) <= float(r["cota_teorica"])
    assert next(float(r["tasa_exacta_bases_aleatorias"]) for r in rates
                if r["n"] == "25" and r["rondas"] == "20") > 0

    figures = list((BASE / "figures").glob("fig*.png"))
    assert len(figures) >= 4 and all(f.stat().st_size > 1000 for f in figures)
    latex_dir = (BASE.parent / "latex" / "secciones" if BASE.name == "python"
                 else BASE / "latex_tables")
    fragments = ("04_tab_generacion.tex", "04_tab_tiempos.tex",
                 "04_tab_dispersion.tex", "04_tab_mentirosos.tex",
                 "04_tab_error.tex", "04_analisis_generacion.tex",
                 "04_analisis_costo.tex")
    assert all((latex_dir / name).is_file() and (latex_dir / name).stat().st_size > 100
               for name in fragments)
    print(f"Evidencias válidas: {len(generated)} probables primos, "
          f"{len(comparison)} comparaciones, {len(classifications)} bases, "
          f"{len(figures)} gráficos.")


if __name__ == "__main__":
    verify()
