"""Batería experimental y generación de CSV, figuras PNG y tablas LaTeX (Guía 09)."""

from __future__ import annotations

import csv
import hashlib
import math
import os
from pathlib import Path
import platform
from statistics import median
import sys
import tempfile
from time import perf_counter_ns
import tracemalloc

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from case_generator import materialize_corpus
from compression import (
    CanonicalHuffmanCompressor,
    LZ77Compressor,
    RLECompressor,
    average_code_length,
    build_code_lengths,
    build_huffman_tree,
    entropy,
    frequencies,
)
from visualize import plot_huffman_didactic, plot_lz77_didactic

BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"
FIGURES_DIR = BASE_DIR / "figures"
LATEX_TABLES_DIR = BASE_DIR / "latex_tables"

REPETITIONS = 10


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _save_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    if fieldnames is None:
        fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def medir_roundtrip(compressor, data: bytes, repeticiones: int = REPETITIONS) -> dict:
    """Metodología exacta de la Sección 10 (Listing 6), excluyendo E/S y generación."""
    # Calentamiento previo de 1 corrida fuera del intervalo cronometrado
    _warm_payload = compressor.compress(data)
    assert compressor.decompress(_warm_payload) == data

    tiempos_c = []
    tiempos_d = []
    payload = None

    for _ in range(repeticiones):
        inicio = perf_counter_ns()
        current = compressor.compress(data)
        fin = perf_counter_ns()
        tiempos_c.append(fin - inicio)

        inicio = perf_counter_ns()
        restored = compressor.decompress(current)
        fin = perf_counter_ns()
        tiempos_d.append(fin - inicio)

        assert restored == data
        if payload is None:
            payload = current
        else:
            assert current == payload

    assert payload is not None
    return {
        "original_bytes": len(data),
        "compressed_bytes": len(payload),
        "compression_median_ns": int(median(tiempos_c)),
        "decompression_median_ns": int(median(tiempos_d)),
        "compression_min_ns": min(tiempos_c),
        "compression_max_ns": max(tiempos_c),
        "decompression_min_ns": min(tiempos_d),
        "decompression_max_ns": max(tiempos_d),
        "payload": payload,
    }


def _measure_peak_memory(compressor, data: bytes, payload: bytes) -> tuple[int, int]:
    """Mide memoria pico fuera del intervalo cronometrado usando tracemalloc."""
    tracemalloc.start()
    _ = compressor.compress(data)
    _, peak_c = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    tracemalloc.start()
    _ = compressor.decompress(payload)
    _, peak_d = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak_c, peak_d


def record_environment() -> list[dict]:
    rows = [
        {"parametro": "python_version", "valor": platform.python_version()},
        {"parametro": "python_implementation", "valor": platform.python_implementation()},
        {"parametro": "os_system", "valor": f"{platform.system()} {platform.release()}"},
        {"parametro": "architecture", "valor": platform.machine()},
        {"parametro": "cpu_count", "valor": str(os.cpu_count() or 1)},
        {"parametro": "repeticiones", "valor": str(REPETITIONS)},
        {"parametro": "lz77_window_size", "valor": "4096"},
        {"parametro": "lz77_min_match", "valor": "3"},
        {"parametro": "lz77_max_match", "valor": "18"},
    ]
    _save_csv(RESULTS_DIR / "entorno_ejecucion.csv", rows)
    return rows


