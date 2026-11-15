"""Auditoría no destructiva de la evidencia generada para la Guía 08."""

import csv
import json
from pathlib import Path

from case_generator import MANUAL_CASES
from transforms import MODULUS, validate_root

BASE = Path(__file__).resolve().parent
DATA = BASE / "results"
EXPECTED = {"casos_manuales.csv", "modulos_raices.csv", "validacion_diferencial.csv",
            "validacion_fft_ifft.csv", "validacion_ntt_intt.csv", "discrepancias.csv",
            "rendimiento.csv", "puntos_cruce.csv", "error_fft.csv", "primer_fallo_fft.csv"}


def rows(name):
    with (DATA / name).open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def verify():
    assert {p.name for p in DATA.glob("*.csv")} == EXPECTED
    manual = rows("casos_manuales.csv")
    assert len(manual) == len(MANUAL_CASES)
    for row, (a, b, expected) in zip(manual, MANUAL_CASES):
        assert json.loads(row["a"]) == a and json.loads(row["b"]) == b
        assert json.loads(row["directa"]) == expected == json.loads(row["fft"])
        assert json.loads(row["ntt_mod_17"]) == [x % 17 for x in expected]

    roots = rows("modulos_raices.csv")
    assert len(roots) == 5 + 24
    for row in roots:
        assert validate_root(int(row["raiz_orden_n"]), int(row["n"]), int(row["modulo"]))
    assert {(int(r["modulo"]), int(r["n"])) for r in roots} >= {
        (17, 16), (MODULUS, 1 << 23)}

    diff = rows("validacion_diferencial.csv")
    assert len(diff) >= 12 and all(r["coincide"] == "True"
                                    for r in diff if r["rango"] != "residuos")
    assert all(r["coincide"] == "True" for r in diff if r["metodo"] == "ntt")
    fft = rows("validacion_fft_ifft.csv")
    ntt = rows("validacion_ntt_intt.csv")
    assert len(fft) == len(ntt) >= 1
    assert all(max(float(r["error_recursiva"]), float(r["error_iterativa"]),
                   float(r["diferencia_fft"])) < 1e-7 for r in fft)
    assert all(r["coincide"] == "True" for r in ntt)
    mismatches = rows("discrepancias.csv")
    assert len(mismatches) == sum(r["coincide"] == "False" for r in diff)
    for r in mismatches:
        assert json.loads(r["a"]) and json.loads(r["b"])
        assert r["metodo"].startswith("fft_") and r["rango"] == "residuos"

    performance = rows("rendimiento.csv")
    sizes = sorted({int(r["n_entrada"]) for r in performance})
    assert sizes == [1 << k for k in range(3, sizes[-1].bit_length())]
    assert all(int(r["repeticiones"]) >= 10 and
               int(r["min_ns"]) <= float(r["mediana_ns"]) <= int(r["max_ns"]) and
               r["coincide_referencia"] == "True" and
               int(r["n_transformada"]) >= 2 * int(r["n_entrada"]) - 1
               for r in performance)
    for n in sizes:
        methods = {r["metodo"] for r in performance if int(r["n_entrada"]) == n}
        expected = {"fft_recursiva", "fft_iterativa", "ntt"}
        if n <= 2048:
            expected.add("directa")
        assert methods == expected
    crossing = rows("puntos_cruce.csv")
    assert {r["metodo"] for r in crossing} == {"fft_recursiva", "fft_iterativa", "ntt"}
    for r in crossing:
        direct = {int(x["n_entrada"]): float(x["mediana_ns"]) for x in performance
                  if x["metodo"] == "directa"}
        faster = [int(x["n_entrada"]) for x in performance
                  if x["metodo"] == r["metodo"] and int(x["n_entrada"]) in direct
                  and float(x["mediana_ns"]) < direct[int(x["n_entrada"])]]
        assert r["primer_n_supera_directa"] == (str(min(faster)) if faster else "")

    errors = rows("error_fft.csv")
    assert len(errors) >= 10 and all(r["ntt_exacta_modulo_p"] == "True" for r in errors)
    first = rows("primer_fallo_fft.csv")
    assert len(first) <= 1
    if first:
        f = first[0]
        assert any(int(r["coeficientes_erroneos"]) > 0 and
                   int(r["n_entrada"]) == int(f["n"]) and
                   int(r["magnitud_maxima"]) == int(f["magnitud"]) and
                   r["metodo"] == f["metodo"] for r in errors)
    figs = {p.name for p in (BASE / "figures").glob("*.png")}
    assert figs == {"tiempo_vs_n.png", "operaciones_vs_n.png", "error_fft_vs_n.png"}
    assert all((BASE / "figures" / name).stat().st_size > 1000 for name in figs)
    print(f"OK: {len(manual)} casos, {len(diff)} comparaciones, {len(performance)} "
          f"mediciones, {len(errors)} filas de error, {len(mismatches)} discrepancias "
          f"documentadas, {len(figs)} figuras.")


if __name__ == "__main__":
    verify()
