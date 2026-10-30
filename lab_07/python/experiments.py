"""Experimentos de la Guía 07. Salidas: results/*.csv, figures/*.png y LaTeX.

Generar entradas y bases ANTES de medir. Para comparar pruebas se desactiva el
precribado: de otro modo la mayoría de compuestos no ejecutaría ninguna ronda.
La generación de primos SÍ usa precribado; su tiempo incluye RNG y candidatos.
"""

import csv
import json
import math
from pathlib import Path
from statistics import mean, median
from time import perf_counter_ns

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from case_generator import KNOWN_CASES, SIZES, benchmark_inputs, make_rng
from primality import (classify_bases, fermat_round, fermat_test,
                       generate_probable_prime, miller_rabin_round,
                       primality_report, trial_division, trial_division_with_count)

BASE = Path(__file__).resolve().parent
RESULTS = BASE / "results"
FIGURES = BASE / "figures"
# En Colab/Jupyter el cuaderno ejecuta este módulo en un directorio temporal;
# sus mediciones no sobrescriben las tablas locales del informe.
LATEX = (BASE.parent / "latex" / "secciones" if BASE.name == "python"
         else BASE / "latex_tables")
SEED_GENERATION = 20260701
SEED_BENCHMARK = 20260702
SEED_LIARS = 20260703
ROUNDS = (1, 5, 10, 20)
PRIMES_PER_BITS = 30
BENCHMARK_PAIRS = 8
REPETITIONS = 7
TRIAL_MAX_BITS = 32

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "figure.dpi": 150,
    "axes.grid": True, "grid.color": "#dddddd", "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False,
    "savefig.bbox": "tight", "legend.frameon": False,
})


def measure(function, repetitions=REPETITIONS):
    """Mínimo, mediana y máximo en ns; sin impresión, CSV ni RNG en la ventana."""
    times = []
    for _ in range(repetitions):
        start = perf_counter_ns()
        function()
        times.append(perf_counter_ns() - start)
    return min(times), median(times), max(times)


def write_csv(name, rows):
    rows = list(rows)
    if not rows:
        raise ValueError(f"Sin filas para {name}")
    with (RESULTS / name).open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def known_and_traces():
    cases = []
    for n, actual_prime in KNOWN_CASES:
        fm = fermat_round(n, 2) if n >= 5 and n % 2 else "no_aplica"
        mr = miller_rabin_round(n, 2)[0] if n >= 5 and n % 2 else "no_aplica"
        cases.append({"n": n, "clasificacion": "primo" if actual_prime else
                      ("no_primo_ni_compuesto" if n < 2 else "compuesto"),
                      "division_prueba": trial_division(n), "fermat_base_2": fm,
                      "miller_rabin_base_2": mr,
                      "precribado": primality_report(n)["descartado_precribado"]})
    write_csv("casos_conocidos.csv", cases)

    traces = []
    for n, a in ((221, 2), (341, 2), (561, 2), (1105, 2), (1729, 2), (25, 7)):
        passed, row = miller_rabin_round(n, a, trace=True)
        traces.append({"n": n, "a": a, "s": row["s"], "d": row["d"],
                       "residuos": json.dumps(row["residuos"]),
                       "pasa": passed, "motivo": row["motivo"],
                       "cuadrados_modulares": row["cuadrados_modulares"]})
    write_csv("trazas_miller_rabin.csv", traces)
    return cases, traces


