"""Convolución lineal, FFT compleja y NTT radix-2 (Guía 08, UNSAAC).

Los coeficientes se almacenan en orden ascendente. Las multiplicaciones de
entradas no vacías devuelven len(a)+len(b)-1 posiciones, incluso para cero.
FFT trabaja con complejos; NTT trabaja exactamente en el campo F_p.
"""

from cmath import exp, pi
from dataclasses import dataclass
from functools import lru_cache
from math import gcd, isfinite, isqrt

MODULUS = 998244353  # 119 * 2**23 + 1; 3 genera F_p^*.
PRIMITIVE_ROOT = 3


@dataclass
class OperationCounts:
    """Conteos ejecutados: una mariposa = 2 sumas y 2 productos (giro y avance).

    ``multiplications`` también incluye producto punto a punto y escalado
    inverso; ``stages`` suma etapas de cada transformada (no de cada nodo).
    No incluye inversos, exponenciaciones de configuración ni permutaciones.
    """

    butterflies: int = 0
    multiplications: int = 0
    additions: int = 0
    stages: int = 0


def _check_length(n):
    if n < 1 or n & (n - 1):
        raise ValueError("La longitud debe ser una potencia de dos positiva")


def next_power_of_two(value):
    """Menor potencia de 2 >= value; value debe ser entero positivo."""
    if type(value) is not int:
        raise TypeError("value debe ser entero")
    if value < 1:
        raise ValueError("value debe ser positivo")
    return 1 << (value - 1).bit_length()


def naive_convolution(a, b, *, stats=None):
    """Convolución lineal exacta para enteros; [] si una entrada está vacía."""
    if not a or not b:
        return []
    result = [0] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        for j, bj in enumerate(b):
            result[i + j] += ai * bj
            if stats is not None:
                stats.multiplications += 1
                stats.additions += 1
    return result


def _butterfly(stats):
    if stats is not None:
        stats.butterflies += 1
        stats.multiplications += 2  # twiddle * odd; twiddle *= root
        stats.additions += 2         # even + t; even - t


