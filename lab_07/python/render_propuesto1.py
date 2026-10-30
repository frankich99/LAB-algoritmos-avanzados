"""Construye tablas del propuesto 1 a partir de los CSV verificados."""

import csv
import json
from pathlib import Path


BASE = Path(__file__).resolve().parent
DESTINO = BASE.parent / "latex" / "secciones"


def rows(name):
    with (BASE / "results" / name).open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def renderizar():
    casos = {int(r["n"]): r for r in rows("casos_conocidos.csv")}
    numeros = (0, 1, 2, 3, 25, 341, 561, 1105, 1729)
    lines = [r"\begin{table}[H]\centering\small",
             r"\caption{Casos especiales y pseudoprimos: resultado de las tres pruebas}",
             r"\label{tab:casos_propuesto1}",
             r"\begin{tabular}{rlccc}\toprule",
             r"$n$ & Clasificación & División & Fermat (2) & MR (2) \\",
             r"\midrule"]
    tipos = {"primo": "primo", "compuesto": "compuesto",
             "no_primo_ni_compuesto": "ni primo ni compuesto"}
    def booleano(value):
        return {"True": "sí", "False": "no", "no_aplica": "--"}[value]
    for n in numeros:
        r = casos[n]
        lines.append(f'{n} & {tipos[r["clasificacion"]]} & '
                     f'{booleano(r["division_prueba"])} & '
                     f'{booleano(r["fermat_base_2"])} & '
                     f'{booleano(r["miller_rabin_base_2"])} \\\\')
    lines.append(r"\bottomrule\end{tabular}\end{table}")
    (DESTINO / "03_casos_generados.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    trazas = {int(r["n"]): r for r in rows("trazas_miller_rabin.csv")}
    lines = [r"\begin{table}[H]\centering\small",
             r"\caption{Trazas verificables de Miller--Rabin con base $2$}",
             r"\label{tab:trazas_propuesto1}",
             r"\begin{tabular}{rrrrll}\toprule",
             r"$n$ & $a$ & $s$ & $d$ & Residuos & Decisión \\",
             r"\midrule"]
    for n in (221, 341, 561):
        r = trazas[n]
        residuos = ", ".join(map(str, json.loads(r["residuos"])))
        assert r["pasa"] == "False"
        lines.append(f'{n} & {r["a"]} & {r["s"]} & {r["d"]} & '
                     f'[{residuos}] & testigo \\\\')
    lines.append(r"\bottomrule\end{tabular}\end{table}")
    (DESTINO / "03_trazas_generadas.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    renderizar()
