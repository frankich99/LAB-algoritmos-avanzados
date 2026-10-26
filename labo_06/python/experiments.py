"""
experiments.py
==============

Escenarios experimentales A, B y C de la Guía 06 (Ejercicio propuesto 2) y
generación de tablas (CSV) y gráficos (PNG). Totalmente reproducible: cada
escenario usa su propia semilla fija, registrada en los CSV.

Uso:  python experiments.py     (o ejecutar las celdas del notebook en Colab)
"""

import csv
import math
import os
from statistics import mean, median
from time import perf_counter_ns

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from number_theory import (crt_with_trace, extended_gcd, gcd_trace,
                           modular_inverse, modular_pow,
                           naive_pow_multiplications, solve_linear_congruence,
                           validate_crt_solution, crt)
from case_generator import (FIB_PAIRS, exponent_with_popcount, make_rng,
                            random_congruence, random_crt_system,
                            random_int_bits, random_pair)

RESULTS = "results"
FIGURES = "figures"
os.makedirs(RESULTS, exist_ok=True)
os.makedirs(FIGURES, exist_ok=True)

SEED_A, SEED_B, SEED_C = 6001, 6002, 6003
BITS_A = [8, 16, 32, 64, 128, 256, 512]
PAIRS_PER_BITS = 1000                      # 7 x 1000 = 7000 pares (>= 5000)
BITS_B = [8, 16, 32, 64, 128, 256, 512, 1024]
EXPONENTS_PER_BITS = 30
PHI = (1 + 5 ** 0.5) / 2

# Paleta (referencia validada, slots 1-3) y estilo sobrio para impresión
C1, C2, C3 = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({
    "font.family": "DejaVu Serif", "font.size": 10,
    "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
    "ytick.color": INK2, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
    "lines.linewidth": 2, "lines.markersize": 6, "legend.frameon": False,
    "figure.dpi": 150, "savefig.bbox": "tight",
})


def measure(function, repetitions=10):
    """Medición de la guía: devuelve mínimo, mediana y máximo en nanosegundos."""
    times = []
    for _ in range(repetitions):
        start = perf_counter_ns()
        function()
        end = perf_counter_ns()
        times.append(end - start)
    return {"min_ns": min(times), "median_ns": median(times), "max_ns": max(times)}


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# Escenario A: pruebas diferenciales de Euclides
# ---------------------------------------------------------------------------
def scenario_a():
    rng = make_rng(SEED_A)
    pairs = [(bits, *random_pair(rng, bits)) for bits in BITS_A
             for _ in range(PAIRS_PER_BITS)]          # entradas generadas antes de medir
    rows, discrepancies = [], []
    for idx, (bits, a, b) in enumerate(pairs):
        d, trace = gcd_trace(a, b)
        d2, x, y = extended_gcd(a, b)
        ok_gcd = d == math.gcd(a, b)
        ok_bezout = (a * x + b * y == d2) and d2 == d
        if not (ok_gcd and ok_bezout):
            discrepancies.append({"seed": SEED_A, "index": idx, "a": a, "b": b})
        rows.append({"seed": SEED_A, "index": idx, "bits": bits, "a": a, "b": b,
                     "gcd": d, "divisions": len(trace),
                     "bit_length_min": min(abs(a), abs(b)).bit_length(),
                     "gcd_ok": ok_gcd, "bezout_ok": ok_bezout})
    write_csv(f"{RESULTS}/escenario_A_euclides.csv", rows)
    if discrepancies:
        write_csv(f"{RESULTS}/escenario_A_discrepancias.csv", discrepancies)

    summary = []
    for bits in BITS_A:
        sub = [r for r in rows if r["bits"] == bits]
        divs = [r["divisions"] for r in sub]
        summary.append({
            "bits": bits, "pares": len(sub),
            "div_media": round(mean(divs), 2), "div_mediana": median(divs),
            "div_max": max(divs),
            "teorico_medio": round(12 * math.log(2) ** 2 / math.pi ** 2 * bits, 2),
            "cota_lame": math.ceil(bits * math.log(2) / math.log(PHI)) + 1,
            "mcd_1_pct": round(100 * sum(r["gcd"] == 1 for r in sub) / len(sub), 1),
            "gcd_ok": all(r["gcd_ok"] for r in sub),
            "bezout_ok": all(r["bezout_ok"] for r in sub),
        })
    write_csv(f"{RESULTS}/escenario_A_resumen.csv", summary)

    # Tabla de MCD de casos representativos y Fibonacci
    examples = [(252, 105), (-252, 105), (48, 180), (35, 64), (17, 0), (0, 17)] + FIB_PAIRS
    ex_rows = []
    for a, b in examples:
        d, trace = gcd_trace(a, b)
        _, x, y = extended_gcd(a, b)
        ex_rows.append({"a": a, "b": b, "mcd": d, "divisiones": len(trace),
                        "bits": max(abs(a), abs(b)).bit_length(), "x": x, "y": y,
                        "bezout": a * x + b * y == d})
    write_csv(f"{RESULTS}/tabla_mcd_ejemplos.csv", ex_rows)

    # Tiempos de Euclides por tamaño (sobre 50 pares fijos por tamaño)
    time_rows = []
    for bits in BITS_A:
        sub = [(a, b) for (bb, a, b) in pairs if bb == bits][:50]
        t = measure(lambda: [gcd_trace(a, b) for a, b in sub], repetitions=7)
        time_rows.append({"bits": bits, "pares": len(sub),
                          "median_us_por_par": round(t["median_ns"] / len(sub) / 1000, 3),
                          "min_us_por_par": round(t["min_ns"] / len(sub) / 1000, 3),
                          "max_us_por_par": round(t["max_ns"] / len(sub) / 1000, 3)})
    write_csv(f"{RESULTS}/escenario_A_tiempos.csv", time_rows)

    # Figura 1: divisiones vs bits
    fig, ax = plt.subplots(figsize=(6.2, 3.8))
    ax.plot(BITS_A, [s["cota_lame"] for s in summary], color=C2, marker="s",
            linestyle="--", label="Cota de Lamé (peor caso)")
    ax.plot(BITS_A, [s["div_max"] for s in summary], color=C3, marker="^",
            label="Máximo observado")
    ax.plot(BITS_A, [s["div_media"] for s in summary], color=C1, marker="o",
            label="Media observada")
    ax.plot(BITS_A, [s["teorico_medio"] for s in summary], color=INK2,
            linestyle=":", linewidth=1.5, label="Media teórica ≈ 0.584·bits")
    ax.set_xticks([8, 64, 128, 256, 512])
    ax.set_xlabel("Longitud en bits de a y b")
    ax.set_ylabel("Número de divisiones")
    ax.legend(loc="upper left")
    fig.savefig(f"{FIGURES}/fig1_euclides_divisiones.png")
    plt.close(fig)
    return summary, ex_rows, time_rows, discrepancies


