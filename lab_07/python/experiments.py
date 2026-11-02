"""Batería experimental, mediciones y auditoría (Guía 07, Algoritmos Avanzados, UNSAAC).

Módulo asignado a Romario Quispe Rimachi (RamaRomario).
Ejecuta la campaña experimental rigurosa para la comparación de pruebas de
primalidad deterministas y probabilísticas (división de prueba, Fermat y Miller-Rabin).
"""

from math import gcd, isqrt
from pathlib import Path
from random import Random
from statistics import mean, median
from time import perf_counter_ns
import csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from primality import (
    classify_bases,
    decompose,
    fermat_round,
    fermat_test,
    generate_candidate,
    generate_probable_prime,
    miller_rabin_round,
    primality_report,
    trial_division,
)

BASE_DIR = Path(__file__).resolve().parent
RESULTS = BASE_DIR / "results"
FIGURES = BASE_DIR / "figures"
LATEX = BASE_DIR / "latex_tables"

SEEDS = {
    "generation": 20260701,
    "comparison": 20260702,
    "error_rate": 20260703,
}

BIT_SIZES = [16, 32, 64, 128, 256, 512, 1024]
ROUNDS_LIST = [1, 5, 10, 20]
REPETITIONS = 7


def _save_csv(path, rows, fieldnames=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    if fieldnames is None:
        fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _measure_call(func, repetitions=REPETITIONS):
    times = []
    result = None
    for _ in range(repetitions):
        start = perf_counter_ns()
        res = func()
        elapsed = perf_counter_ns() - start
        times.append(elapsed)
        result = res
    times.sort()
    return min(times), median(times), max(times), result


def known_and_traces():
    """Genera tablas de casos conocidos deterministas y trazas detalladas de Miller-Rabin."""
    casos_raw = [
        (0, "especial", "no_primo"),
        (1, "especial", "no_primo"),
        (2, "primo_par", "primo"),
        (3, "primo_impar", "primo"),
        (4, "par_compuesto", "compuesto"),
        (6, "par_compuesto", "compuesto"),
        (8, "par_compuesto", "compuesto"),
        (9, "cuadrado_primo", "compuesto"),
        (15, "impar_compuesto", "compuesto"),
        (25, "cuadrado_primo", "compuesto"),
        (49, "cuadrado_primo", "compuesto"),
        (121, "cuadrado_primo", "compuesto"),
        (169, "cuadrado_primo", "compuesto"),
        (221, "pseudoprimo_candidato", "compuesto"),
        (341, "pseudoprimo_fermat", "compuesto"),
        (561, "carmichael", "compuesto"),
        (1105, "carmichael", "compuesto"),
        (1729, "carmichael", "compuesto"),
        (17, "primo_pequeno", "primo"),
        (31, "primo_pequeno", "primo"),
        (127, "primo_pequeno", "primo"),
        (1009, "primo_pequeno", "primo"),
    ]

    casos = []
    for n, cat, esperado in casos_raw:
        td = trial_division(n) if n >= 2 else False
        f_b2 = fermat_round(n, 2) if (n >= 5 and n % 2 == 1) else None
        mr_b2, mr_det = miller_rabin_round(n, 2) if (n >= 5 and n % 2 == 1) else (None, None)
        rep = primality_report(n, rounds=5, presieve=True)

        casos.append({
            "n": n,
            "categoria": cat,
            "esperado": esperado,
            "trial_division": td,
            "fermat_base_2": f_b2,
            "miller_rabin_base_2": mr_b2,
            "resultado_reporte": rep["resultado"],
            "descartado_precribado": rep["descartado_precribado"],
            "rondas_ejecutadas": rep["rondas_ejecutadas"],
        })

    _save_csv(RESULTS / "casos_conocidos.csv", casos)

    trazas_casos = [
        (221, 2),
        (341, 2),
        (561, 2),
        (1105, 2),
        (1729, 2),
        (1009, 2),
        (221, 3),
        (341, 3),
        (561, 5),
    ]

    trazas = []
    for n, a in trazas_casos:
        passed, detail = miller_rabin_round(n, a, trace=True)
        trazas.append({
            "n": n,
            "a": a,
            "s": detail["s"],
            "d": detail["d"],
            "residuos": " -> ".join(map(str, detail["residuos"])),
            "cuadrados_cadena": detail["cuadrados_cadena"],
            "cuadrados_modulares": detail["cuadrados_modulares"],
            "productos_modulares": detail["productos_modulares"],
            "motivo": detail["motivo"],
            "pasa": passed,
        })

    _save_csv(RESULTS / "trazas_miller_rabin.csv", trazas)
    return casos, trazas


def liars_and_error(seed=SEEDS["error_rate"]):
    """Clasifica bases para compuestos pequeños y mide empíricamente la tasa de error."""
    compuestos_exhaustivos = [
        c for c in range(9, 200, 2) if not trial_division(c)
    ]
    for especial in [221, 341, 561]:
        if especial not in compuestos_exhaustivos:
            compuestos_exhaustivos.append(especial)
    compuestos_exhaustivos.sort()

    liars = []
    for c in compuestos_exhaustivos:
        res = classify_bases(c)
        total_bases = c - 3
        cant_liars = len(res["mentirosos_fuertes"])
        cant_wit = len(res["testigos"])
        frac = res["fraccion_mentirosos"]
        liars.append({
            "n": c,
            "total_bases": total_bases,
            "cantidad_mentirosos": cant_liars,
            "cantidad_testigos": cant_wit,
            "fraccion_mentirosos": round(frac, 6),
            "cota_max_teorica": 0.25,
            "mentirosos_fuertes": ",".join(map(str, res["mentirosos_fuertes"][:10])) + ("..." if cant_liars > 10 else ""),
        })

    _save_csv(RESULTS / "clasificacion_bases.csv", liars)

    compuestos_sim = [25, 91, 121, 221, 341, 561]
    num_simulaciones = 3000
    rates = []
    rng = Random(seed)

    for n in compuestos_sim:
        res_bases = classify_bases(n)
        p_base = res_bases["fraccion_mentirosos"]
        for r in ROUNDS_LIST:
            errores = 0
            for _ in range(num_simulaciones):
                bases = [rng.randrange(2, n - 1) for _ in range(r)]
                rep = primality_report(n, rounds=r, bases=bases, presieve=False)
                if rep["resultado"] == "probable_primo":
                    errores += 1

            tasa_obs = errores / num_simulaciones
            prob_exacta = p_base ** r
            cota_univ = 4.0 ** (-r)

            rates.append({
                "n": n,
                "rondas": r,
                "simulaciones": num_simulaciones,
                "errores_observados": errores,
                "tasa_observada": round(tasa_obs, 7),
                "probabilidad_exacta": round(prob_exacta, 8),
                "cota_universal": cota_univ,
            })

    _save_csv(RESULTS / "tasa_error_empirica.csv", rates)
    return liars, rates


def generate_primes(seed=SEEDS["generation"]):
    """Genera 30 probables primos por cada longitud (210 en total) y registra estadísticas."""
    rng = Random(seed)
    primes_by_bits = {}
    detalle_primos = []
    generation = []

    for bits in BIT_SIZES:
        primes_list = []
        candidatos_lista = []
        descartes_lista = []
        cuadrados_lista = []

        for idx in range(30):
            rep = generate_probable_prime(bits, rounds=20, rng=rng, return_report=True)
            p = rep["n"]
            primes_list.append(p)
            candidatos_lista.append(rep["candidatos"])
            descartes_lista.append(rep["descartes_precribado"])
            cuadrados_lista.append(rep["cuadrados_modulares"])

            if bits in (16, 32):
                es_primo_exacto = trial_division(p)
                assert es_primo_exacto is True, f"Fallo al validar primo {bits} bits: {p}"
                tipo = "primo_verificado"
            else:
                tipo = "probable_primo"

            detalle_primos.append({
                "bits": bits,
                "indice": idx,
                "n": str(p),
                "candidatos": rep["candidatos"],
                "descartes_precribado": rep["descartes_precribado"],
                "rondas_ejecutadas": rep["rondas_ejecutadas"],
                "cuadrados_modulares": rep["cuadrados_modulares"],
                "cota_error": rep["cota_error"],
                "tipo_entrada": tipo,
            })

        primes_by_bits[bits] = primes_list
        generation.append({
            "bits": bits,
            "total_generados": len(primes_list),
            "candidatos_total": sum(candidatos_lista),
            "candidatos_promedio": round(mean(candidatos_lista), 2),
            "candidatos_mediana": median(candidatos_lista),
            "descartes_promedio": round(mean(descartes_lista), 2),
            "cuadrados_promedio": round(mean(cuadrados_lista), 2),
            "cota_error": 4.0 ** (-20),
        })

    _save_csv(RESULTS / "probables_primos_generados.csv", detalle_primos)
    _save_csv(RESULTS / "resumen_generacion.csv", generation)
    return primes_by_bits, generation


def _construct_composite(bits, rng):
    """Construye un compuesto impar de exactamente `bits` bits multiplicando dos impares."""
    if bits <= 16:
        while True:
            a = rng.getrandbits(bits // 2) | 1 | (1 << ((bits // 2) - 1))
            b = rng.getrandbits(bits - (bits // 2)) | 1 | (1 << (bits - (bits // 2) - 1))
            n = a * b
            if n.bit_length() == bits and n % 2 == 1 and not trial_division(n):
                return n
    else:
        half = bits // 2
        p1 = generate_candidate(half, rng)
        p2 = generate_candidate(bits - half, rng)
        n = p1 * p2
        while n.bit_length() != bits:
            p1 = generate_candidate(half, rng)
            p2 = generate_candidate(bits - half, rng)
            n = p1 * p2
        return n


def compare_methods(primes_by_bits, seed=SEEDS["comparison"]):
    """Compara división de prueba, Fermat y Miller-Rabin con 20 bases pre-generadas."""
    rng = Random(seed)
    entradas_y_bases = []
    inputs_by_size = {}

    for bits in BIT_SIZES:
        primes = primes_by_bits[bits][:8]
        composites = [_construct_composite(bits, rng) for _ in range(8)]
        lista_entradas = []

        for idx, p in enumerate(primes):
            tipo = "primo_verificado" if bits in (16, 32) else "probable_primo"
            bases = []
            while len(bases) < 20:
                cand = rng.randrange(2, p - 1)
                if cand not in bases:
                    bases.append(cand)
            row = {"bits": bits, "indice": idx, "tipo_entrada": tipo, "n": str(p), "n_val": p, "bases": bases}
            lista_entradas.append(row)

        for idx, c in enumerate(composites):
            bases = []
            while len(bases) < 20:
                cand = rng.randrange(2, c - 1)
                if cand not in bases:
                    bases.append(cand)
            row = {"bits": bits, "indice": idx + 8, "tipo_entrada": "compuesto_construido", "n": str(c), "n_val": c, "bases": bases}
            lista_entradas.append(row)

        inputs_by_size[bits] = lista_entradas

    for bits in BIT_SIZES:
        for item in inputs_by_size[bits]:
            base_cols = {f"base_{i+1:02d}": item["bases"][i] for i in range(20)}
            entradas_y_bases.append({
                "bits": item["bits"],
                "indice": item["indice"],
                "tipo_entrada": item["tipo_entrada"],
                "n": item["n"],
                **base_cols,
            })

    _save_csv(RESULTS / "entradas_y_bases.csv", entradas_y_bases)

    comparison_rows = []

    for bits in BIT_SIZES:
        for item in inputs_by_size[bits]:
            n = item["n_val"]
            bases_20 = item["bases"]
            tipo = item["tipo_entrada"]
            idx = item["indice"]

            if bits <= 32:
                min_ns, med_ns, max_ns, td_res = _measure_call(lambda: trial_division(n))
                comparison_rows.append({
                    "bits": bits,
                    "indice": idx,
                    "tipo_entrada": tipo,
                    "n": str(n),
                    "metodo": "division_prueba",
                    "rondas_solicitadas": 1,
                    "rondas_ejecutadas": 1,
                    "cuadrados_modulares": 0,
                    "min_ns": min_ns,
                    "mediana_ns": med_ns,
                    "max_ns": max_ns,
                    "resultado": "primo" if td_res else "compuesto",
                })

            for r in ROUNDS_LIST:
                sub_bases = bases_20[:r]
                min_ns, med_ns, max_ns, f_res = _measure_call(lambda: fermat_test(n, sub_bases))
                comparison_rows.append({
                    "bits": bits,
                    "indice": idx,
                    "tipo_entrada": tipo,
                    "n": str(n),
                    "metodo": "fermat",
                    "rondas_solicitadas": r,
                    "rondas_ejecutadas": f_res["rondas_ejecutadas"],
                    "cuadrados_modulares": f_res["cuadrados_modulares"],
                    "min_ns": min_ns,
                    "mediana_ns": med_ns,
                    "max_ns": max_ns,
                    "resultado": f_res["resultado"],
                })

            for r in ROUNDS_LIST:
                sub_bases = bases_20[:r]
                min_ns, med_ns, max_ns, mr_res = _measure_call(
                    lambda: primality_report(n, rounds=r, bases=sub_bases, presieve=False)
                )
                comparison_rows.append({
                    "bits": bits,
                    "indice": idx,
                    "tipo_entrada": tipo,
                    "n": str(n),
                    "metodo": "miller_rabin",
                    "rondas_solicitadas": r,
                    "rondas_ejecutadas": mr_res["rondas_ejecutadas"],
                    "cuadrados_modulares": mr_res["cuadrados_modulares"],
                    "min_ns": min_ns,
                    "mediana_ns": med_ns,
                    "max_ns": max_ns,
                    "resultado": mr_res["resultado"],
                })

    _save_csv(RESULTS / "comparacion_detallada.csv", comparison_rows)

    from collections import defaultdict
    grouped = defaultdict(list)
    for row in comparison_rows:
        key = (row["bits"], row["tipo_entrada"], row["metodo"], row["rondas_solicitadas"])
        grouped[key].append(row)

    comparison = []
    for (bits, tipo, metodo, rondas), items in sorted(grouped.items()):
        meds_ns = [it["mediana_ns"] for it in items]
        mins_ns = [it["min_ns"] for it in items]
        maxs_ns = [it["max_ns"] for it in items]
        sqs = [it["cuadrados_modulares"] for it in items]
        comparison.append({
            "bits": bits,
            "tipo_entrada": tipo,
            "metodo": metodo,
            "rondas": rondas,
            "tiempo_min_us": round(median(mins_ns) / 1000.0, 3),
            "tiempo_mediano_us": round(median(meds_ns) / 1000.0, 3),
            "tiempo_max_us": round(median(maxs_ns) / 1000.0, 3),
            "cuadrados_modulares": int(median(sqs)),
        })

    _save_csv(RESULTS / "comparacion_resumen.csv", comparison)
    return comparison_rows, comparison


def plot_timing(comparison):
    """Figura 1: Gráfico de tiempo de ejecución mediano vs longitud en bits."""
    FIGURES.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(9, 5.5))

    td_points = [
        (c["bits"], c["tiempo_mediano_us"])
        for c in comparison
        if c["metodo"] == "division_prueba" and c["tipo_entrada"] != "compuesto_construido"
    ]
    if td_points:
        xs, ys = zip(*td_points)
        plt.plot(xs, ys, "o--", color="#d62728", label="División de prueba (determinista)", linewidth=2.2, markersize=8)

    colors_mr = {1: "#1f77b4", 5: "#2ca02c", 10: "#ff7f0e", 20: "#9467bd"}
    for r in ROUNDS_LIST:
        pts = [
            (c["bits"], c["tiempo_mediano_us"])
            for c in comparison
            if c["metodo"] == "miller_rabin" and c["rondas"] == r and c["tipo_entrada"] != "compuesto_construido"
        ]
        if pts:
            xs, ys = zip(*pts)
            plt.plot(xs, ys, "s-", color=colors_mr[r], label=f"Miller-Rabin ({r} rondas)", linewidth=1.8, markersize=6)

    for r in (1, 20):
        pts = [
            (c["bits"], c["tiempo_mediano_us"])
            for c in comparison
            if c["metodo"] == "fermat" and c["rondas"] == r and c["tipo_entrada"] != "compuesto_construido"
        ]
        if pts:
            xs, ys = zip(*pts)
            plt.plot(xs, ys, ":", color=colors_mr[r], alpha=0.75, label=f"Fermat ({r} rondas)", linewidth=1.5)

    plt.yscale("log")
    plt.xlabel("Longitud binaria $L$ (bits)", fontsize=11, fontweight="bold")
    plt.ylabel("Tiempo mediano ($\\mu s$, escala logarítmica)", fontsize=11, fontweight="bold")
    plt.title("Rendimiento Temporal: Pruebas de Primalidad vs. Longitud Binaria", fontsize=12, fontweight="bold")
    plt.grid(True, which="both", linestyle="--", alpha=0.5)
    plt.legend(fontsize=9, loc="upper left")
    plt.tight_layout()
    plt.savefig(FIGURES / "fig1_tiempo_vs_bits.png", dpi=300)
    plt.close()


def plot_squares(comparison):
    """Figura 2: Cuadrados modulares en función de la longitud en bits."""
    FIGURES.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(9, 5.5))

    colors = {1: "#1f77b4", 5: "#2ca02c", 10: "#ff7f0e", 20: "#9467bd"}
    for r in ROUNDS_LIST:
        pts = [
            (c["bits"], c["cuadrados_modulares"])
            for c in comparison
            if c["metodo"] == "miller_rabin" and c["rondas"] == r and c["tipo_entrada"] != "compuesto_construido"
        ]
        if pts:
            xs, ys = zip(*pts)
            plt.plot(xs, ys, "o-", color=colors[r], label=f"Miller-Rabin ({r} rondas)", linewidth=2, markersize=6)

    plt.xlabel("Longitud binaria $L$ (bits)", fontsize=11, fontweight="bold")
    plt.ylabel("Cuadrados modulares reales ejecutados", fontsize=11, fontweight="bold")
    plt.title("Operaciones Aritméticas: Cuadrados Modulares vs. Longitud Binaria", fontsize=12, fontweight="bold")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(fontsize=9)
    plt.tight_layout()
    plt.savefig(FIGURES / "fig2_cuadrados_vs_bits.png", dpi=300)
    plt.close()


def plot_candidates(generation):
    """Figura 3: Número de candidatos necesarios hasta hallar un primo frente a bits."""
    FIGURES.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(9, 5.5))

    bits = [g["bits"] for g in generation]
    cands_mean = [g["candidatos_promedio"] for g in generation]
    cands_med = [g["candidatos_mediana"] for g in generation]

    import math
    teorico_sin_precribado = [(math.log(2) / 2) * b for b in bits]

    plt.plot(bits, cands_mean, "o-", color="#1f77b4", label="Candidatos promedio (con precribado)", linewidth=2.2, markersize=7)
    plt.plot(bits, cands_med, "s--", color="#2ca02c", label="Candidatos mediana", linewidth=1.8, markersize=6)
    plt.plot(bits, teorico_sin_precribado, ":", color="#7f7f7f", label="Referencia teórica sin precribado $\\approx \\frac{\\ln 2}{2} L$", linewidth=1.5)

    plt.xlabel("Longitud binaria $L$ (bits)", fontsize=11, fontweight="bold")
    plt.ylabel("Número de candidatos muestreados", fontsize=11, fontweight="bold")
    plt.title("Generación de Primos: Candidatos Requeridos vs. Bits", fontsize=12, fontweight="bold")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(fontsize=9)
    plt.tight_layout()
    plt.savefig(FIGURES / "fig3_candidatos_vs_bits.png", dpi=300)
    plt.close()


def plot_error(rates):
    """Figura 4: Tasa empírica de error vs probabilidad exacta y cota universal."""
    FIGURES.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(9, 5.5))

    rondas = ROUNDS_LIST
    cotas = [4.0 ** (-r) for r in rondas]
    plt.plot(rondas, cotas, "k--", label="Cota universal teórica $4^{-r}$", linewidth=2.5)

    compuestos = [25, 91, 561]
    colores = {25: "#1f77b4", 91: "#ff7f0e", 561: "#2ca02c"}

    for c in compuestos:
        subset = [r for r in rates if r["n"] == c]
        if subset:
            xs = [r["rondas"] for r in subset]
            exactas = [r["probabilidad_exacta"] for r in subset]
            obs = [max(r["tasa_observada"], 1e-6) for r in subset]
            plt.plot(xs, exactas, "o-", color=colores[c], label=f"$n={c}$ (Probabilidad exacta)", linewidth=1.8)
            plt.scatter(xs, obs, marker="x", s=80, color=colores[c], label=f"$n={c}$ (Empírica, 3000 sim.)")

    plt.yscale("log")
    plt.xlabel("Número de rondas independientes $r$", fontsize=11, fontweight="bold")
    plt.ylabel("Probabilidad / Tasa de error (escala log)", fontsize=11, fontweight="bold")
    plt.title("Análisis de Error: Tasa Empírica vs. Probabilidad Exacta y Cota $4^{-r}$", fontsize=12, fontweight="bold")
    plt.grid(True, which="both", linestyle="--", alpha=0.5)
    plt.legend(fontsize=8.5, loc="upper right")
    plt.tight_layout()
    plt.savefig(FIGURES / "fig4_error_empirico.png", dpi=300)
    plt.close()


