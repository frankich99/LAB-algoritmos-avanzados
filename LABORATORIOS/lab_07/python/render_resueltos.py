"""Inserta en el informe el código y la salida real de los tres resueltos."""

from inspect import getsource
from pathlib import Path
from pprint import pformat

from ejercicios_resueltos import resuelto_1, resuelto_2, resuelto_3


DESTINO = Path(__file__).resolve().parent.parent / "latex" / "secciones"
EJERCICIOS = (
    (1, resuelto_1, "División de prueba y Fermat"),
    (2, resuelto_2, "Miller--Rabin con traza"),
    (3, resuelto_3, "Prueba repetida y candidatos"),
)


def renderizar():
    """Usa las funciones ejecutadas, no resultados escritos a mano."""
    for numero, funcion, titulo in EJERCICIOS:
        codigo = getsource(funcion).rstrip()
        salida = pformat(funcion(), width=75, sort_dicts=False)
        contenido = (
            f"\\begin{{lstlisting}}[language=Python,caption={{{titulo}: código ejecutable}}]\n"
            f"{codigo}\n"
            "\\end{lstlisting}\n"
            "\\noindent\\textbf{Resultado de la ejecución:}\n"
            "\\begin{lstlisting}[style=consolestyle]\n"
            f">>> {funcion.__name__}()\n{salida}\n"
            "\\end{lstlisting}\n"
        )
        (DESTINO / f"02_resuelto_{numero}_generado.tex").write_text(
            contenido, encoding="utf-8"
        )


if __name__ == "__main__":
    renderizar()
