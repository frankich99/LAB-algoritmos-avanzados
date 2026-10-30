"""Casos reproducibles de laboratorio; random.Random NO sirve para claves."""

from random import Random

from primality import generate_candidate

SEED = 202607
SIZES = (16, 32, 64, 128, 256, 512, 1024)
KNOWN_CASES = (
    (0, False), (1, False), (2, True), (3, True), (4, False),
    (5, True), (7, True), (9, False), (25, False), (49, False),
    (97, True), (221, False), (341, False), (561, False),
    (1105, False), (1729, False),
)


def make_rng(seed=SEED):
    return Random(seed)


def random_composite(bits, rng):
    """Producto impar de dos factores > 1, exactamente bits bits.

    A diferencia de una etiqueta probabilística, este constructor garantiza
    composición; no presupone que los factores sean primos.
    """
    if bits < 4:
        raise ValueError("bits debe ser >= 4")
    left = bits // 2
    right = bits - left
    while True:
        a = generate_candidate(left, rng)
        b = generate_candidate(right, rng)
        n = a * b
        if n.bit_length() == bits:
            return n


def benchmark_inputs(bits, primes, rng, count=8):
    """Pares equilibrados probable primo/compuesto; bases compartidas."""
    cases = []
    for i in range(count):
        prime_label = "primo_verificado" if bits <= 32 else "probable_primo"
        for kind, n in ((prime_label, primes[i]),
                        ("compuesto_construido", random_composite(bits, rng))):
            bases = tuple(rng.randrange(2, n - 1) for _ in range(20))
            cases.append({"bits": bits, "tipo": kind, "n": n,
                          "bases": bases, "indice": i})
    return cases