def fft(values, *, stats=None):
    """DFT recursiva de signo +, radix-2; no modifica values.

    Pre: longitud potencia de dos positiva. Post: N complejos; excepción
    ValueError para 0 o longitud no compatible. Error de punto flotante posible.
    """
    n = len(values)
    _check_length(n)
    if stats is not None:
        stats.stages += n.bit_length() - 1

    def transform(a):
        size = len(a)
        if size == 1:
            return [complex(a[0])]
        even = transform(a[::2])
        odd = transform(a[1::2])
        root = exp(2j * pi / size)
        w = 1 + 0j
        result = [0j] * size
        for k in range(size // 2):
            t = w * odd[k]
            result[k] = even[k] + t
            result[k + size // 2] = even[k] - t
            w *= root
            _butterfly(stats)
        return result

    return transform(values)


def ifft(values, *, stats=None):
    """DFT inversa, conjugación y normalización por N; misma precondición FFT."""
    _check_length(len(values))
    transformed = fft([complex(z).conjugate() for z in values], stats=stats)
    if stats is not None:
        stats.multiplications += len(values)
    return [z.conjugate() / len(values) for z in transformed]


def _bit_reverse(values):
    n = len(values)
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit
        if i < j:
            values[i], values[j] = values[j], values[i]


def fft_iterative(values, *, invert=False, stats=None):
    """FFT radix-2 iterativa in-place; modifica una lista de N valores.

    Pre: lista, N potencia de dos positiva. Pos: DFT signo + (o inversa,
    normalizada si invert=True). ValueError/TypeError si la entrada es inválida.
    """
    if not isinstance(values, list):
        raise TypeError("La FFT iterativa requiere una lista mutable")
    n = len(values)
    _check_length(n)
    _bit_reverse(values)
    size = 2
    while size <= n:
        root = exp((-2j if invert else 2j) * pi / size)
        for start in range(0, n, size):
            w = 1 + 0j
            for k in range(size // 2):
                u = values[start + k]
                t = w * values[start + k + size // 2]
                values[start + k] = u + t
                values[start + k + size // 2] = u - t
                w *= root
                _butterfly(stats)
        if stats is not None:
            stats.stages += 1
        size <<= 1
    if invert:
        for i in range(n):
            values[i] /= n
        if stats is not None:
            stats.multiplications += n
    return values


def convolution_fft_raw(a, b, *, method="recursive", stats=None):
    """Producto sin redondear: coeficientes complejos antes de normalización.

    Útil para medir errores reales/imaginarios. [] si alguna entrada es vacía.
    """
    if method not in ("recursive", "iterative"):
        raise ValueError("method debe ser 'recursive' o 'iterative'")
    if not a or not b:
        return []
    length = len(a) + len(b) - 1
    n = next_power_of_two(length)
    pa = list(a) + [0] * (n - len(a))
    pb = list(b) + [0] * (n - len(b))
    if method == "recursive":
        fa, fb = fft(pa, stats=stats), fft(pb, stats=stats)
    else:
        fa = fft_iterative(pa, stats=stats)
        fb = fft_iterative(pb, stats=stats)
    fc = [x * y for x, y in zip(fa, fb)]
    if stats is not None:
        stats.multiplications += n
    if method == "recursive":
        return ifft(fc, stats=stats)[:length]
    return fft_iterative(fc, invert=True, stats=stats)[:length]


def multiply_fft(a, b, tolerance=1e-7, *, method="recursive", stats=None):
    """Convolución entera por FFT; rechaza error imaginario o real excesivo.

    Pre: coeficientes enteros y tolerancia finita no negativa. Pos: salida
    entera de m+n-1; ArithmeticError si el redondeo no es confiable.
    """
    if not isinstance(tolerance, (int, float)) or not isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance debe ser finita y no negativa")
    if any(type(x) is not int for values in (a, b) for x in values):
        raise TypeError("multiply_fft requiere coeficientes enteros")
    values = convolution_fft_raw(a, b, method=method, stats=stats)
    result = []
    for z in values:
        rounded = round(z.real)
        if abs(z.imag) > tolerance or abs(z.real - rounded) > tolerance:
            raise ArithmeticError("Error FFT superior a la tolerancia")
        result.append(rounded)
    return result


@lru_cache(maxsize=None)
def _prime(modulus):
    if type(modulus) is not int or modulus < 2:
        return False
    if modulus == 2:
        return True
    if modulus % 2 == 0:
        return False
    return all(modulus % d for d in range(3, isqrt(modulus) + 1, 2))


def modular_inverse(a, modulus):
    """Inverso multiplicativo; ValueError si modulus<=1 o no es coprimo."""
    if type(a) is not int or type(modulus) is not int:
        raise TypeError("Se requieren enteros")
    if modulus < 2 or gcd(a, modulus) != 1:
        raise ValueError("El inverso modular no existe")
    return pow(a, -1, modulus)


def validate_root(root, length, modulus):
    """Comprueba raíz de orden EXACTO length en el campo primo F_modulus.

    Rechaza módulos compuestos, N no potencia de 2, N que no divide p-1 y
    raíces de orden menor. Para N=1 la única raíz es 1.
    """
    if type(root) is not int or type(length) is not int or type(modulus) is not int:
        raise TypeError("Raíz, longitud y módulo deben ser enteros")
    _check_length(length)
    if not _prime(modulus):
        raise ValueError("El módulo debe ser primo")
    if (modulus - 1) % length:
        raise ValueError("N debe dividir p-1")
    root %= modulus
    if pow(root, length, modulus) != 1 or (
        length > 1 and pow(root, length // 2, modulus) == 1
    ):
        raise ValueError("La raíz no tiene orden exacto N")
    return True


def _prime_factors(value):
    factors = set()
    divisor = 2
    while divisor * divisor <= value:
        if value % divisor == 0:
            factors.add(divisor)
            while value % divisor == 0:
                value //= divisor
        divisor += 1 if divisor == 2 else 2
    if value > 1:
        factors.add(value)
    return factors


def _validate_generator(generator, modulus):
    if type(generator) is not int:
        raise TypeError("primitive_root debe ser entero")
    if not _prime(modulus):
        raise ValueError("El módulo debe ser primo")
    if generator % modulus == 0 or any(
        pow(generator, (modulus - 1) // factor, modulus) == 1
        for factor in _prime_factors(modulus - 1)
    ):
        raise ValueError("primitive_root debe generar F_p^*")


def ntt(values, invert, modulus, root, *, stats=None):
    """NTT/INTT radix-2, sin mutar entrada; root tiene orden len(values).

    Pre: p primo, N potencia de dos, N|(p-1), raíz válida. Pos: residuos
    canónicos 0..p-1; la inversa multiplica por N^{-1} módulo p.
    """
    n = len(values)
    validate_root(root, n, modulus)
    if any(type(x) is not int for x in values):
        raise TypeError("NTT requiere coeficientes enteros")
    data = [x % modulus for x in values]
    _bit_reverse(data)
    if invert:
        root = modular_inverse(root % modulus, modulus)
    size = 2
    while size <= n:
        step = pow(root, n // size, modulus)
        for start in range(0, n, size):
            w = 1
            for k in range(size // 2):
                u = data[start + k]
                t = w * data[start + k + size // 2] % modulus
                data[start + k] = (u + t) % modulus
                data[start + k + size // 2] = (u - t) % modulus
                w = w * step % modulus
                _butterfly(stats)
        if stats is not None:
            stats.stages += 1
        size <<= 1
    if invert:
        inverse_n = modular_inverse(n, modulus)
        data = [x * inverse_n % modulus for x in data]
        if stats is not None:
            stats.multiplications += n
    return data


def multiply_ntt(a, b, modulus, primitive_root, *, stats=None):
    """Convolución lineal exacta MODULO p; no recupera enteros sin cota/CRT.

    Pre: p primo, primitive_root generador y N<=máxima potencia de 2 de p-1.
    Pos: exactamente m+n-1 residuos canónicos, [] si entrada vacía.
    """
    _validate_generator(primitive_root, modulus)
    if not a or not b:
        return []
    length = len(a) + len(b) - 1
    n = next_power_of_two(length)
    if (modulus - 1) % n:
        raise ValueError("El módulo no permite la longitud N requerida")
    root = pow(primitive_root, (modulus - 1) // n, modulus)
    validate_root(root, n, modulus)
    pa = list(a) + [0] * (n - len(a))
    pb = list(b) + [0] * (n - len(b))
    fa, fb = ntt(pa, False, modulus, root, stats=stats), ntt(pb, False, modulus, root, stats=stats)
    pointwise = [x * y % modulus for x, y in zip(fa, fb)]
    if stats is not None:
        stats.multiplications += n
    return ntt(pointwise, True, modulus, root, stats=stats)[:length]