# ---------------------------------------------------------------------------
# Escenario B: potencia modular binaria
# ---------------------------------------------------------------------------
def scenario_b():
    rng = make_rng(SEED_B)
    modulus = random_int_bits(rng, 1024) | 1          # módulo fijo de 1024 bits
    base = rng.randrange(2, modulus)
    exps = []
    for bits in BITS_B:
        for _ in range(EXPONENTS_PER_BITS):
            exps.append(("aleatorio", bits, random_int_bits(rng, bits)))
        exps.append(("pocos_unos", bits, exponent_with_popcount(rng, bits, 1)))
        exps.append(("todos_unos", bits, (1 << bits) - 1))
    rows = []
    for kind, bits, e in exps:
        value, sq, pr = modular_pow(base, e, modulus)
        assert value == pow(base, e, modulus)
        t = measure(lambda: modular_pow(base, e, modulus), repetitions=10)
        naive = naive_pow_multiplications(e)
        rows.append({"seed": SEED_B, "tipo": kind, "bits_exponente": e.bit_length(),
                     "unos": bin(e).count("1"), "cuadrados": sq, "productos": pr,
                     "total_binario": sq + pr,
                     "directo_e_menos_1_log10": round(math.log10(naive), 2) if naive else 0,
                     "median_us": round(t["median_ns"] / 1000, 2),
                     "min_us": round(t["min_ns"] / 1000, 2),
                     "max_us": round(t["max_ns"] / 1000, 2),
                     "coincide_pow": True})
    write_csv(f"{RESULTS}/escenario_B_potencia.csv", rows)

    summary = []
    for bits in BITS_B:
        sub = [r for r in rows if r["bits_exponente"] == bits and r["tipo"] == "aleatorio"]
        lo = next(r for r in rows if r["bits_exponente"] == bits and r["tipo"] == "pocos_unos")
        hi = next(r for r in rows if r["bits_exponente"] == bits and r["tipo"] == "todos_unos")
        summary.append({
            "bits": bits, "cuadrados": sub[0]["cuadrados"],
            "productos_medios": round(mean(r["productos"] for r in sub), 1),
            "total_min": lo["total_binario"], "total_medio": round(mean(r["total_binario"] for r in sub), 1),
            "total_max": hi["total_binario"],
            "directo_log10": round(mean(r["directo_e_menos_1_log10"] for r in sub), 1),
            "t_med_us": round(median(r["median_us"] for r in sub), 1),
            "t_pocos_unos_us": lo["median_us"], "t_todos_unos_us": hi["median_us"],
        })
    write_csv(f"{RESULTS}/escenario_B_resumen.csv", summary)

    # Comparación real con el método directo solo para exponentes pequeños
    small = []
    for e in [2 ** 8 - 1, 2 ** 12 - 1, 2 ** 16 - 1]:
        def naive():
            r = 1
            for _ in range(e):
                r = (r * base) % modulus
            return r
        assert naive() == pow(base, e, modulus)
        tn = measure(naive, repetitions=3)
        tb = measure(lambda: modular_pow(base, e, modulus), repetitions=10)
        _, sq, pr = modular_pow(base, e, modulus)
        small.append({"e": e, "bits": e.bit_length(), "mult_directo": e - 1,
                      "mult_binario": sq + pr,
                      "t_directo_us": round(tn["median_ns"] / 1000, 1),
                      "t_binario_us": round(tb["median_ns"] / 1000, 1),
                      "aceleracion": round(tn["median_ns"] / tb["median_ns"], 1)})
    write_csv(f"{RESULTS}/escenario_B_directo_vs_binario.csv", small)

    # Figura 2: operaciones vs bits del exponente
    fig, ax = plt.subplots(figsize=(6.2, 3.8))
    ax.fill_between(BITS_B, [s["total_min"] for s in summary],
                    [s["total_max"] for s in summary], color=C1, alpha=0.12, linewidth=0,
                    label="Rango: 1 bit en 1 … todos en 1")
    ax.plot(BITS_B, [s["total_medio"] for s in summary], color=C1, marker="o",
            label="Total (cuadrados + productos)")
    ax.plot(BITS_B, [s["cuadrados"] for s in summary], color=C2, marker="s",
            label="Cuadrados")
    ax.plot(BITS_B, [s["productos_medios"] for s in summary], color=C3, marker="^",
            label="Productos seleccionados (media)")
    ax.set_xlabel("Bits del exponente")
    ax.set_ylabel("Multiplicaciones modulares")
    ax.legend(loc="upper left")
    fig.savefig(f"{FIGURES}/fig2_potencia_operaciones.png")
    plt.close(fig)

    # Figura 3: e - 1 frente al método binario (escala log10)
    fig, ax = plt.subplots(figsize=(6.2, 3.8))
    ax.plot(BITS_B, [s["directo_log10"] for s in summary], color=C2, marker="s",
            label="Método directo: e − 1")
    ax.plot(BITS_B, [math.log10(s["total_medio"]) for s in summary], color=C1,
            marker="o", label="Método binario: cuadrados + productos")
    ax.set_xlabel("Bits del exponente")
    ax.set_ylabel("log₁₀(multiplicaciones)")
    ax.legend(loc="upper left")
    for s in summary[-1:]:
        ax.annotate(rf"$\approx 10^{{{s['directo_log10']:.0f}}}$", (s["bits"], s["directo_log10"]),
                    textcoords="offset points", xytext=(-40, -14), color=INK2, fontsize=9)
        ax.annotate(f"{s['total_medio']:.0f}", (s["bits"], math.log10(s["total_medio"])),
                    textcoords="offset points", xytext=(-22, 8), color=INK2, fontsize=9)
    fig.savefig(f"{FIGURES}/fig3_directo_vs_binario.png")
    plt.close(fig)

    # Figura 4: efecto de la cantidad de unos (exponente de 1024 bits)
    pc_rows = []
    for ones in [1, 64, 128, 256, 384, 512, 640, 768, 896, 1024]:
        e = exponent_with_popcount(rng, 1024, ones)
        _, sq, pr = modular_pow(base, e, modulus)
        t = measure(lambda: modular_pow(base, e, modulus), repetitions=15)
        pc_rows.append({"unos": ones, "cuadrados": sq, "productos": pr,
                        "total": sq + pr, "median_us": round(t["median_ns"] / 1000, 1)})
    write_csv(f"{RESULTS}/escenario_B_unos_1024bits.csv", pc_rows)
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    ax.plot([r["unos"] for r in pc_rows], [r["median_us"] for r in pc_rows],
            color=C1, marker="o")
    ax.set_xlabel("Cantidad de bits iguales a 1 en un exponente de 1024 bits")
    ax.set_ylabel("Tiempo mediano (µs)")
    ax.set_ylim(bottom=0)
    fig.savefig(f"{FIGURES}/fig4_unos_tiempo.png")
    plt.close(fig)
    return summary, small, pc_rows


