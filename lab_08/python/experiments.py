"""Escenarios A/B/C de la Guía 08. Produce CSV y PNG, sin datos fabricados.

Uso: python python/experiments.py [--max-k 14] [--repetitions 10]
La generación, instrumentación y escritura se excluyen de los cronómetros.
"""

import argparse
import csv
import json
import platform
import sys
from pathlib import Path
from statistics import median
from time import perf_counter_ns

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from case_generator import MANUAL_CASES, RANGES, SEED, SIZES, polynomial_pair
from ejercicios_resueltos import intt_direct, ntt_direct
from transforms import (MODULUS, PRIMITIVE_ROOT, OperationCounts,
                        convolution_fft_raw, fft, fft_iterative, ifft,
                        multiply_fft, multiply_ntt, naive_convolution,
                        next_power_of_two, ntt, validate_root)

BASE = Path(__file__).resolve().parent
RESULTS = BASE / "results"
FIGURES = BASE / "figures"
METHODS = ("directa", "fft_recursiva", "fft_iterativa", "ntt")
BENCHMARK_DIRECT_MAX = 2048
REPETITIONS = 10


def write_csv(name, rows, fields=None):
    rows = list(rows)
    fields = fields or (list(rows[0]) if rows else None)
    if fields is None:
        raise ValueError("Especifique las columnas de un CSV vacío")
    with (RESULTS / name).open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def measure(function, repetitions=REPETITIONS):
    """Mide SOLO la función preparada; resultados en ns, min <= med <= max."""
    if repetitions < 10:
        raise ValueError("La guía exige al menos diez repeticiones")
    times = []
    for _ in range(repetitions):
        start = perf_counter_ns()
        function()
        times.append(perf_counter_ns() - start)
    return min(times), median(times), max(times)