def latex_tables(generation, comparison, rates, liars, comparison_rows):
    """Genera fragmentos LaTeX para la integración automática del informe."""
    LATEX.mkdir(parents=True, exist_ok=True)

    with open(LATEX / "tabla_generacion.tex", "w", encoding="utf-8") as f:
        f.write("% Tabla autogenerada de generacion de probables primos\n")
        f.write("\\begin{tabular}{ccccc}\n\\toprule\n")
        f.write("Bits & Total & Candidatos Prom. & Descartes Prom. & Cota Error \\\\\n\\midrule\n")
        for g in generation:
            f.write(f"{g['bits']} & {g['total_generados']} & {g['candidatos_promedio']} & {g['descartes_promedio']} & $4^{{-20}}$ \\\\\n")
        f.write("\\bottomrule\n\\end{tabular}\n")

    with open(LATEX / "tabla_comparacion.tex", "w", encoding="utf-8") as f:
        f.write("% Tabla autogenerada de comparacion de metodos\n")
        f.write("\\begin{tabular}{cccccc}\n\\toprule\n")
        f.write("Bits & Método & Rondas & $t_{med}$ ($\\mu$s) & Cuadrados \\\\\n\\midrule\n")
        for c in comparison:
            if c["tipo_entrada"] != "compuesto_construido" and c["rondas"] in (1, 20):
                f.write(f"{c['bits']} & {c['metodo']} & {c['rondas']} & {c['tiempo_mediano_us']} & {c['cuadrados_modulares']} \\\\\n")
        f.write("\\bottomrule\n\\end{tabular}\n")

    with open(LATEX / "tabla_tasa_error.tex", "w", encoding="utf-8") as f:
        f.write("% Tabla autogenerada de tasa de error empirica\n")
        f.write("\\begin{tabular}{cccccc}\n\\toprule\n")
        f.write("$n$ & Rondas & Sim. & Errores Obs. & Prob. Exacta & Cota $4^{-r}$ \\\\\n\\midrule\n")
        for r in rates:
            f.write(f"{r['n']} & {r['rondas']} & {r['simulaciones']} & {r['errores_observados']} & {r['probabilidad_exacta']:.2e} & {r['cota_universal']:.2e} \\\\\n")
        f.write("\\bottomrule\n\\end{tabular}\n")

    with open(LATEX / "tabla_clasificacion_bases.tex", "w", encoding="utf-8") as f:
        f.write("% Tabla autogenerada de clasificacion de bases\n")
        f.write("\\begin{tabular}{ccccc}\n\\toprule\n")
        f.write("$n$ & Total Bases & Mentirosos & Testigos & Frac. Mentirosos \\\\\n\\midrule\n")
        for l in liars[:10]:
            f.write(f"{l['n']} & {l['total_bases']} & {l['cantidad_mentirosos']} & {l['cantidad_testigos']} & {l['fraccion_mentirosos']} \\\\\n")
        f.write("\\bottomrule\n\\end{tabular}\n")