# ---------------------------------------------------------------------------
# Escenario C: inversos, congruencias y TCR
# ---------------------------------------------------------------------------
def scenario_c():
    rng = make_rng(SEED_C)
    # Inversos
    inv_rows, inv_ok = [], True
    for _ in range(2000):
        n = rng.randint(2, 10_000)
        a = rng.randint(-20_000, 20_000)
        d = math.gcd(a, n)
        try:
            u = modular_inverse(a, n)
            existe, valido = True, (a * u) % n == 1
        except ValueError:
            u, existe, valido = None, False, True
        inv_ok &= (existe == (d == 1)) and valido
        inv_rows.append({"seed": SEED_C, "a": a, "n": n, "mcd": d,
                         "inverso": u, "existe": existe, "valido": valido})
    write_csv(f"{RESULTS}/escenario_C_inversos.csv", inv_rows)
    inv_example = [(7, 40), (-3, 11), (47, 40), (17, 3120), (6, 9), (10, 25), (0, 7), (14, 100)]
    inv_table = []
    for a, n in inv_example:
        try:
            u = modular_inverse(a, n)
            inv_table.append({"a": a, "n": n, "mcd": math.gcd(a, n), "resultado": u,
                              "verificacion": f"({a}·{u}) mod {n} = {(a*u) % n}"})
        except ValueError:
            inv_table.append({"a": a, "n": n, "mcd": math.gcd(a, n),
                              "resultado": "Rechazado", "verificacion": "ValueError"})

    # Congruencias
    cong_rows, cong_ok = [], True
    for i in range(2000):
        a, b, n = random_congruence(rng, force_solvable=(i % 2 == 0))
        d = math.gcd(a, n)
        sol = solve_linear_congruence(a, b, n)
        expected = d if b % d == 0 else 0
        valid = all((a * x - b) % n == 0 and 0 <= x < n for x in sol)
        cong_ok &= (len(sol) == expected) and valid
        cong_rows.append({"seed": SEED_C, "a": a, "b": b, "n": n, "mcd": d,
                          "esperadas": expected, "obtenidas": len(sol), "validas": valid})
    write_csv(f"{RESULTS}/escenario_C_congruencias.csv", cong_rows)
    cong_example = [(14, 30, 100), (6, 4, 9), (7, 3, 40), (12, 18, 30), (-4, 6, 10), (35, 10, 50)]
    cong_table = []
    for a, b, n in cong_example:
        d = math.gcd(a, n)
        sol = solve_linear_congruence(a, b, n)
        cong_table.append({"congruencia": f"{a}x ≡ {b} (mod {n})", "mcd": d,
                           "esperadas": d if b % d == 0 else 0, "obtenidas": len(sol),
                           "soluciones": ", ".join(map(str, sol)) if sol else "—"})

    # TCR
    crt_rows, crt_ok = [], True
    for _ in range(1000):
        k = rng.randint(1, 6)
        x_known, r, m = random_crt_system(rng, k)
        x, N = crt(r, m)
        ok = x == x_known % N and validate_crt_solution(x, r, m)
        crt_ok &= ok
        crt_rows.append({"seed": SEED_C, "k": k, "residuos": r, "modulos": m,
                         "x_conocida": x_known, "x": x, "N": N, "ok": ok})
    write_csv(f"{RESULTS}/escenario_C_tcr.csv", crt_rows)
    _, _, crt_trace = crt_with_trace([2, 3, 2], [3, 5, 7])
    write_csv(f"{RESULTS}/traza_tcr_caso_obligatorio.csv", crt_trace)
    stats = {
        "inversos": len(inv_rows), "inv_existen": sum(r["existe"] for r in inv_rows),
        "inv_ok": inv_ok, "congruencias": len(cong_rows),
        "cong_con_sol": sum(r["esperadas"] > 0 for r in cong_rows), "cong_ok": cong_ok,
        "tcr": len(crt_rows), "tcr_ok": crt_ok,
    }
    return inv_table, cong_table, crt_trace, stats


if __name__ == "__main__":
    A = scenario_a()
    print("A resumen:", *A[0], sep="\n")
    print("A tiempos:", *A[2], sep="\n")
    print("Discrepancias:", len(A[3]))
    B = scenario_b()
    print("B resumen:", *B[0], sep="\n")
    print("B directo:", *B[1], sep="\n")
    print("B unos:", *B[2], sep="\n")
    C = scenario_c()
    print("C inv:", *C[0], sep="\n")
    print("C cong:", *C[1], sep="\n")
    print("C traza:", *C[2], sep="\n")
    print("C stats:", C[3])
