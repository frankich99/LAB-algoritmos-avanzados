"""
ejercicios_resueltos.py
======================

Ejercicios resueltos 1, 2 y 3 de la Guía 06, tal como se ejecutan en el cuaderno de Colab.
"""
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# --- Ejercicio resuelto 1: Euclides con traza y coeficientes de Bézout ---
def gcd_trace(a, b):
    a, b = abs(a), abs(b)
    trace = []
    while b != 0:
        q, r = divmod(a, b)
        trace.append((a, b, q, r))
        a, b = b, r
    return a, trace


def extended_gcd(a, b):
    old_r, r = abs(a), abs(b)
    old_s, s = 1, 0
    old_t, t = 0, 1
    while r != 0:
        q = old_r // r
        old_r, r = r, old_r - q * r
        old_s, s = s, old_s - q * s
        old_t, t = t, old_t - q * t
    x = old_s if a >= 0 else -old_s
    y = old_t if b >= 0 else -old_t
    return old_r, x, y


d, trace = gcd_trace(252, 105)
assert d == 21
assert trace == [(252, 105, 2, 42), (105, 42, 2, 21), (42, 21, 2, 0)]
d, x, y = extended_gcd(252, 105)
assert (d, x, y) == (21, -2, 5)
assert 252 * x + 105 * y == d
print("Traza:")
for fila in trace:
    print("  {} = {}·{} + {}".format(*fila))
print(f"Bézout: {d} = 252·({x}) + 105·({y})")


# --- Ejercicio resuelto 2: inversos y congruencias lineales ---
def modular_inverse(a, n):
    if n <= 1:
        raise ValueError("El modulo debe ser mayor que uno")
    d, x, _ = extended_gcd(a, n)
    if d != 1:
        raise ValueError("El inverso modular no existe")
    return x % n


def solve_linear_congruence(a, b, n):
    if n <= 0:
        raise ValueError("El modulo debe ser positivo")
    d, x, _ = extended_gcd(a, n)
    if b % d != 0:
        return []
    reduced_modulus = n // d
    x0 = (x * (b // d)) % reduced_modulus
    return [(x0 + k * reduced_modulus) % n for k in range(d)]


assert modular_inverse(7, 40) == 23
assert (7 * 23) % 40 == 1
solutions = solve_linear_congruence(14, 30, 100)
assert solutions == [45, 95]
assert all((14 * x - 30) % 100 == 0 for x in solutions)
print("7^(-1) mod 40 =", modular_inverse(7, 40))
print("14x ≡ 30 (mod 100) →", solutions)


# --- Ejercicio resuelto 3: exponenciación modular binaria instrumentada ---
def modular_pow(base, exponent, modulus):
    if modulus <= 0:
        raise ValueError("El modulo debe ser positivo")
    if exponent < 0:
        raise ValueError("El exponente debe ser no negativo")
    result = 1 % modulus
    base %= modulus
    squares = 0
    selected_products = 0
    while exponent > 0:
        if exponent & 1:
            result = (result * base) % modulus
            selected_products += 1
        exponent >>= 1
        if exponent > 0:
            base = (base * base) % modulus
            squares += 1
    return result, squares, selected_products


value, squares, products = modular_pow(7, 13, 20)
assert value == pow(7, 13, 20) == 7
assert squares == 3 and products == 3
print(f"7^13 mod 20 = {value} | cuadrados = {squares} | productos = {products} | 13 = {bin(13)}")
