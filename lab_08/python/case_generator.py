"""Vectores y casos reproducibles de la Guía 08 (no generar dentro de la medición)."""

from random import Random

SEED = 20260813
SIZES = tuple(1 << k for k in range(3, 15))
RANGES = {"pequeno": (-10, 10), "mediano": (-1000, 1000)}
MANUAL_CASES = (
    ([], [1, 2], []),
    ([0], [0], [0]),
    ([3], [-2], [-6]),
    ([1, 2, 3], [4, 5], [4, 13, 22, 15]),
    ([1, -1], [1, 1], [1, 0, -1]),
    ([1, 0, 0, 1], [1, 1], [1, 1, 0, 1, 1]),
)


def polynomial_pair(size, seed=SEED, bounds=(-10, 10)):
    """Par de longitud size, generado independientemente con semilla local."""
    if size < 1 or bounds[0] > bounds[1]:
        raise ValueError("Tamaño y límites inválidos")
    rng = Random(seed)
    return ([rng.randint(*bounds) for _ in range(size)],
            [rng.randint(*bounds) for _ in range(size)])
