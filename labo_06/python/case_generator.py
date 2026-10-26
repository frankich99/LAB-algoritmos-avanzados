"""
case_generator.py
=================

Generador reproducible de casos aleatorios para la Guía 06.
Todas las funciones reciben un objeto random.Random inicializado con una
semilla fija, de modo que cada experimento puede repetirse exactamente.
"""

import random
from math import gcd

SEED = 20262  # semilla global del laboratorio (2026-II)

FIB_PAIRS = [(13, 8), (89, 55), (6765, 4181), (832040, 514229)]


def make_rng(seed=SEED):
    """Crea un generador pseudoaleatorio reproducible."""
    return random.Random(seed)


def random_int_bits(rng, bits):
    """Entero aleatorio con exactamente `bits` bits (el bit más alto es 1)."""
    if bits <= 0:
        return 0
    return rng.getrandbits(bits) | (1 << (bits - 1))


def random_pair(rng, bits, allow_negative=True):
    """Par (a, b) con `bits` bits cada uno y signo aleatorio opcional."""
    a = random_int_bits(rng, bits)
    b = random_int_bits(rng, bits)
    if allow_negative:
        if rng.random() < 0.25:
            a = -a
        if rng.random() < 0.25:
            b = -b
    return a, b


def exponent_with_popcount(rng, bits, ones):
    """Exponente de `bits` bits con exactamente `ones` bits iguales a 1 (el más alto incluido)."""
    if not 1 <= ones <= bits:
        raise ValueError("ones debe estar entre 1 y bits")
    positions = rng.sample(range(bits - 1), ones - 1)
    e = 1 << (bits - 1)
    for p in positions:
        e |= 1 << p
    return e


def random_coprime_moduli(rng, k, low=2, high=10_000):
    """Lista de k módulos > 1 coprimos dos a dos."""
    moduli = []
    while len(moduli) < k:
        candidate = rng.randint(low, high)
        if all(gcd(candidate, m) == 1 for m in moduli):
            moduli.append(candidate)
    return moduli


def random_crt_system(rng, k, low=2, high=10_000):
    """Sistema TCR construido a partir de una solución conocida.

    Devuelve (x_conocida, residuos, módulos). Los residuos se desplazan con
    múltiplos aleatorios del módulo para obtener valores no normalizados.
    """
    moduli = random_coprime_moduli(rng, k, low, high)
    N = 1
    for m in moduli:
        N *= m
    x_known = rng.randrange(N)
    residues = [x_known % m + rng.randint(-3, 3) * m for m in moduli]
    return x_known, residues, moduli


def random_congruence(rng, n_max=1000, force_solvable=None):
    """Congruencia a x ≡ b (mod n). force_solvable=True/False fuerza el tipo."""
    while True:
        n = rng.randint(2, n_max)
        a = rng.randint(-n_max, n_max)
        b = rng.randint(-n_max, n_max)
        if a % n == 0:
            continue
        d = gcd(a, n)
        solvable = (b % d == 0)
        if force_solvable is None or force_solvable == solvable:
            return a, b, n
