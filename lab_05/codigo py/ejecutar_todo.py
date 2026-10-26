"""Script maestro: genera toda la evidencia del Laboratorio 05."""

import json

from lab05_pipeline import run_all


def main() -> None:
    summary = run_all()
    print("=" * 76)
    print("[ÉXITO TOTAL] Laboratorio 05 ejecutado; CSV, trazas, figuras e informe listos.")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
