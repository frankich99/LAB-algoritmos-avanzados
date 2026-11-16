"""Actualiza fragmentos LaTeX generados desde código y CSV reales."""

import csv
import inspect
from pathlib import Path
from pprint import pformat

from ejercicios_resueltos import resuelto_1, resuelto_2, resuelto_3

BASE = Path(__file__).resolve().parent
OUTPUT = BASE.parent / "latex" / "secciones"


def data(name):
    with (BASE / "results" / name).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def table(caption, columns, rows, label=None):
    """Tabla booktabs; las celdas son LaTeX generado/controlado localmente."""
    header = " & ".join(columns) + r" \\" + "\n"
    body = "".join(" & ".join(str(v) for v in row) + r" \\" + "\n" for row in rows)
    label_str = f"\\label{{{label}}}\n" if label else ""
    return (r"\begin{table}[htbp]\centering\small" + "\n"
            + r"\caption{" + caption + "}\n"
            + label_str
            + r"\begin{tabular}{" + "r" * len(columns) + r"}\toprule" + "\n"
            + header + r"\midrule" + "\n" + body
            + r"\bottomrule\end{tabular}\end{table}" + "\n")


def render():
    ejercicios = (
        (1, resuelto_1, "Ejercicio resuelto 1: convolución directa"),
        (2, resuelto_2, "Ejercicio resuelto 2: FFT, IFFT y multiplicación"),
        (3, resuelto_3, "Ejercicio resuelto 3: NTT e INTT directa en F17"),
    )
    for num, func, title in ejercicios:
        code_src = inspect.getsource(func).rstrip()
        out_src = pformat(func(), width=80, sort_dicts=False)
        content = (
            f"\\begin{{lstlisting}}[language=Python,caption={{{title}}}]\n"
            f"{code_src}\n"
            f"\\end{{lstlisting}}\n"
            f"\\noindent\\textbf{{Resultado de la ejecución:}}\n"
            f"\\begin{{lstlisting}}[style=consolestyle]\n"
            f">>> {func.__name__}()\n{out_src}\n"
            f"\\end{{lstlisting}}\n"
        )
        (OUTPUT / f"02_resuelto_{num}_generado.tex").write_text(content, encoding="utf-8")

    manual = data("casos_manuales.csv")
    roots = data("modulos_raices.csv")
    performance = data("rendimiento.csv")
    crossing = data("puntos_cruce.csv")
    error = data("error_fft.csv")
    first = data("primer_fallo_fft.csv")
    fft_validation = data("validacion_fft_ifft.csv")
    ntt_validation = data("validacion_ntt_intt.csv")
    diff = data("validacion_diferencial.csv")
    discrepancies = data("discrepancias.csv")
    sections = []
    sections.append(table("Casos manuales (coeficientes en orden ascendente)",
                          ["Caso", "$a$", "$b$", "$c$"],
                          [(r["caso"], r["a"], r["b"], r["esperado"]) for r in manual],
                          label="tab:manuales"))
    sections.append(table("Transformadas directas/inversas y diferencia FFT recursiva/iterativa",
                          ["$n$", "Error FFT/IFFT", "Error iterativa", "Diferencia FFT"],
                          [(r["n"], f'{float(r["error_recursiva"]):.2g}',
                            f'{float(r["error_iterativa"]):.2g}',
                            f'{float(r["diferencia_fft"]):.2g}') for r in fft_validation],
                          label="tab:validacion_fft"))
    sections.append(table("NTT/INTT: recuperación exacta módulo $998244353$",
                          ["$n$", "Raíz", "Recupera módulo $p$"],
                          [(r["n"], r["raiz"], "sí") for r in ntt_validation],
                          label="tab:validacion_ntt"))
    sections.append(table("Primos, generadores, raíces y longitudes NTT seleccionadas",
                          ["$p$", "Generador", "$N$", "$\\omega_N$", "$N_{max}$"],
                          [(r["modulo"], r["generador"], r["n"], r["raiz_orden_n"], r["n_maxima"])
                           for r in roots if int(r["n"]) in (1, 2, 4, 8, 16, 32768, 1 << 23)],
                          label="tab:modulos_raices"))
    grouped = {(int(r["n_entrada"]), r["metodo"]): r for r in performance}
    sizes = sorted({n for n, _ in grouped})
    def ms(n, method):
        row = grouped.get((n, method))
        return f'{float(row["mediana_ns"])/1e6:.3f}' if row else "--"
    sections.append(table("Tiempo mediano en ms, 10 repeticiones o más; --: no medido",
                          ["$n$", "Directa", "FFT rec.", "FFT iter.", "NTT"],
                          [(n, ms(n, "directa"), ms(n, "fft_recursiva"),
                            ms(n, "fft_iterativa"), ms(n, "ntt")) for n in sizes],
                          label="tab:tiempos"))
    sections.append(table("Operaciones ejecutadas en multiplicación; cada mariposa incluye 2 sumas y 2 productos",
                          ["$n$", "Productos directa", "Mariposas FFT", "Mariposas NTT", "Etapas"],
                          [(n, grouped[(n, "directa")]["multiplicaciones"] if (n, "directa") in grouped else "--",
                            grouped[(n, "fft_recursiva")]["mariposas"],
                            grouped[(n, "ntt")]["mariposas"],
                            grouped[(n, "ntt")]["etapas"]) for n in sizes],
                          label="tab:operaciones"))
    max_size = max(int(r["n_entrada"]) for r in error)
    selected = [r for r in error if int(r["n_entrada"]) == max_size and
                int(r["magnitud_maxima"]) in (10, 1000, 100000, 1000000000)]
    sections.append(table("Error FFT antes de redondear (n="+str(max_size)+")",
                          ["Magnitud", "Método", "Error real", "Error imaginario", "Fallos"],
                          [(r["magnitud_maxima"], "rec." if r["metodo"] == "recursive" else "iter.",
                            f'{float(r["error_real_max"]):.2g}',
                            f'{float(r["error_imaginario_max"]):.2g}',
                            r["coeficientes_erroneos"]) for r in selected],
                          label="tab:error"))
    sections.append(table("Primer tamaño medido que supera a la convolución directa",
                          ["Método", "$n$ de cruce", "Directa medida hasta"],
                          [(r["metodo"].replace("_", r"\_"), r["primer_n_supera_directa"] or "--",
                            r["ultimo_n_directa_medido"]) for r in crossing],
                          label="tab:puntos_cruce"))
    sections += [f"\n\\noindent En nuestro análisis diferencial realizamos {len(diff)} comparaciones en el Escenario A; "
                 f"identificamos {len(discrepancies)} discrepancias en el rango $[0,p-1]$ "
                 "con FFT de doble precisión debido a la saturación de la mantisa de 53 bits. Estas discrepancias "
                 "quedaron registradas en \\path{python/results/discrepancias.csv}. Por su parte, la NTT coincidió "
                 "exactamente módulo $p$ en la totalidad de los casos.\\par\n"]
    if first:
        f = first[0]
        sections.append("\n\\noindent Identificamos que el primer fallo de redondeo en la FFT "
                        f"ocurrió en $n={f['n']}$, magnitud máxima {f['magnitud']}, "
                        f"semilla {f['seed']}, método {f['metodo']}, índice {f['indice']}: "
                        f"referencia entera {f['esperado']} frente al valor redondeado {f['redondeado']}. "
                        "Los vectores de prueba se registran en \\path{python/results/primer_fallo_fft.csv}.\\par")
    (OUTPUT / "04_tablas_generadas.tex").write_text("\n".join(sections)+"\n", encoding="utf-8")


if __name__ == "__main__":
    render()