def run_core_experiments(corpus: list[dict]) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """Compara los tres métodos sobre exactamente los mismos 9 archivos en memoria."""
    comp_rows: list[dict] = []
    huff_rows: list[dict] = []
    expansion_rows: list[dict] = []
    verif_rows: list[dict] = []

    factories = (
        ("huffman_canonico", CanonicalHuffmanCompressor),
        ("rle", RLECompressor),
        ("lz77", LZ77Compressor),
    )

    for item in corpus:
        data = item["data"]
        h_orig = _sha256(data)

        # Métricas teóricas de Huffman para el archivo
        freq = frequencies(data)
        h_val = entropy(freq)
        tree = build_huffman_tree(freq)
        lengths = build_code_lengths(tree)
        l_val = average_code_length(freq, lengths)
        eta = (h_val / l_val) if l_val > 0 else (1.0 if not data else 0.0)
        theo_bytes = math.ceil((len(data) * l_val) / 8.0) if data else 0

        for alg_name, factory in factories:
            comp = factory()
            timing = medir_roundtrip(comp, data, REPETITIONS)
            # Última llamada para fijar stats de compresión y obtener desglose
            payload = comp.compress(data)
            st = comp.stats()
            restored = comp.decompress(payload)
            h_rest = _sha256(restored)
            exact = restored == data and h_orig == h_rest
            assert exact

            peak_c, peak_d = _measure_peak_memory(factory(), data, payload)
            if alg_name == "huffman_canonico":
                estructura = f"nodos={st.get('nodos_arbol', 0)}, sim={st.get('simbolos_distintos', 0)}"
                huff_rows.append({
                    "archivo": item["archivo"],
                    "categoria": item["categoria"],
                    "original_bytes": len(data),
                    "simbolos_distintos": st.get("simbolos_distintos", 0),
                    "entropy_H": round(h_val, 6),
                    "avg_length_L": round(l_val, 6),
                    "efficiency_eta": round(eta, 6),
                    "redundancy_L_minus_H": round(l_val - h_val, 6),
                    "theoretical_payload_bytes": theo_bytes,
                    "actual_data_bytes": st["data_bytes"],
                    "header_plus_metadata_bytes": st["header_bytes"] + st["metadata_bytes"],
                    "total_bytes": st["total_bytes"],
                    "expansion_por_metadatos": st["total_bytes"] > len(data),
                })
            elif alg_name == "rle":
                estructura = f"corridas={st.get('corridas', 0)}"
            else:
                estructura = (
                    f"win={st.get('window_size', 4096)}, "
                    f"tok={st.get('tokens', 0)} (L={st.get('literales', 0)}, M={st.get('coincidencias', 0)})"
                )

            row = {
                "archivo": item["archivo"],
                "categoria": item["categoria"],
                "algoritmo": alg_name,
                "original_bytes": st["original_bytes"],
                "header_bytes": st["header_bytes"],
                "metadata_bytes": st["metadata_bytes"],
                "data_bytes": st["data_bytes"],
                "padding_bits": st["padding_bits"],
                "total_bytes": st["total_bytes"],
                "compression_ratio": round(st["compression_ratio"], 4),
                "savings_pct": round(st["savings_pct"], 2),
                "compression_median_ns": timing["compression_median_ns"],
                "compression_min_ns": timing["compression_min_ns"],
                "compression_max_ns": timing["compression_max_ns"],
                "decompression_median_ns": timing["decompression_median_ns"],
                "decompression_min_ns": timing["decompression_min_ns"],
                "decompression_max_ns": timing["decompression_max_ns"],
                "compression_median_ms": round(timing["compression_median_ns"] / 1e6, 4),
                "decompression_median_ms": round(timing["decompression_median_ns"] / 1e6, 4),
                "peak_memory_compress_bytes": peak_c,
                "peak_memory_decompress_bytes": peak_d,
                "estructura_principal": estructura,
                "sha256_original": h_orig,
                "sha256_restored": h_rest,
                "exact_match": exact,
            }
            comp_rows.append(row)

            verif_rows.append({
                "entorno": "nucleo_memoria",
                "archivo": item["archivo"],
                "algoritmo": alg_name,
                "original_bytes": len(data),
                "total_bytes": st["total_bytes"],
                "sha256_original": h_orig[:16],
                "sha256_restored": h_rest[:16],
                "exact_match": exact,
            })

            if st["total_bytes"] > len(data):
                if len(data) <= 16:
                    causa = "Encabezado y metadatos superan la entrada corta"
                elif alg_name == "rle":
                    causa = "Corridas cortas (3 bytes por par exceden 1 byte original)"
                elif alg_name == "huffman_canonico":
                    causa = "Alta entropía (~8 bits/símbolo) más tabla canónica de 256 símbolos"
                else:
                    causa = "Sin coincidencias >= 3 B: sobrecarga de 1 bit de bandera por literal"
                expansion_rows.append({
                    "archivo": item["archivo"],
                    "categoria": item["categoria"],
                    "algoritmo": alg_name,
                    "original_bytes": len(data),
                    "header_plus_metadata_bytes": st["header_bytes"] + st["metadata_bytes"],
                    "data_bytes": st["data_bytes"],
                    "total_bytes": st["total_bytes"],
                    "incremento_bytes": st["total_bytes"] - len(data),
                    "causa": causa,
                })

    _save_csv(RESULTS_DIR / "comparacion_algoritmos.csv", comp_rows)
    _save_csv(RESULTS_DIR / "huffman_entropia.csv", huff_rows)
    _save_csv(RESULTS_DIR / "casos_expansion.csv", expansion_rows)
    return comp_rows, huff_rows, expansion_rows, verif_rows


