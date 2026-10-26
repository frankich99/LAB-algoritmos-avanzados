"""
number_theory.py
================

Biblioteca de algoritmos fundamentales de teoría de números.
Guía de Laboratorio N.º 06 - Algoritmos Avanzados (UNSAAC, 2026-II).

Funciones de la interfaz requerida
----------------------------------
- gcd_trace(a, b)                      -> (d, traza)
- extended_gcd(a, b)                   -> (d, x, y)
- modular_inverse(a, n)                -> u
- solve_linear_congruence(a, b, n)     -> [x_0, ..., x_{d-1}]
- modular_pow(base, exponent, modulus) -> (valor, cuadrados, productos)
- crt(residues, moduli)                -> (x, N)
- validate_crt_solution(x, residues, moduli) -> bool

Funciones auxiliares
--------------------
- crt_with_trace(residues, moduli)     -> (x, N, traza)
- naive_pow_multiplications(exponent)  -> número de multiplicaciones del método directo

Convención para (0, 0): mcd(0, 0) = 0 (convención usada por math.gcd).
La traza para (0, 0) es vacía y extended_gcd(0, 0) devuelve (0, 0, 0),
que satisface trivialmente 0*0 + 0*0 = 0.
"""

from math import prod

__all__ = [
    "gcd_trace",
    "extended_gcd",
    "modular_inverse",
    "solve_linear_congruence",
    "modular_pow",
    "crt",
    "crt_with_trace",
    "validate_crt_solution",
    "naive_pow_multiplications",
]


def _check_int(*values):
    """Verifica que todos los argumentos sean enteros (no bool)."""
    for v in values:
        if not isinstance(v, int) or isinstance(v, bool):
            raise TypeError(f"Se esperaba un entero y se recibió {type(v).__name__}")


# ---------------------------------------------------------------------------
# 1. Algoritmo de Euclides con traza
# ---------------------------------------------------------------------------
def gcd_trace(a, b):
    """Calcula mcd(a, b) con el algoritmo de Euclides y registra cada división.

    Precondiciones:
        a, b son enteros (pueden ser negativos o cero).
    Poscondiciones:
        Devuelve (d, trace) donde d = mcd(|a|, |b|) >= 0 y trace es una lista
        de tuplas (a_i, b_i, q_i, r_i) que cumplen a_i = b_i*q_i + r_i y
        0 <= r_i < b_i. len(trace) es el número de divisiones realizadas.
        Para (0, 0) se devuelve (0, []) por convención.
    Excepciones:
        TypeError si algún argumento no es entero.
    """
    _check_int(a, b)
    a, b = abs(a), abs(b)
    trace = []
    while b != 0:
        q, r = divmod(a, b)
        trace.append((a, b, q, r))
        a, b = b, r
    return a, trace


# ---------------------------------------------------------------------------
# 2. Euclides extendido (forma iterativa)
# ---------------------------------------------------------------------------
def extended_gcd(a, b):
    """Calcula d = mcd(a, b) y coeficientes de Bézout x, y con a*x + b*y = d.

    Precondiciones:
        a, b son enteros.
    Poscondiciones:
        Devuelve (d, x, y) con d >= 0 y a*x + b*y == d.
        Para (0, 0) devuelve (0, 0, 0).
    Excepciones:
        TypeError si algún argumento no es entero.
    """
    _check_int(a, b)
    old_r, r = abs(a), abs(b)
    old_s, s = 1, 0
    old_t, t = 0, 1
    while r != 0:
        q = old_r // r
        old_r, r = r, old_r - q * r
        old_s, s = s, old_s - q * s
        old_t, t = t, old_t - q * t
    if old_r == 0:          # caso (0, 0)
        return 0, 0, 0
    x = old_s if a >= 0 else -old_s
    y = old_t if b >= 0 else -old_t
    return old_r, x, y


# ---------------------------------------------------------------------------
# 3. Inverso modular
# ---------------------------------------------------------------------------
def modular_inverse(a, n):
    """Calcula el inverso de a módulo n.

    Precondiciones:
        a entero cualquiera (puede ser negativo o mayor que n); n entero > 1.
    Poscondiciones:
        Devuelve u en {1, ..., n-1} tal que (a*u) % n == 1.
    Excepciones:
        ValueError si n <= 1 o si mcd(a, n) != 1 (el inverso no existe).
        TypeError si algún argumento no es entero.
    """
    _check_int(a, n)
    if n <= 1:
        raise ValueError("El modulo debe ser mayor que uno")
    d, x, _ = extended_gcd(a, n)
    if d != 1:
        raise ValueError(f"El inverso modular no existe: mcd({a}, {n}) = {d}")
    return x % n


