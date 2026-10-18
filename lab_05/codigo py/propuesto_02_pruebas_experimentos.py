"""Ejercicio propuesto 2: pruebas diferenciales y análisis experimental."""

from lab05_pipeline import run_differential_experiments, run_experimental_scenario


def main() -> None:
    differential, _ = run_differential_experiments()
    experiments = run_experimental_scenario()
    assert all(row["discrepancias"] == 0 for row in differential)
    print(f"[OK] Diferenciales: {len(differential)} tamaños; métricas: {len(experiments)} lotes.")


if __name__ == "__main__":
    main()