def liars_and_error():
    base_rows, summary = [], []
    chosen = set(range(5, 200, 2)) | {221, 341, 561}
    for n in sorted(chosen):
        if trial_division(n):
            continue
        result = classify_bases(n)
        liars = set(result["mentirosos_fuertes"])
        summary.append({"n": n, "bases_validas": n - 3,
                        "testigos": len(result["testigos"]),
                        "mentirosos_fuertes": len(liars),
                        "fraccion_mentirosos": round(result["fraccion_mentirosos"], 8),
                        "cota_un_cuarto": 0.25})
        for a in range(2, n - 1):
            base_rows.append({"n": n, "a": a, "clase":
                              "mentiroso_fuerte" if a in liars else "testigo"})
    write_csv("clasificacion_bases.csv", base_rows)
    write_csv("resumen_testigos_mentirosos.csv", summary)
    assert all(row["fraccion_mentirosos"] <= 0.25 for row in summary)

    # Simulación de bases uniformes independientes con reemplazo. El valor
    # exacto (p_n)^r se obtiene de la clasificación exhaustiva, sin simular MR.
    rng = make_rng(SEED_LIARS)
    rate_rows = []
    trials = 3000
    for n in (25, 91, 121, 341, 561):
        liar_set = set(classify_bases(n)["mentirosos_fuertes"])
        p = len(liar_set) / (n - 3)
        for rounds in ROUNDS:
            accepted = 0
            for _ in range(trials):
                accepted += all(rng.randrange(2, n - 1) in liar_set
                                for _ in range(rounds))
            rate_rows.append({"seed": SEED_LIARS, "n": n, "rondas": rounds,
                              "muestras": trials, "compuestos_aceptados": accepted,
                              "tasa_empirica": round(accepted / trials, 8),
                              "tasa_exacta_bases_aleatorias": p**rounds,
                              "cota_teorica": 4.0**-rounds})
    write_csv("tasa_error_empirica.csv", rate_rows)
    return summary, rate_rows


def generate_primes():
    rng = make_rng(SEED_GENERATION)
    rows, primes_by_bits, summary = [], {}, []
    for bits in SIZES:
        primes = []
        for index in range(PRIMES_PER_BITS):
            start = perf_counter_ns()
            result = generate_probable_prime(bits, rounds=20, rng=rng, return_report=True)
            elapsed = perf_counter_ns() - start
            n = result["n"]
            assert n.bit_length() == bits and n % 2 == 1
            if bits <= TRIAL_MAX_BITS:
                assert trial_division(n), n
            primes.append(n)
            rows.append({"seed": SEED_GENERATION, "bits": bits, "indice": index,
                         "n": n, "resultado": "primo_verificado" if bits <= 32
                         else "probable_primo", "candidatos": result["candidatos"],
                         "descartes_precribado": result["descartes_precribado"],
                         "rondas_ejecutadas": result["rondas_ejecutadas"],
                         "cuadrados_modulares": result["cuadrados_modulares"],
                         "rondas_finales": result["rondas_finales"],
                         "cota_error": result["cota_error"],
                         "verificacion_exacta": bits <= TRIAL_MAX_BITS,
                         "tiempo_generacion_ns": elapsed})
        primes_by_bits[bits] = primes
        group = [r for r in rows if r["bits"] == bits]
        summary.append({"seed": SEED_GENERATION, "bits": bits,
                        "primos_probables": len(group),
                        "candidatos_total": sum(r["candidatos"] for r in group),
                        "candidatos_media": round(mean(r["candidatos"] for r in group), 2),
                        "candidatos_mediana": median(r["candidatos"] for r in group),
                        "candidatos_min": min(r["candidatos"] for r in group),
                        "candidatos_max": max(r["candidatos"] for r in group),
                        "descartes_precribado": sum(r["descartes_precribado"] for r in group),
                        "rondas_ejecutadas": sum(r["rondas_ejecutadas"] for r in group),
                        "cuadrados_modulares": sum(r["cuadrados_modulares"] for r in group),
                        "tiempo_mediano_ms": round(median(r["tiempo_generacion_ns"]
                                                       for r in group) / 1e6, 3),
                        "tiempo_min_ms": round(min(r["tiempo_generacion_ns"]
                                                    for r in group) / 1e6, 3),
                        "tiempo_max_ms": round(max(r["tiempo_generacion_ns"]
                                                    for r in group) / 1e6, 3),
                        "candidatos_estimados": round(bits * math.log(2) / 2, 1)})
        print(f"Generación {bits:4d} bits: {len(group)} probables primos, "
              f"{summary[-1]['candidatos_total']} candidatos")
    write_csv("generacion_210_probables_primos.csv", rows)
    write_csv("resumen_generacion.csv", summary)
    return primes_by_bits, summary