def run_e2e_disk_experiments(
    corpus: list[dict], core_rows: list[dict], verif_rows: list[dict]
) -> list[dict]:
    """Mide compresión y descompresión de extremo a extremo incluyendo lectura/escritura en disco."""
    selected = {"04_unico_simbolo", "05_texto_espanol", "06_patrones_repetitivos", "08_aleatorio", "09_imagen_comprimida"}
    core_lookup = {(r["archivo"], r["algoritmo"]): r for r in core_rows}
    e2e_rows: list[dict] = []

    factories = (
        ("huffman_canonico", CanonicalHuffmanCompressor),
        ("rle", RLECompressor),
        ("lz77", LZ77Compressor),
    )

    with tempfile.TemporaryDirectory(prefix="lab09_e2e_") as tmp:
        tmp_dir = Path(tmp)
        for item in corpus:
            if item["id"] not in selected:
                continue
            src_path = tmp_dir / item["archivo"]
            src_path.write_bytes(item["data"])
            h_orig = _sha256(item["data"])

            for alg_name, factory in factories:
                cmp_path = tmp_dir / f"{item['id']}.{alg_name}.cmp9"
                out_path = tmp_dir / f"{item['id']}.{alg_name}.restored"
                # Calentamiento previo
                _w_comp = factory()
                cmp_path.write_bytes(_w_comp.compress(src_path.read_bytes()))
                out_path.write_bytes(_w_comp.decompress(cmp_path.read_bytes()))

                times_c = []
                times_d = []
                for _ in range(REPETITIONS):
                    comp = factory()
                    t0 = perf_counter_ns()
                    raw = src_path.read_bytes()
                    payload = comp.compress(raw)
                    cmp_path.write_bytes(payload)
                    times_c.append(perf_counter_ns() - t0)

                    t0 = perf_counter_ns()
                    loaded = cmp_path.read_bytes()
                    restored = comp.decompress(loaded)
                    out_path.write_bytes(restored)
                    times_d.append(perf_counter_ns() - t0)

                    assert restored == item["data"]

                h_rest = _sha256(out_path.read_bytes())
                assert h_orig == h_rest
                med_c_ms = median(times_c) / 1e6
                med_d_ms = median(times_d) / 1e6
                core_r = core_lookup[(item["archivo"], alg_name)]
                core_c_ms = core_r["compression_median_ms"]
                core_d_ms = core_r["decompression_median_ms"]

                e2e_rows.append({
                    "archivo": item["archivo"],
                    "algoritmo": alg_name,
                    "original_bytes": len(item["data"]),
                    "total_bytes": core_r["total_bytes"],
                    "core_comp_ms": round(core_c_ms, 4),
                    "e2e_comp_ms": round(med_c_ms, 4),
                    "overhead_io_comp_ms": round(med_c_ms - core_c_ms, 4),
                    "core_decomp_ms": round(core_d_ms, 4),
                    "e2e_decomp_ms": round(med_d_ms, 4),
                    "overhead_io_decomp_ms": round(med_d_ms - core_d_ms, 4),
                    "exact_match": True,
                })
                verif_rows.append({
                    "entorno": "extremo_a_extremo_disco",
                    "archivo": item["archivo"],
                    "algoritmo": alg_name,
                    "original_bytes": len(item["data"]),
                    "total_bytes": core_r["total_bytes"],
                    "sha256_original": h_orig[:16],
                    "sha256_restored": h_rest[:16],
                    "exact_match": True,
                })

    _save_csv(RESULTS_DIR / "comparacion_e2e_disco.csv", e2e_rows)
    _save_csv(RESULTS_DIR / "resumen_verificacion.csv", verif_rows)
    return e2e_rows


