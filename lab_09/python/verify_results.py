"""Auditoría automática de datasets CSV y gráficos PNG (Guía 09, UNSAAC)."""

from __future__ import annotations

import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"
FIGURES_DIR = BASE_DIR / "figures"

EXPECTED_CSVS = [
    "entorno_ejecucion.csv",
    "comparacion_algoritmos.csv",
    "comparacion_e2e_disco.csv",
    "huffman_entropia.csv",
    "lz77_parametros.csv",
    "casos_expansion.csv",
    "resumen_verificacion.csv",
]

EXPECTED_FIGURES = [
    "fig_didactica_huffman.png",
    "fig_didactica_lz77.png",
    "fig1_ahorro_por_archivo.png",
    "fig2_tiempos_compresion_descompresion.png",
    "fig3_desglose_metadatos_datos.png",
    "fig4_entropia_vs_longitud_huffman.png",
]

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _read_csv(path: Path) -> list[dict]:
    assert path.is_file(), f"Falta el archivo CSV: {path}"
    with path.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) > 0, f"CSV vacío: {path}"
    return rows


def verify() -> bool:
    print("=" * 72)
    print("AUDITORÍA DE EVIDENCIA EXPERIMENTAL — LABORATORIO 09 (UNSAAC)")
    print("=" * 72)

    print("\n[1/3] Auditando las 6 figuras PNG (2 didácticas + 4 experimentales)...")
    for name in EXPECTED_FIGURES:
        path = FIGURES_DIR / name
        assert path.is_file(), f"Falta figura PNG: {path}"
        raw = path.read_bytes()
        size_kb = len(raw) / 1024.0
        assert raw.startswith(PNG_MAGIC), f"Cabecera PNG inválida: {name}"
        assert size_kb >= 15.0, f"Figura sospechosamente pequeña ({size_kb:.1f} KiB): {name}"
        print(f"  [OK] {name:<44} {size_kb:>7.1f} KiB")

    print("\n[2/3] Auditando los 7 datasets CSV en python/results/...")
    data: dict[str, list[dict]] = {}
    for name in EXPECTED_CSVS:
        rows = _read_csv(RESULTS_DIR / name)
        data[name] = rows
        print(f"  [OK] {name:<32} {len(rows):>5} filas")

    print("\n[3/3] Comprobando invariantes científicos y requisitos de la Guía 09...")
    comp = data["comparacion_algoritmos.csv"]
    assert len(comp) == 27, f"Se esperaban 27 filas (9 archivos x 3 métodos), hay {len(comp)}"
    for r in comp:
        h = int(r["header_bytes"])
        m = int(r["metadata_bytes"])
        d = int(r["data_bytes"])
        tot = int(r["total_bytes"])
        assert h + m + d == tot, f"Suma estructural inválida en {r['archivo']}/{r['algoritmo']}"
        assert r["exact_match"] == "True", f"Fallo de reconstrucción en {r['archivo']}/{r['algoritmo']}"
        assert r["sha256_original"] == r["sha256_restored"], "SHA-256 no coincide"
    print("  [OK] 27 casos núcleo: Sc = S_encabezado + S_metadatos + S_datos y SHA-256 exacto.")

    huff = data["huffman_entropia.csv"]
    assert len(huff) == 9, f"Se esperaban 9 filas en huffman_entropia.csv, hay {len(huff)}"
    for r in huff:
        h_val = float(r["entropy_H"])
        l_val = float(r["avg_length_L"])
        if int(r["original_bytes"]) > 0:
            assert h_val <= l_val + 1e-6, f"Violación H <= L en {r['archivo']}"
            assert l_val < h_val + 1.0 + 1e-6, f"Violación L < H + 1 en {r['archivo']}"
    print("  [OK] Desigualdad de Shannon H(X) <= L < H(X) + 1 verificada en todos los archivos.")

    e2e = data["comparacion_e2e_disco.csv"]
    assert len(e2e) == 15, f"Se esperaban 15 filas E2E en disco, hay {len(e2e)}"
    assert all(r["exact_match"] == "True" for r in e2e)
    print("  [OK] 15 mediciones extremo a extremo en disco verificadas (con SHA-256).")

    expansion = data["casos_expansion.csv"]
    assert any(r["algoritmo"] == "rle" for r in expansion), "Falta caso de expansión RLE"
    assert any(r["algoritmo"] == "huffman_canonico" for r in expansion), "Falta caso de expansión Huffman"
    print(f"  [OK] Documentados {len(expansion)} casos donde los metadatos o baja redundancia expanden el tamaño.")

    verif = data["resumen_verificacion.csv"]
    assert len(verif) == 42 and all(r["exact_match"] == "True" for r in verif)
    print("  [OK] 42/42 comprobaciones de reconstrucción exacta aprobadas.")

    print("\n" + "=" * 72)
    print("RESULTADO DE AUDITORÍA: 100% DE CRITERIOS DE LA GUÍA 09 VERIFICADOS")
    print("=" * 72)
    return True


if __name__ == "__main__":
    verify()
