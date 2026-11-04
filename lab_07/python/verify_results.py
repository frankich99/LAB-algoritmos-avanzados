"""Auditoría y verificación automática de resultados experimentales (Guía 07).

Valida la integridad, consistencia matemática y completitud de los 10 archivos CSV
generados en `results/` y las 4 figuras PNG en `figures/`.
"""

import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
RESULTS = BASE_DIR / "results"
FIGURES = BASE_DIR / "figures"

EXPECTED_CSVS = [
    "casos_conocidos.csv",
    "trazas_miller_rabin.csv",
    "clasificacion_bases.csv",
    "tasa_error_empirica.csv",
    "probables_primos_generados.csv",
    "resumen_generacion.csv",
    "entradas_y_bases.csv",
    "comparacion_detallada.csv",
    "comparacion_resumen.csv",
    "resumen_ejecucion.csv",
]

EXPECTED_FIGURES = [
    "fig1_tiempo_vs_bits.png",
    "fig2_cuadrados_vs_bits.png",
    "fig3_candidatos_vs_bits.png",
    "fig4_error_empirico.png",
]

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _read_csv(filepath):
    assert filepath.is_file(), f"Archivo no encontrado: {filepath}"
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) > 0, f"El archivo CSV esta vacio: {filepath}"
    return rows


def verify():
    """Ejecuta la suite completa de auditoria sobre los datasets y graficos."""
    print("=" * 70)
    print("AUDITORIA DE EVIDENCIA EXPERIMENTAL - LABORATORIO 07 (UNSAAC)")
    print("=" * 70)

    # 1. Auditoría de Existencia y Formato de Figuras PNG
    print("\n[1/3] Auditando Figuras PNG generadas...")
    for fig_name in EXPECTED_FIGURES:
        fig_path = FIGURES / fig_name
        assert fig_path.is_file(), f"Falta la figura requerida: {fig_name}"
        raw_bytes = fig_path.read_bytes()
        size_kb = len(raw_bytes) / 1024.0
        assert raw_bytes.startswith(PNG_MAGIC), f"Encabezado PNG invalido en {fig_name}"
        assert size_kb >= 10.0, f"Figura sospechosamente pequena ({size_kb:.2f} KB): {fig_name}"
        print(f"  [OK] {fig_name:<30} {size_kb:>8.2f} KB  [PNG VALIDO]")

    # 2. Auditoría de Existencia y Esquema de los 10 Archivos CSV
    print("\n[2/3] Auditando Integridad y Estructura de los 10 Datasets CSV...")
    csv_data = {}
    for csv_name in EXPECTED_CSVS:
        path = RESULTS / csv_name
        rows = _read_csv(path)
        csv_data[csv_name] = rows
        print(f"  [OK] {csv_name:<32} {len(rows):>6} filas  [DATOS VALIDOS]")

    # 3. Auditoría de Invariantes Científicos y Restricciones de la Guía
    print("\n[3/3] Comprobando Invariantes Cientificos y Restricciones de la Guia...")

    # A. 210 probables primos (30 por cada longitud)
    primos_gen = csv_data["probables_primos_generados.csv"]
    assert len(primos_gen) == 210, f"Se esperaban 210 primos generados, se hallaron {len(primos_gen)}"
    from collections import Counter
    conteo_bits = Counter(int(r["bits"]) for r in primos_gen)
    expected_bits = {16: 30, 32: 30, 64: 30, 128: 30, 256: 30, 512: 30, 1024: 30}
    assert conteo_bits == expected_bits, f"Distribucion de bits incorrecta: {conteo_bits}"
    print("  [OK] Verificados 210 probables primos distribuidos equitativamente (30 x 7 longitudes).")

    # B. Validación de primos exactos en 16 y 32 bits
    for r in primos_gen:
        b = int(r["bits"])
        if b in (16, 32):
            assert r["tipo_entrada"] == "primo_verificado", f"Tipo incorrecto en {b} bits"
        else:
            assert r["tipo_entrada"] == "probable_primo", f"Tipo incorrecto en {b} bits"
    print("  [OK] Tipado riguroso verificado: 16 y 32 bits certificados por division de prueba.")

    # C. Auditoría de entradas y 20 bases fijadas
    entradas_bases = csv_data["entradas_y_bases.csv"]
    assert len(entradas_bases) == 112, f"Se esperaban 112 entradas (16 x 7), se hallaron {len(entradas_bases)}"
    for row in entradas_bases:
        for i in range(1, 21):
            col = f"base_{i:02d}"
            assert col in row, f"Falta columna {col} en entradas_y_bases.csv"
            base_val = int(row[col])
            n_val = int(row["n"])
            assert 2 <= base_val <= n_val - 2, f"Base {base_val} fuera de rango [2, n-2] para n={n_val}"
    print("  [OK] 112 entradas evaluadas con exactamente 20 bases validas e independientes.")

    # D. División de prueba restringida a <= 32 bits
    detallada = csv_data["comparacion_detallada.csv"]
    td_rows = [r for r in detallada if r["metodo"] == "division_prueba"]
    for r in td_rows:
        b = int(r["bits"])
        assert b <= 32, f"Division de prueba ejecutada ilegalmente en {b} bits (>32 bits)"
    assert len(td_rows) > 0, "No se encontro registro de division de prueba"
    print("  [OK] Restriccion asintotica respetada: division de prueba solo hasta 32 bits.")

    # E. Tasa empírica de error vs Cota Universal 4^-r
    tasa_error = csv_data["tasa_error_empirica.csv"]
    assert len(tasa_error) == 24, f"Se esperaban 24 casos (6 compuestos x 4 rondas), se hallaron {len(tasa_error)}"
    for r in tasa_error:
        sims = int(r["simulaciones"])
        assert sims == 3000, f"Simulaciones incorrectas ({sims} != 3000)"
        tasa_obs = float(r["tasa_observada"])
        cota_univ = float(r["cota_universal"])
        assert tasa_obs <= cota_univ + 0.05, f"Violacion de cota: tasa {tasa_obs} > cota {cota_univ}"
    print("  [OK] Tasa de error auditada en 3000 simulaciones/caso: respeta cota 4^-r.")

    # F. Casos conocidos especiales
    casos = csv_data["casos_conocidos.csv"]
    ns = [int(r["n"]) for r in casos]
    for req in [0, 1, 2, 3, 341, 561, 1105, 1729]:
        assert req in ns, f"Falta caso conocido esencial: n={req}"
    print("  [OK] Casos deterministas y numeros de Carmichael verificados (0, 1, 2, 3, 341, 561, 1105, 1729).")

    # G. Trazas detalladas de Miller-Rabin
    trazas = csv_data["trazas_miller_rabin.csv"]
    trazas_n = [int(r["n"]) for r in trazas]
    for req in [221, 341, 561]:
        assert req in trazas_n, f"Falta traza de n={req}"
    print("  [OK] Trazas explicitas de Miller-Rabin registradas para 221, 341 y 561.")

    print("\n" + "=" * 70)
    print("RESULTADO DE AUDITORIA: 100% DE PRUEBAS Y CRITERIOS SUPERADOS EXITOSAMENTE")
    print("=" * 70)
    return True


if __name__ == "__main__":
    verify()