def run_lz77_sensitivity(corpus: list[dict]) -> list[dict]:
    """Evalúa sensibilidad de LZ77 a tamaño de ventana y longitud máxima de coincidencia."""
    targets = [item for item in corpus if item["id"] in ("05_texto_espanol", "06_patrones_repetitivos")]
    configs = [(64, 3, 18), (512, 3, 18), (4096, 3, 6), (4096, 3, 18)]
    rows: list[dict] = []
    for item in targets:
        data = item["data"]
        for win, min_m, max_m in configs:
            comp = LZ77Compressor(window_size=win, min_match=min_m, max_match=max_m)
            timing = medir_roundtrip(comp, data, 5)
            _ = comp.compress(data)
            st = comp.stats()
            rows.append({
                "archivo": item["archivo"],
                "window_size": win,
                "min_match": min_m,
                "max_match": max_m,
                "original_bytes": len(data),
                "total_bytes": st["total_bytes"],
                "savings_pct": round(st["savings_pct"], 2),
                "tokens": st["tokens"],
                "literales": st["literales"],
                "coincidencias": st["coincidencias"],
                "compression_median_ms": round(timing["compression_median_ns"] / 1e6, 3),
            })
    _save_csv(RESULTS_DIR / "lz77_parametros.csv", rows)
    return rows