# ---------------------------------------------------------------------------
# 4. Congruencias lineales a x ≡ b (mod n)
# ---------------------------------------------------------------------------
def solve_linear_congruence(a, b, n):
    """Resuelve a*x ≡ b (mod n) y devuelve todas las soluciones módulo n.

    Precondiciones:
        a, b enteros; n entero > 0.
    Poscondiciones:
        Si d = mcd(a, n) no divide a b, devuelve [].
        En otro caso devuelve una lista ordenada de exactamente d valores
        distintos en {0, ..., n-1}, cada uno con (a*x - b) % n == 0.
        Caso especial: si a ≡ 0 (mod n), d = n y la congruencia 0 ≡ b
        tiene n soluciones si b ≡ 0 y ninguna en otro caso.
    Excepciones:
        ValueError si n <= 0. TypeError si algún argumento no es entero.
    """
    _check_int(a, b, n)
    if n <= 0:
        raise ValueError("El modulo debe ser positivo")
    a %= n
    b %= n
    if a == 0:
        return list(range(n)) if b == 0 else []
    d, x, _ = extended_gcd(a, n)
    if b % d != 0:
        return []
    reduced_modulus = n // d
    x0 = (x * (b // d)) % reduced_modulus
    return sorted((x0 + k * reduced_modulus) % n for k in range(d))


# ---------------------------------------------------------------------------
# 5. Exponenciación modular binaria instrumentada
# ---------------------------------------------------------------------------
def modular_pow(base, exponent, modulus):
    """Calcula base**exponent mod modulus por cuadrados sucesivos (derecha a izquierda).

    Precondiciones:
        base entero cualquiera; exponent entero >= 0; modulus entero > 0.
    Poscondiciones:
        Devuelve (valor, squares, selected_products) donde
          valor == pow(base, exponent, modulus),
          squares == max(exponent.bit_length() - 1, 0),
          selected_products == número de bits 1 de exponent (popcount).
        Nunca se construye la potencia completa: todo intermedio es < modulus**2.
    Excepciones:
        ValueError si modulus <= 0 o exponent < 0. TypeError si no son enteros.
    """
    _check_int(base, exponent, modulus)
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


def naive_pow_multiplications(exponent):
    """Número de multiplicaciones del método directo a*a*...*a: e - 1 (0 si e <= 1)."""
    return max(exponent - 1, 0)


# ---------------------------------------------------------------------------
# 6. Teorema chino del resto
# ---------------------------------------------------------------------------
def _validate_crt_input(residues, moduli):
    """Valida longitudes, módulos > 1 y coprimalidad dos a dos."""
    residues = list(residues)
    moduli = list(moduli)
    if len(residues) == 0 or len(moduli) == 0:
        raise ValueError("Las listas de residuos y modulos no pueden estar vacias")
    if len(residues) != len(moduli):
        raise ValueError("Residuos y modulos deben tener la misma longitud")
    _check_int(*residues, *moduli)
    for n in moduli:
        if n <= 1:
            raise ValueError(f"Todos los modulos deben ser mayores que uno (se recibio {n})")
    k = len(moduli)
    for i in range(k):
        for j in range(i + 1, k):
            g, _ = gcd_trace(moduli[i], moduli[j])
            if g != 1:
                raise ValueError(
                    f"Los modulos {moduli[i]} y {moduli[j]} no son coprimos (mcd = {g})"
                )
    return residues, moduli


def crt_with_trace(residues, moduli):
    """TCR con traza de construcción.

    Precondiciones:
        residues y moduli son listas no vacías de igual longitud, de enteros;
        cada n_i > 1 y mcd(n_i, n_j) = 1 para i != j. Los residuos pueden ser
        negativos o mayores que su módulo.
    Poscondiciones:
        Devuelve (x, N, trace) con N = prod(n_i), 0 <= x < N, x ≡ a_i (mod n_i)
        para todo i, y trace una lista de diccionarios con claves
        i, a_i, n_i, N_i, M_i, a_i*N_i*M_i (a_i normalizado en [0, n_i)).
        No realiza búsqueda exhaustiva: costo O(k^2 log N) operaciones aritméticas.
    Excepciones:
        ValueError ante listas vacías, longitudes distintas, módulos <= 1
        o módulos no coprimos. TypeError si hay valores no enteros.
    """
    residues, moduli = _validate_crt_input(residues, moduli)
    N = prod(moduli)
    total = 0
    trace = []
    for i, (a_i, n_i) in enumerate(zip(residues, moduli), start=1):
        a_norm = a_i % n_i
        N_i = N // n_i
        M_i = modular_inverse(N_i % n_i, n_i)
        term = a_norm * N_i * M_i
        total += term
        trace.append({"i": i, "a_i": a_norm, "n_i": n_i, "N_i": N_i,
                      "M_i": M_i, "a_i*N_i*M_i": term})
    return total % N, N, trace


def crt(residues, moduli):
    """Resuelve x ≡ a_i (mod n_i) para módulos coprimos dos a dos.

    Devuelve (x, N): x es el menor representante no negativo y N = prod(n_i).
    Ver crt_with_trace para precondiciones y excepciones.
    """
    x, N, _ = crt_with_trace(residues, moduli)
    return x, N


def validate_crt_solution(x, residues, moduli):
    """Comprueba que x satisface simultáneamente todas las congruencias x ≡ a_i (mod n_i).

    Precondiciones: listas de igual longitud y módulos positivos.
    Poscondiciones: True si (x - a_i) % n_i == 0 para todo i; False en otro caso.
    Excepciones: ValueError si las longitudes difieren o algún módulo es <= 0.
    """
    residues = list(residues)
    moduli = list(moduli)
    if len(residues) != len(moduli):
        raise ValueError("Residuos y modulos deben tener la misma longitud")
    if any(n <= 0 for n in moduli):
        raise ValueError("Los modulos deben ser positivos")
    return all((x - a) % n == 0 for a, n in zip(residues, moduli))


if __name__ == "__main__":
    # Ejecución rápida de los casos de la guía
    print(gcd_trace(252, 105))
    print(extended_gcd(252, 105))
    print(modular_inverse(7, 40))
    print(solve_linear_congruence(14, 30, 100))
    print(modular_pow(7, 13, 20))
    x, N, tr = crt_with_trace([2, 3, 2], [3, 5, 7])
    print((x, N))
    for row in tr:
        print(row)