def manual_and_roots():
    manual = []
    for i, (a, b, expected) in enumerate(MANUAL_CASES):
        actual = naive_convolution(a, b)
        by_fft = multiply_fft(a, b)
        by_ntt = multiply_ntt(a, b, 17, 3)
        assert actual == expected == by_fft
        assert by_ntt == [x % 17 for x in expected]
        manual.append({"caso": i, "a": json.dumps(a), "b": json.dumps(b),
                       "esperado": json.dumps(expected), "directa": json.dumps(actual),
                       "fft": json.dumps(by_fft), "ntt_mod_17": json.dumps(by_ntt)})
    write_csv("casos_manuales.csv", manual)

    roots = []
    for p, generator, max_n in ((17, 3, 16), (MODULUS, PRIMITIVE_ROOT, 1 << 23)):
        n = 1
        while n <= max_n:
            root = pow(generator, (p - 1) // n, p)
            assert validate_root(root, n, p)
            roots.append({"modulo": p, "generador": generator, "n": n,
                          "raiz_orden_n": root, "orden": n,
                          "valida": True, "n_maxima": max_n})
            n *= 2
    write_csv("modulos_raices.csv", roots)
    return manual, roots


def correctness(max_k):
    """Escenario A: diferencias con oráculos y rondas directas/inversas."""
    rows, fft_roundtrips, ntt_roundtrips = [], [], []
    discrepancy_fields = ("escenario", "metodo", "n", "rango", "seed", "a", "b",
                          "esperado", "obtenido")
    discrepancies = []
    for k in range(3, min(max_k, 7) + 1):
        n = 1 << k
        for label, bounds in (*RANGES.items(), ("residuos", (0, MODULUS - 1))):
            seed = SEED + k * 17 + len(label)
            a, b = polynomial_pair(n, seed, bounds)
            direct = naive_convolution(a, b)
            modular = [x % MODULUS for x in direct]
            matches = {"directa": direct, "ntt": multiply_ntt(a, b, MODULUS, PRIMITIVE_ROOT)}
            for method in ("recursive", "iterative"):
                try:
                    matches[f"fft_{'recursiva' if method == 'recursive' else 'iterativa'}"] = (
                        multiply_fft(a, b, tolerance=1e-7, method=method))
                except ArithmeticError:
                    matches[f"fft_{'recursiva' if method == 'recursive' else 'iterativa'}"] = None
            for method in METHODS:
                output = matches[method]
                expected = modular if method == "ntt" else direct
                success = output == expected
                rows.append({"n_entrada": n, "n_fft": next_power_of_two(2*n-1),
                             "rango": label, "seed": seed, "metodo": method,
                             "coincide": success, "salida_longitud": len(output) if output else 0,
                             "referencia_longitud": len(expected)})
                if not success:
                    discrepancies.append(dict(zip(discrepancy_fields,
                        ("correccion", method, n, label, seed, json.dumps(a), json.dumps(b),
                         json.dumps(expected), json.dumps(output)))))
            # Para números de casi 1e9, el redondeo complejo NO está garantizado;
            # el escenario C cuantifica esos casos, no se finge corrección.
            if label != "residuos":
                assert all(r["coincide"] for r in rows[-4:]), (n, label)
            else:
                assert matches["ntt"] == modular

        seed = SEED + k
        a, _ = polynomial_pair(n, seed)
        original = a.copy()
        rec = ifft(fft(a))
        iterative = a.copy()
        fft_iterative(iterative)
        difference = max(abs(x-y) for x, y in zip(fft(a), iterative))
        fft_iterative(iterative, invert=True)
        err_rec = max(abs(x-y) for x, y in zip(a, rec))
        err_iter = max(abs(x-y) for x, y in zip(a, iterative))
        assert max(err_rec, err_iter, difference) < 1e-7 and a == original
        fft_roundtrips.append({"n": n, "seed": seed, "error_recursiva": err_rec,
                               "error_iterativa": err_iter, "diferencia_fft": difference})
        root = pow(PRIMITIVE_ROOT, (MODULUS - 1) // n, MODULUS)
        transformed = ntt(a, False, MODULUS, root)
        recovered = ntt(transformed, True, MODULUS, root)
        assert recovered == [x % MODULUS for x in a]
        ntt_roundtrips.append({"n": n, "seed": seed, "modulo": MODULUS,
                               "raiz": root, "coincide": True})
        if n <= 16:
            root_17 = pow(3, 16 // n, 17)
            assert ntt(a, False, 17, root_17) == ntt_direct(a, root_17, 17)
            assert intt_direct(ntt_direct(a, root_17, 17), root_17, 17) == [x % 17 for x in a]
    write_csv("validacion_diferencial.csv", rows)
    write_csv("validacion_fft_ifft.csv", fft_roundtrips)
    write_csv("validacion_ntt_intt.csv", ntt_roundtrips)
    write_csv("discrepancias.csv", discrepancies, discrepancy_fields)
    return rows, discrepancies


def run_method(method, a, b, stats=None):
    if method == "directa":
        return naive_convolution(a, b, stats=stats)
    if method == "fft_recursiva":
        return multiply_fft(a, b, method="recursive", stats=stats)
    if method == "fft_iterativa":
        return multiply_fft(a, b, method="iterative", stats=stats)
    return multiply_ntt(a, b, MODULUS, PRIMITIVE_ROOT, stats=stats)


def performance(max_k, repetitions):
    """Escenario B: diez repeticiones, tamaños 2^3..2^14; directo hasta 2048."""
    rows = []
    for n in SIZES:
        if n > (1 << max_k):
            break
        seed = SEED + n
        a, b = polynomial_pair(n, seed)
        # Oráculo completo para tamaños medibles; para el resto basta
        # equivalencia recursiva/iterativa y NTT == FFT módulo p.
        expected = naive_convolution(a, b) if n <= BENCHMARK_DIRECT_MAX else None
        reference = expected if expected is not None else multiply_fft(a, b)
        for method in METHODS:
            if method == "directa" and n > BENCHMARK_DIRECT_MAX:
                continue  # límite documentado, sin extrapolar tiempos falsos
            counts = OperationCounts()
            obtained = run_method(method, a, b, stats=counts)
            comparison = [x % MODULUS for x in reference] if method == "ntt" else reference
            assert obtained == comparison, (n, method)
            minimum, middle, maximum = measure(lambda: run_method(method, a, b), repetitions)
            rows.append({"n_entrada": n, "n_transformada": next_power_of_two(2*n-1),
                         "metodo": method, "rango": "[-10,10]", "modulo": MODULUS if method == "ntt" else "",
                         "generador": PRIMITIVE_ROOT if method == "ntt" else "", "seed": seed,
                         "repeticiones": repetitions, "min_ns": minimum, "mediana_ns": middle,
                         "max_ns": maximum, "mariposas": counts.butterflies,
                         "multiplicaciones": counts.multiplications,
                         "sumas": counts.additions, "etapas": counts.stages,
                         "coincide_referencia": True, "python": platform.python_version(),
                         "sistema": platform.platform(), "procesador": platform.processor()})
        print(f"B: n={n:<5} metodos={len(METHODS) if expected is not None else 3} OK", flush=True)
    write_csv("rendimiento.csv", rows)
    crossing = []
    for method in METHODS[1:]:
        direct = {r["n_entrada"]: r["mediana_ns"] for r in rows if r["metodo"] == "directa"}
        faster = [r["n_entrada"] for r in rows if r["metodo"] == method
                  and r["n_entrada"] in direct and r["mediana_ns"] < direct[r["n_entrada"]]]
        crossing.append({"metodo": method, "primer_n_supera_directa": min(faster) if faster else "",
                         "ultimo_n_directa_medido": max(direct),
                         "criterio": "mediana_ns menor que directa en el mismo n"})
    write_csv("puntos_cruce.csv", crossing)
    return rows, crossing


def accuracy(max_k):
    """Escenario C: errores antes de redondear y primer fallo por orden de exploración."""
    rows, first_failure = [], None
    for k in range(3, min(max_k, 10) + 1):
        n = 1 << k
        for magnitude in (10, 1000, 100000, 10000000, 1000000000):
            seed = SEED + 100000 + k * 31 + magnitude
            a, b = polynomial_pair(n, seed, (-magnitude, magnitude))
            exact = naive_convolution(a, b)
            modular = multiply_ntt(a, b, MODULUS, PRIMITIVE_ROOT)
            assert modular == [x % MODULUS for x in exact]
            for method in ("recursive", "iterative"):
                raw = convolution_fft_raw(a, b, method=method)
                real_err = max(abs(z.real - x) for z, x in zip(raw, exact))
                imag_err = max(abs(z.imag) for z in raw)
                mismatch = sum(round(z.real) != x for z, x in zip(raw, exact))
                rows.append({"n_entrada": n, "n_transformada": next_power_of_two(2*n-1),
                             "magnitud_maxima": magnitude, "seed": seed, "metodo": method,
                             "error_real_max": real_err, "error_imaginario_max": imag_err,
                             "coeficientes_erroneos": mismatch,
                             "ntt_exacta_modulo_p": True, "modulo": MODULUS})
                if mismatch and first_failure is None:
                    index = next(i for i, (z, x) in enumerate(zip(raw, exact)) if round(z.real) != x)
                    first_failure = {"n": n, "magnitud": magnitude, "seed": seed,
                                     "metodo": method, "indice": index,
                                     "esperado": exact[index], "redondeado": round(raw[index].real),
                                     "real": raw[index].real, "imaginario": raw[index].imag,
                                     "a": json.dumps(a), "b": json.dumps(b)}
    write_csv("error_fft.csv", rows)
    write_csv("primer_fallo_fft.csv", [first_failure] if first_failure else [],
              ("n", "magnitud", "seed", "metodo", "indice", "esperado",
               "redondeado", "real", "imaginario", "a", "b"))
    return rows, first_failure


def plot(performance_rows, accuracy_rows):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.grid": True, "figure.dpi": 300})
    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=300)
    for method in METHODS:
        selected = [r for r in performance_rows if r["metodo"] == method]
        ax.plot([r["n_entrada"] for r in selected],
                [r["mediana_ns"] / 1e6 for r in selected], "o-", label=method)
    ax.set(xlabel="Coeficientes por entrada (n)", ylabel="Mediana (ms)",
           title="Multiplicación de polinomios: tiempo frente a tamaño")
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES / "tiempo_vs_n.png", dpi=300)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=300)
    for method in METHODS:
        selected = [r for r in performance_rows if r["metodo"] == method]
        ax.plot([r["n_entrada"] for r in selected],
                [r["mariposas"] if r["mariposas"] else r["multiplicaciones"] for r in selected],
                "o-", label=method)
    ax.set(xlabel="Coeficientes por entrada (n)", ylabel="Mariposas (directa: productos)",
           title="Trabajo contado: transformadas y método directo")
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES / "operaciones_vs_n.png", dpi=300)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=300)
    for method in ("recursive", "iterative"):
        selected = [r for r in accuracy_rows if r["metodo"] == method and
                    r["magnitud_maxima"] in (1000, 1000000000)]
        for magnitude in (1000, 1000000000):
            subset = [r for r in selected if r["magnitud_maxima"] == magnitude]
            ax.plot([r["n_entrada"] for r in subset],
                    [max(r["error_real_max"], 1e-16) for r in subset], "o-",
                    label=f"{method}, ±{magnitude:g}")
    ax.set(xlabel="Coeficientes por entrada (n)", ylabel="Error real máximo (abs)",
           title="Error FFT antes de redondear")
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURES / "error_fft_vs_n.png", dpi=300)
    plt.close(fig)