def compare_methods(primes_by_bits):
    rng = make_rng(SEED_BENCHMARK)
    inputs = [case for bits in SIZES for case in benchmark_inputs(
        bits, primes_by_bits[bits], rng, BENCHMARK_PAIRS)]
    # CSV de las bases realmente usadas: la semilla sola no documenta qué
    # testigos concretos recibió cada método ni facilita auditar una fila.
    write_csv("entradas_y_bases.csv", (
        {"seed": SEED_BENCHMARK, "bits": case["bits"], "indice": case["indice"],
         "tipo_entrada": case["tipo"], "n": case["n"],
         "bases_20": json.dumps(case["bases"])} for case in inputs))
    rows = []
    for case in inputs:
        bits, n, kind, bases = (case["bits"], case["n"],
                                case["tipo"], case["bases"])
        methods = [("fermat", r) for r in ROUNDS] + [("miller_rabin", r) for r in ROUNDS]
        if bits <= TRIAL_MAX_BITS:
            methods.append(("division_prueba", 0))
        for method, rounds in methods:
            if method == "division_prueba":
                run = lambda: trial_division_with_count(n)
                result, divisions = run()
                outcome = "primo" if result else "compuesto"
                actual_rounds = squares = chain_squares = 0
            elif method == "fermat":
                run = lambda: fermat_test(n, bases[:rounds])
                detail = run()
                outcome = detail["resultado"]
                actual_rounds = detail["rondas_ejecutadas"]
                squares, chain_squares, divisions = detail["cuadrados_modulares"], 0, 0
            else:
                run = lambda: primality_report(n, rounds, bases=bases, presieve=False)
                detail = run()
                outcome = detail["resultado"]
                actual_rounds = detail["rondas_ejecutadas"]
                squares, chain_squares, divisions = (detail["cuadrados_modulares"],
                                                     detail["cuadrados_cadena"], 0)
            min_ns, median_ns, max_ns = measure(run)
            is_composite = kind == "compuesto_construido"
            rows.append({"seed": SEED_BENCHMARK, "bits": bits, "indice": case["indice"],
                         "tipo_entrada": kind, "n": n, "metodo": method,
                         "rondas_solicitadas": rounds, "rondas_ejecutadas": actual_rounds,
                         "cuadrados_modulares": squares, "cuadrados_cadena": chain_squares,
                         "divisiones": divisions, "resultado": outcome,
                         "falso_positivo_compuesto": is_composite and outcome not in ("compuesto",),
                         "repeticiones": REPETITIONS, "min_ns": min_ns,
                         "mediana_ns": median_ns, "max_ns": max_ns})
    write_csv("comparacion_metodos.csv", rows)
    summary = []
    for bits in SIZES:
        for kind in ("primo_verificado" if bits <= 32 else "probable_primo",
                     "compuesto_construido"):
            for method, rounds in [("fermat", r) for r in ROUNDS] + [
                    ("miller_rabin", r) for r in ROUNDS] + (
                        [("division_prueba", 0)] if bits <= 32 else []):
                subset = [r for r in rows if (r["bits"], r["tipo_entrada"],
                           r["metodo"], r["rondas_solicitadas"]) ==
                          (bits, kind, method, rounds)]
                summary.append({"seed": SEED_BENCHMARK, "bits": bits,
                                "tipo_entrada": kind, "metodo": method, "rondas": rounds,
                                "entradas": len(subset),
                                "tiempo_mediano_us": round(median(r["mediana_ns"]
                                                            for r in subset) / 1000, 3),
                                "rondas_mediana": median(r["rondas_ejecutadas"] for r in subset),
                                "cuadrados_mediana": median(r["cuadrados_modulares"] for r in subset),
                                "falsos_positivos": sum(r["falso_positivo_compuesto"]
                                                        for r in subset)})
        print(f"Comparación {bits:4d} bits: 16 entradas, métodos Fermat/MR "
              f"(1,5,10,20 rondas){' y división' if bits <= 32 else ''}")
    write_csv("resumen_comparacion.csv", summary)
    return rows, summary


