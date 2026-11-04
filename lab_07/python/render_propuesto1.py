"""Construye tablas del propuesto 1 a partir de los CSV verificados."""

import csv
import json
from pathlib import Path


BASE = Path(__file__).resolve().parent
DESTINO = BASE.parent / "latex" / "secciones"


def rows(name):
    with (BASE / "results" / name).open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def normalizar_caso(r):
    """Acepta los dos esquemas de casos_conocidos.csv usados por el grupo.

    Esquema A: clasificacion, division_prueba, fermat_base_2 (no_aplica), ...
    Esquema B: categoria, esperado, trial_division, fermat_base_2 (vacío), ...
    """
    if "clasificacion" in r:
        return r
    clasificacion = ("no_primo_ni_compuesto" if r["categoria"] == "especial"
                     else r["esperado"])
    def ronda(value):
        return value if value in ("True", "False") else "no_aplica"
    return {"n": r["n"], "clasificacion": clasificacion,
            "division_prueba": r["trial_division"],
            "fermat_base_2": ronda(r["fermat_base_2"]),
            "miller_rabin_base_2": ronda(r["miller_rabin_base_2"])}


def leer_residuos(texto):
    """Residuos como lista JSON ("[128, 30]") o cadena ("128 -> 30")."""
    texto = texto.strip()
    if texto.startswith("["):
        return json.loads(texto)
    return [int(x) for x in texto.split("->")]


def renderizar():
    casos = {int(r["n"]): normalizar_caso(r) for r in rows("casos_conocidos.csv")}
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

    trazas = {}
    for r in rows("trazas_miller_rabin.csv"):
        if r["a"] == "2":
            trazas.setdefault(int(r["n"]), r)
    lines = [r"\begin{table}[H]\centering\small",
             r"\caption{Trazas verificables de Miller--Rabin con base $2$}",
             r"\label{tab:trazas_propuesto1}",
             r"\begin{tabular}{rrrrll}\toprule",
             r"$n$ & $a$ & $s$ & $d$ & Residuos & Decisión \\",
             r"\midrule"]
    for n in (221, 341, 561):
        r = trazas[n]
        residuos = ", ".join(map(str, leer_residuos(r["residuos"])))
        assert r["pasa"] == "False"
        lines.append(f'{n} & {r["a"]} & {r["s"]} & {r["d"]} & '
                     f'[{residuos}] & testigo \\\\')
    lines.append(r"\bottomrule\end{tabular}\end{table}")
    (DESTINO / "03_trazas_generadas.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    renderizar()