def plot_savings_chart(comp_rows: list[dict]) -> None:
    """Figura 1: Porcentaje de ahorro por tipo de archivo y algoritmo."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    files = [
        ("03_pocos_bytes.bin", "Pocos B\n(16 B)"),
        ("04_unico_simbolo.bin", "Único símb.\n(32 KiB)"),
        ("05_texto_espanol.txt", "Texto esp.\n(36 KB)"),
        ("06_patrones_repetitivos.bin", "Patrones\n(32 KiB)"),
        ("07_uniforme_256.bin", "Uniforme\n(32 KiB)"),
        ("08_aleatorio.bin", "Aleatorio\n(32 KiB)"),
        ("09_imagen_comprimida.png", "PNG compr.\n(36.8 KB)"),
    ]
    lookup = {(r["archivo"], r["algoritmo"]): r["savings_pct"] for r in comp_rows}
    x = np.arange(len(files))
    width = 0.26

    fig, ax = plt.subplots(figsize=(11.5, 5.4))
    series = [
        ("Huffman canónico", "huffman_canonico", "#1f77b4", -width),
        ("RLE binario", "rle", "#d62728", 0.0),
        ("LZ77 (ventana 4 KiB)", "lz77", "#2ca02c", width),
    ]
    for label, alg, color, offset in series:
        vals = [lookup[(fname, alg)] for fname, _ in files]
        bars = ax.bar(x + offset, vals, width, label=label, color=color, alpha=0.88, edgecolor="#222")
        for bar, val in zip(bars, vals):
            y_text = val + (3 if val >= 0 else -8)
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                y_text,
                f"{val:.0f}%",
                ha="center",
                va="bottom" if val >= 0 else "top",
                fontsize=7.3,
                fontweight="bold",
            )

    ax.axhline(0, color="#111111", linewidth=1.1)
    ax.set_xticks(x)
    ax.set_xticklabels([lbl for _, lbl in files], fontsize=9)
    ax.set_ylabel("Ahorro porcentual (%)  [negativo = expansión]", fontsize=10.5, fontweight="bold")
    ax.set_title("Porcentaje de ahorro por tipo de archivo y algoritmo (incluye encabezado y metadatos)", fontsize=11.5, fontweight="bold")
    ax.set_ylim(-335, 138)
    ax.grid(axis="y", linestyle="--", alpha=0.45)
    ax.legend(loc="upper center", ncol=3, fontsize=9.2, frameon=True)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig1_ahorro_por_archivo.png", dpi=260)
    plt.close(fig)


def plot_timings_chart(comp_rows: list[dict], e2e_rows: list[dict]) -> None:
    """Figura 2: Tiempos medianos de compresión/descompresión en núcleo y sobrecarga E2E."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    files = [
        ("04_unico_simbolo.bin", "Único símb."),
        ("05_texto_espanol.txt", "Texto esp."),
        ("06_patrones_repetitivos.bin", "Patrones"),
        ("08_aleatorio.bin", "Aleatorio"),
        ("09_imagen_comprimida.png", "PNG compr."),
    ]
    lookup = {(r["archivo"], r["algoritmo"]): r for r in comp_rows}
    e2e_lookup = {(r["archivo"], r["algoritmo"]): r for r in e2e_rows}
    x = np.arange(len(files))
    width = 0.26

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.2, 5.1), sharey=True)
    series = [
        ("Huffman canónico", "huffman_canonico", "#1f77b4", -width),
        ("RLE binario", "rle", "#d62728", 0.0),
        ("LZ77 (4 KiB)", "lz77", "#2ca02c", width),
    ]

    for label, alg, color, offset in series:
        c_core = [lookup[(f, alg)]["compression_median_ms"] for f, _ in files]
        d_core = [lookup[(f, alg)]["decompression_median_ms"] for f, _ in files]
        c_e2e = [e2e_lookup[(f, alg)]["e2e_comp_ms"] for f, _ in files]
        d_e2e = [e2e_lookup[(f, alg)]["e2e_decomp_ms"] for f, _ in files]

        ax1.bar(x + offset, c_core, width, label=label if ax1 else "", color=color, alpha=0.88)
        ax1.scatter(x + offset, c_e2e, color="#111111", marker="^", s=34, zorder=4, label="E2E con disco" if alg == "lz77" else None)

        ax2.bar(x + offset, d_core, width, label=label, color=color, alpha=0.88)
        ax2.scatter(x + offset, d_e2e, color="#111111", marker="^", s=34, zorder=4, label="E2E con disco" if alg == "lz77" else None)

    for ax, title in ((ax1, "Compresión (mediana de 10 corridas)"), (ax2, "Descompresión (mediana de 10 corridas)")):
        ax.set_yscale("log")
        ax.set_xticks(x)
        ax.set_xticklabels([lbl for _, lbl in files], fontsize=9)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.grid(axis="y", which="both", linestyle="--", alpha=0.45)

    ax1.set_ylabel("Tiempo mediano (ms, escala logarítmica)", fontsize=10.5, fontweight="bold")
    ax1.legend(loc="upper left", fontsize=8.5)
    fig.suptitle("Rendimiento temporal: núcleo en memoria (barras) vs extremo a extremo con disco (▲)", fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig2_tiempos_compresion_descompresion.png", dpi=260)
    plt.close(fig)


def plot_metadata_vs_data_chart(comp_rows: list[dict]) -> None:
    """Figura 3: Comparación entre datos codificados y encabezado+metadatos."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    cases = [
        ("03_pocos_bytes.bin", "Pocos B (16 B)"),
        ("05_texto_espanol.txt", "Texto esp. (36 KB)"),
        ("08_aleatorio.bin", "Aleatorio (32 KiB)"),
    ]
    lookup = {(r["archivo"], r["algoritmo"]): r for r in comp_rows}
    algs = [("huffman_canonico", "Huff"), ("rle", "RLE"), ("lz77", "LZ77")]

    labels = []
    meta_vals = []
    data_vals = []
    for fname, short_name in cases:
        for alg_key, alg_short in algs:
            r = lookup[(fname, alg_key)]
            labels.append(f"{short_name}\n{alg_short}")
            meta_vals.append(r["header_bytes"] + r["metadata_bytes"])
            data_vals.append(max(r["data_bytes"], 0))

    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(11.8, 5.1))
    ax.bar(x, meta_vals, label="Encabezado + Metadatos (bytes)", color="#f59e0b", edgecolor="#222")
    ax.bar(x, data_vals, bottom=meta_vals, label="Datos codificados (bytes)", color="#2563eb", alpha=0.88, edgecolor="#222")
    ax.set_yscale("log")
    ax.set_ylim(8, None)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylabel("Tamaño en bytes (escala logarítmica)", fontsize=10.5, fontweight="bold")
    ax.set_title("Desglose estructural: sobrecarga fija de metadatos frente a datos codificados", fontsize=11.5, fontweight="bold")
    ax.grid(axis="y", which="both", linestyle="--", alpha=0.45)
    ax.legend(fontsize=9.5)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig3_desglose_metadatos_datos.png", dpi=260)
    plt.close(fig)


def plot_entropy_chart(huff_rows: list[dict]) -> None:
    """Figura 4: Entropía H(X), longitud promedio L y bits/byte reales totales."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    filtered = [r for r in huff_rows if r["original_bytes"] > 0]
    labels = [
        r["archivo"].replace(".bin", "").replace(".txt", "").replace(".png", "").replace("_", "\n")
        for r in filtered
    ]
    hs = [r["entropy_H"] for r in filtered]
    ls = [r["avg_length_L"] for r in filtered]
    real_bpb = [min((r["total_bytes"] * 8.0) / r["original_bytes"], 16.0) for r in filtered]

    x = np.arange(len(filtered))
    width = 0.27
    fig, ax = plt.subplots(figsize=(11.5, 5.0))
    ax.bar(x - width, hs, width, label="Entropía H(X) [bits/símbolo]", color="#10b981")
    ax.bar(x, ls, width, label="Longitud media L de Huffman", color="#3b82f6")
    ax.bar(x + width, real_bpb, width, label="Costo real total 8·Sc/So (acotado a 16)", color="#ef4444", alpha=0.85)
    ax.axhline(8.0, color="#374151", linestyle=":", linewidth=1.2, label="8 bits/byte (sin comprimir)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8.2)
    ax.set_ylabel("Bits por byte original", fontsize=10.5, fontweight="bold")
    ax.set_title("Cota de Shannon H(X) <= L < H(X)+1 frente al costo real con metadatos", fontsize=11.5, fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.45)
    ax.legend(fontsize=8.8)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig4_entropia_vs_longitud_huffman.png", dpi=260)
    plt.close(fig)


def main() -> None:
    print("Iniciando campaña experimental de Compresión (Guía 09)...")
    corpus = materialize_corpus()
    record_environment()
    core_rows, huff_rows, expansion_rows, verif_rows = run_core_experiments(corpus)
    e2e_rows = run_e2e_disk_experiments(corpus, core_rows, verif_rows)
    run_lz77_sensitivity(corpus)

    print("Generando visualizaciones obligatorias y figuras experimentales...")
    plot_huffman_didactic()
    plot_lz77_didactic()
    plot_savings_chart(core_rows)
    plot_timings_chart(core_rows, e2e_rows)
    plot_metadata_vs_data_chart(core_rows)
    plot_entropy_chart(huff_rows)
    print(
        f"Experimentos completados: {len(core_rows)} filas núcleo, "
        f"{len(e2e_rows)} filas E2E disco, {len(expansion_rows)} casos de expansión."
    )


if __name__ == "__main__":
    main()