def plot_timing(comparison):
    """Tiempo mediano por prueba; división solo donde es viable."""
    bits = list(SIZES)
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    primes = {"primo_verificado", "probable_primo"}
    for method, rounds, color, label in (("fermat", 20, "#dc681f", "Fermat, 20 bases"),
                                         ("miller_rabin", 1, "#198761", "MR, 1 ronda"),
                                         ("miller_rabin", 5, "#5458a6", "MR, 5 rondas"),
                                         ("miller_rabin", 20, "#2165ae", "MR, 20 rondas")):
        selected = [r for r in comparison if r["metodo"] == method
                    and r["rondas"] == rounds and r["tipo_entrada"] in primes]
        ax.plot(bits, [next(r["tiempo_mediano_us"] for r in selected
                            if r["bits"] == b) for b in bits], marker="o", color=color, label=label)
    trial = [r for r in comparison if r["metodo"] == "division_prueba"
             and r["tipo_entrada"] == "primo_verificado"]
    ax.plot([r["bits"] for r in trial], [r["tiempo_mediano_us"] for r in trial],
            "s--", color="#a5468b", label="División (solo 16/32 bits)")
    ax.set(xlabel="Longitud del candidato (bits)", ylabel="Tiempo mediano por prueba (µs)")
    ax.set_yscale("log")
    ax.legend(fontsize=8)
    fig.savefig(FIGURES / "fig1_tiempo_vs_bits.png")
    plt.close(fig)


def plot_squares(comparison):
    """Costo operacional de las rondas de Miller--Rabin."""
    bits = list(SIZES)
    primes = {"primo_verificado", "probable_primo"}
    fig, ax = plt.subplots(figsize=(8, 4.3))
    for rounds, color in ((1, "#198761"), (5, "#5458a6"),
                          (10, "#dc681f"), (20, "#2165ae")):
        selected = [r for r in comparison if r["metodo"] == "miller_rabin"
                    and r["rondas"] == rounds and r["tipo_entrada"] in primes]
        ax.plot(bits, [next(r["cuadrados_mediana"] for r in selected
                            if r["bits"] == b) for b in bits], marker="o", color=color,
                label=f"{rounds} rondas")
    ax.set(xlabel="Longitud del candidato (bits)",
           ylabel="Cuadrados modulares ejecutados (mediana)")
    ax.legend()
    fig.savefig(FIGURES / "fig2_cuadrados_vs_bits.png")
    plt.close(fig)


def plot_candidates(generation):
    """Candidatos por probable primo frente a la aproximación teórica."""
    bits = list(SIZES)
    fig, ax = plt.subplots(figsize=(8, 4.3))
    ax.plot(bits, [r["candidatos_media"] for r in generation], "o-",
            color="#2165ae", label="Media observada (30 primos/tamaño)")
    ax.plot(bits, [r["candidatos_estimados"] for r in generation], "s--",
            color="#dc681f", label="Aproximación: bits × ln(2) / 2")
    ax.set(xlabel="Longitud del candidato (bits)",
           ylabel="Candidatos impares por probable primo")
    ax.legend()
    fig.savefig(FIGURES / "fig3_candidatos_vs_bits.png")
    plt.close(fig)


def plot_error(error_rates):
    """Distingue tasa empírica, tasa exacta y cota superior."""
    fig, ax = plt.subplots(figsize=(8, 4.3))
    n = 25  # Ejemplo con mentirosos fuertes en el intervalo de bases válidas.
    selected = [r for r in error_rates if r["n"] == n]
    ax.plot(ROUNDS, [r["cota_teorica"] for r in selected], "s--",
            color="#dc681f", label="Cota universal 4⁻ʳ")
    ax.plot(ROUNDS, [r["tasa_exacta_bases_aleatorias"] for r in selected],
            "o-", color="#2165ae", label="Tasa exacta pₙʳ")
    observed = [r for r in selected if r["tasa_empirica"] > 0]
    ax.scatter([r["rondas"] for r in observed], [r["tasa_empirica"] for r in observed],
               color="#198761", marker="x", s=70, label="Observada: 3000 muestras")
    for row in selected:
        if row["tasa_empirica"] == 0:
            ax.annotate("0/3000", (row["rondas"], 2e-23), ha="center", fontsize=8,
                        color="#198761")
    ax.set(xlabel="Rondas independientes", ylabel="Fracción de compuestos aceptados")
    ax.set_yscale("log")
    ax.set_ylim(1e-23, 1)
    ax.set_xticks(ROUNDS)
    ax.legend(fontsize=8)
    fig.savefig(FIGURES / "fig4_error_empirico.png")
    plt.close(fig)


def plot(generation, comparison, error_rates):
    """Construye las cuatro figuras en la ejecución local completa."""
    plot_timing(comparison)
    plot_squares(comparison)
    plot_candidates(generation)
    plot_error(error_rates)