def main(max_k=14, repetitions=REPETITIONS):
    if max_k < 3 or max_k > 14 or repetitions < 10:
        raise ValueError("3 <= max_k <= 14 y repeticiones >= 10")
    RESULTS.mkdir(exist_ok=True)
    FIGURES.mkdir(exist_ok=True)
    manual, roots = manual_and_roots()
    checked, discrepancies = correctness(max_k)
    performance_rows, crossings = performance(max_k, repetitions)
    accuracy_rows, first = accuracy(max_k)
    plot(performance_rows, accuracy_rows)
    print(f"A: {len(manual)} casos manuales, {len(checked)} comparaciones, "
          f"{len(discrepancies)} discrepancias (rango [0,p-1] puede fallar en FFT).")
    print(f"B: {len(performance_rows)} mediciones, {repetitions} repeticiones; cruces: {crossings}")
    print(f"C: {len(accuracy_rows)} filas; primer fallo: "
          f"{ {k:v for k,v in first.items() if k not in ('a','b')} if first else 'ninguno'}")
    print(f"Raíces válidas: {len(roots)}; CSV={RESULTS}, PNG={FIGURES}")
    return {"manual": manual, "roots": roots, "checked": checked,
            "performance": performance_rows, "crossings": crossings,
            "accuracy": accuracy_rows, "first": first}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-k", type=int, default=14)
    parser.add_argument("--repetitions", type=int, default=10)
    args = parser.parse_args()
    main(args.max_k, args.repetitions)