def main():
    """Ejecuta la campaña experimental completa, genera 10 CSVs, 4 PNGs y tablas LaTeX."""
    print("Iniciando batería experimental de Primalidad (Guía 07)...")
    RESULTS.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    LATEX.mkdir(parents=True, exist_ok=True)

    print("1/5. Casos conocidos y trazas de Miller-Rabin...")
    casos, trazas = known_and_traces()

    print("2/5. Clasificación de bases y tasa de error empírica (3000 sim/caso)...")
    liars, rates = liars_and_error()

    print("3/5. Generación de 210 probables primos (16 a 1024 bits)...")
    primes_by_bits, generation = generate_primes()

    print("4/5. Comparación experimental de métodos (7 repeticiones, 20 bases)...")
    comparison_rows, comparison = compare_methods(primes_by_bits)

    print("5/5. Generación de figuras PNG y tablas LaTeX...")
    plot_timing(comparison)
    plot_squares(comparison)
    plot_candidates(generation)
    plot_error(rates)
    latex_tables(generation, comparison, rates, liars, comparison_rows)

    resumen_ejecucion = [
        {"parametro": "semilla_generacion", "valor": SEEDS["generation"], "descripcion": "Semilla para 210 probables primos"},
        {"parametro": "semilla_comparacion", "valor": SEEDS["comparison"], "descripcion": "Semilla para 112 entradas y 20 bases"},
        {"parametro": "semilla_tasa_error", "valor": SEEDS["error_rate"], "descripcion": "Semilla para simulación de errores"},
        {"parametro": "tamanios_bits", "valor": "16, 32, 64, 128, 256, 512, 1024", "descripcion": "Longitudes evaluadas"},
        {"parametro": "total_primos_generados", "valor": 210, "descripcion": "30 primos por cada tamaño"},
        {"parametro": "repeticiones_por_medicion", "valor": REPETITIONS, "descripcion": "Repeticiones para cálculo de mediana"},
        {"parametro": "simulaciones_tasa_error", "valor": 3000, "descripcion": "Muestreos Monte Carlo por caso"},
        {"parametro": "csvs_generados", "valor": 10, "descripcion": "Total de datasets CSV auditables"},
        {"parametro": "figuras_png", "valor": 4, "descripcion": "Total de gráficos de alta resolución"},
    ]
    _save_csv(RESULTS / "resumen_ejecucion.csv", resumen_ejecucion)

    print("Batería experimental finalizada con éxito.")
    print(f"Resultados guardados en: {RESULTS}")
    print(f"Figuras guardadas en: {FIGURES}")


if __name__ == "__main__":
    main()