def latex_tables(generation, comparison, rates, liars, measurements):
    """Tablas generadas desde CSV/mediciones; evita valores inventados o viejos."""
    lines = [r"\begin{table}[htbp]\centering\small",
             r"\caption{Generación de 30 probables primos por longitud binaria}",
             r"\label{tab:generacion}",
             r"\begin{tabular}{rrrrrr}\toprule",
             r"Bits & Candidatos & Media & Mediana & Descartes & Tiempo med. (ms) \\",
             r"\midrule"]
    for row in generation:
        lines.append(f'{row["bits"]} & {row["candidatos_total"]} & '
                     f'{row["candidatos_media"]:.2f} & {row["candidatos_mediana"]} & '
                     f'{row["descartes_precribado"]} & {row["tiempo_mediano_ms"]:.3f} \\\\')
    lines += [r"\bottomrule\end{tabular}\end{table}",
              r"\begin{table}[htbp]\centering\small",
              r"\caption{Tiempo mediano por prueba sobre probables primos (µs)}",
              r"\label{tab:tiempos}",
              r"\begin{tabular}{rrrrrr}\toprule",
              r"Bits & División & Fermat 20 & MR 1 & MR 5 & MR 20 \\",
              r"\midrule"]
    def time_for(bits, method, rounds):
        row = next((r for r in comparison if r["bits"] == bits and r["metodo"] == method
                    and r["rondas"] == rounds and r["tipo_entrada"] != "compuesto_construido"), None)
        return f'{row["tiempo_mediano_us"]:.1f}' if row else "--"
    for bits in SIZES:
        lines.append(f"{bits} & {time_for(bits, 'division_prueba', 0)} & "
                     f"{time_for(bits, 'fermat', 20)} & {time_for(bits, 'miller_rabin', 1)} & "
                     f"{time_for(bits, 'miller_rabin', 5)} & "
                     f"{time_for(bits, 'miller_rabin', 20)} \\\\ ")
    lines += [r"\bottomrule\end{tabular}\end{table}",
               r"\begin{table}[htbp]\centering\small",
               r"\caption{Mínimo, mediana y máximo de siete pruebas sobre una misma entrada ($\mu$s)}",
               r"\label{tab:dispersion}",
               r"\begin{tabular}{rlrrr}\toprule",
               r"Bits & Método & Mínimo & Mediana & Máximo \\",
               r"\midrule"]
    for bits in (16, 32, 1024):
        for method, rounds, label in (("division_prueba", 0, "División"),
                                      ("miller_rabin", 20, "MR 20")):
            if method == "division_prueba" and bits > TRIAL_MAX_BITS:
                continue
            row = next(r for r in measurements if r["bits"] == bits and r["indice"] == 0
                       and r["tipo_entrada"] != "compuesto_construido"
                       and r["metodo"] == method and r["rondas_solicitadas"] == rounds)
            lines.append(f'{bits} & {label} & {row["min_ns"] / 1000:.1f} & '
                         f'{row["mediana_ns"] / 1000:.1f} & {row["max_ns"] / 1000:.1f} \\\\')
    lines += [r"\bottomrule\end{tabular}\end{table}",
               r"\begin{table}[htbp]\centering\small",
               r"\caption{Testigos y mentirosos fuertes: bases válidas de compuestos seleccionados}",
              r"\label{tab:mentirosos}",
              r"\begin{tabular}{rrrrr}\toprule",
              r"$n$ & Bases & Testigos & Mentirosos & Fracción \\",
              r"\midrule"]
    for n in (25, 91, 121, 221, 341, 561):
        row = next(r for r in liars if r["n"] == n)
        lines.append(f'{n} & {row["bases_validas"]} & {row["testigos"]} & '
                     f'{row["mentirosos_fuertes"]} & {row["fraccion_mentirosos"]:.4f} \\\\')
    lines += [r"\bottomrule\end{tabular}\end{table}",
              r"\begin{table}[htbp]\centering\small",
              r"\caption{Aceptación empírica y exacta de compuestos para 3000 ensayos por fila}",
              r"\label{tab:error}",
              r"\begin{tabular}{rrrrrr}\toprule",
              r"$n$ & Rondas & Aceptados & Frecuencia & Exacta $p_n^r$ & Cota $4^{-r}$ \\",
              r"\midrule"]
    for row in rates:
        if row["n"] in (25, 341, 561) and row["rondas"] in (1, 5, 20):
            lines.append(f'{row["n"]} & {row["rondas"]} & '
                         f'{row["compuestos_aceptados"]} & '
                         f'{row["tasa_empirica"]:.3g} & '
                         f'{row["tasa_exacta_bases_aleatorias"]:.3g} & '
                         f'{row["cota_teorica"]:.3g} \\\\')
    lines += [r"\bottomrule\end{tabular}\end{table}"]
    large = generation[-1]
    middle = next(row for row in generation if row["bits"] == 512)
    mr_1 = float(time_for(1024, "miller_rabin", 1))
    mr_20 = float(time_for(1024, "miller_rabin", 20))
    fermat_20 = float(time_for(1024, "fermat", 20))
    fraction = 100 * large["descartes_precribado"] / large["candidatos_total"]
    liar_341 = next(row for row in liars if row["n"] == 341)
    lines += [
        r"\noindent\textbf{Lectura cuantitativa de la generación.} " +
        f'Para 1024 bits se necesitaron {large["candidatos_total"]} candidatos '
        f'para 30 probables primos (media {large["candidatos_media"]:.2f}, '
        f'mediana {large["candidatos_mediana"]}); el precribado descartó '
        f'{large["descartes_precribado"]} ({fraction:.1f}\\%). '
        f'La referencia asintótica es {large["candidatos_estimados"]:.1f} '
        r'candidatos impares por primo. Para 512 bits, la media observada fue '
        f'{middle["candidatos_media"]:.2f} frente a '
        f'{middle["candidatos_estimados"]:.1f} estimados. '
        r'Las diferencias con la aproximación pueden reflejar variación muestral; '
        r'por sí solas no prueban ni descartan errores de primalidad.\par',
        r"\noindent\textbf{Lectura cuantitativa del costo y error.} " +
        f'Para 1024 bits, la mediana de Miller--Rabin con 20 rondas fue '
        f'{mr_20:.1f}~$\\mu$s frente a {mr_1:.1f}~$\\mu$s con una ronda '
        f'(razón {mr_20 / mr_1:.1f}); Fermat con 20 rondas tomó '
        f'{fermat_20:.1f}~$\\mu$s. '
        f'El compuesto 341 presentó {liar_341["mentirosos_fuertes"]} '
        f'mentirosos fuertes entre {liar_341["bases_validas"]} bases válidas: '
        f'$p_{{341}}={liar_341["fraccion_mentirosos"]:.4f}$. '
        r'El tiempo medido de Fermat no resuelve sus falsos positivos para Carmichael; '
        r'cero errores observados tras varias rondas no implica probabilidad cero.\par',
    ]
    # Archivos independientes: cada tabla se coloca junto a su interpretación.
    LATEX.mkdir(parents=True, exist_ok=True)
    names = ("generacion", "tiempos", "dispersion", "mentirosos", "error")
    starts = [i for i, line in enumerate(lines) if line.startswith(r"\begin{table}")]
    assert len(starts) == len(names)
    for name, start in zip(names, starts):
        end = lines.index(r"\bottomrule\end{tabular}\end{table}", start)
        content = "\n".join(lines[start:end + 1]).replace("[htbp]", "[H]") + "\n"
        (LATEX / f"04_tab_{name}.tex").write_text(content, encoding="utf-8")
    assert len(lines[end + 1:]) == 2
    for name, paragraph in zip(("generacion", "costo"), lines[end + 1:]):
        (LATEX / f"04_analisis_{name}.tex").write_text(paragraph + "\n", encoding="utf-8")


def main():
    for folder in (RESULTS, FIGURES, LATEX):
        folder.mkdir(parents=True, exist_ok=True)
    known_and_traces()
    liars, rates = liars_and_error()
    primes, generation = generate_primes()
    rows, comparison = compare_methods(primes)
    plot(generation, comparison, rates)
    latex_tables(generation, comparison, rates, liars, rows)
    print(f"OK: {len(primes) * PRIMES_PER_BITS} probables primos, "
          f"{len(rows)} comparaciones; CSV en {RESULTS}, PNG en {FIGURES}.")


if __name__ == "__main__":
    main()
