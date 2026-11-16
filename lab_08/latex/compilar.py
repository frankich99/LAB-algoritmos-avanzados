"""Genera fragmentos verificables y compila dos/tres pasadas con pdflatex."""

import subprocess
import sys
from pathlib import Path


def main():
    base = Path(__file__).resolve().parent
    for script in ("verify_results.py", "render_report.py"):
        result = subprocess.run([sys.executable, str(base.parent / "python" / script)],
                                cwd=base.parent, check=False)
        if result.returncode:
            raise SystemExit(f"Falló la generación previa: {script}")
    for run in range(3):
        result = subprocess.run(["pdflatex", "-interaction=nonstopmode",
                                 "-halt-on-error", "main.tex"], cwd=base,
                                capture_output=True, check=False)
        (base / "compilacion.log").write_bytes(result.stdout + result.stderr)
        if result.returncode:
            print((result.stdout + result.stderr).decode(errors="replace")[-4000:])
            raise SystemExit(f"pdflatex falló en pasada {run+1}")
        if run >= 1 and b"Rerun to get" not in result.stdout:
            break
    print(f"PDF generado: {base / 'main.pdf'}")


if __name__ == "__main__":
    main()
