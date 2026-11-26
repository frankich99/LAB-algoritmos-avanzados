"""Tres ejercicios resueltos de la sección 8 de la Guía 09 (UNSAAC)."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import heapq
import itertools
import math
import struct


@dataclass
class Node:
    freq: int
    symbol: int | None = None
    left: "Node | None" = None
    right: "Node | None" = None


def build_tree(data: bytes) -> Node | None:
    freq = Counter(data)
    serial = itertools.count()
    heap = []
    for symbol, count in freq.items():
        heapq.heappush(heap, (count, next(serial), Node(count, symbol)))
    if not heap:
        return None
    if len(heap) == 1:
        count, _, only = heapq.heappop(heap)
        return Node(count, left=only)
    while len(heap) > 1:
        f1, _, a = heapq.heappop(heap)
        f2, _, b = heapq.heappop(heap)
        parent = Node(f1 + f2, left=a, right=b)
        heapq.heappush(heap, (parent.freq, next(serial), parent))
    return heap[0][2]


def make_codes(node: Node, prefix: str = "", codes: dict[int, str] | None = None) -> dict[int, str]:
    if codes is None:
        codes = {}
    if node.symbol is not None:
        codes[node.symbol] = prefix or "0"
        return codes
    if node.left is not None:
        make_codes(node.left, prefix + "0", codes)
    if node.right is not None:
        make_codes(node.right, prefix + "1", codes)
    return codes


def huffman_encode(data: bytes, codes: dict[int, str]) -> str:
    return "".join(codes[b] for b in data)


def huffman_decode(bits: str, root: Node | None, original_size: int) -> bytes:
    if original_size == 0 or root is None:
        return b""
    out = bytearray()
    node = root
    for bit in bits:
        node = node.left if bit == "0" else node.right
        if node.symbol is not None:
            out.append(node.symbol)
            if len(out) == original_size:
                break
            node = root
    return bytes(out)


def resuelto_1() -> dict:
    """Huffman completo sobre b'AAAABBCD' con verificación de entropía y longitud."""
    data = b"AAAABBCD"
    freq = dict(Counter(data))
    root = build_tree(data)
    codes = make_codes(root)
    bits = huffman_encode(data, codes)
    restored = huffman_decode(bits, root, len(data))
    assert restored == data
    assert sum(freq.values()) == len(data)
    ordered = sorted(codes.values())
    assert all(not ordered[i + 1].startswith(ordered[i]) for i in range(len(ordered) - 1))
    n = len(data)
    h_val = -sum((c / n) * math.log2(c / n) for c in freq.values())
    l_val = sum((c / n) * len(codes[s]) for s, c in freq.items())
    assert abs(h_val - 1.75) < 1e-12 and abs(l_val - 1.75) < 1e-12
    return {
        "entrada": data.decode("ascii"),
        "codigos": {chr(k): v for k, v in sorted(codes.items())},
        "bits": bits,
        "bits_totales": len(bits),
        "entropia_H": round(h_val, 4),
        "longitud_promedio_L": round(l_val, 4),
        "reconstruccion_exacta": restored == data,
    }


def canonical_codes_demo(lengths: dict[int, int]) -> dict[int, str]:
    """Reconstrucción determinista de códigos Huffman canónicos."""
    ordered = sorted(lengths.items(), key=lambda x: (x[1], x[0]))
    if not ordered:
        return {}
    codes = {}
    code = 0
    previous_length = ordered[0][1]
    for symbol, length in ordered:
        code <<= length - previous_length
        codes[symbol] = format(code, f"0{length}b")
        code += 1
        previous_length = length
    return codes


def resuelto_2() -> dict:
    """Reconstrucción Huffman canónica desde longitudes (Sección 8.2)."""
    lengths = {
        ord("A"): 2,
        ord("B"): 2,
        ord("C"): 2,
        ord("D"): 3,
        ord("E"): 3,
    }
    codes = canonical_codes_demo(lengths)
    readable = {chr(k): v for k, v in codes.items()}
    assert readable == {"A": "00", "B": "01", "C": "10", "D": "110", "E": "111"}
    sample = b"AAABBBCCCDE"
    encoded_bits = "".join(codes[b] for b in sample)
    return {
        "longitudes": {chr(k): v for k, v in lengths.items()},
        "codigos_canonicos": readable,
        "muestra": sample.decode("ascii"),
        "bits_codificados": len(encoded_bits),
        "flujo_bits": encoded_bits,
    }


HEADER = struct.Struct(">Q")
RUN = struct.Struct(">BH")


def rle_compress(data: bytes) -> bytes:
    out = bytearray(HEADER.pack(len(data)))
    if not data:
        return bytes(out)
    symbol = data[0]
    count = 1
    for current in data[1:]:
        if current == symbol and count < 65535:
            count += 1
        else:
            out.extend(RUN.pack(symbol, count))
            symbol = current
            count = 1
    out.extend(RUN.pack(symbol, count))
    return bytes(out)


def rle_decompress(payload: bytes) -> bytes:
    if len(payload) < HEADER.size:
        raise ValueError("Encabezado incompleto")
    original_size = HEADER.unpack_from(payload, 0)[0]
    body = payload[HEADER.size:]
    if len(body) % RUN.size != 0:
        raise ValueError("Cuerpo RLE incompleto")
    out = bytearray()
    for pos in range(0, len(body), RUN.size):
        symbol, count = RUN.unpack_from(body, pos)
        if count == 0:
            raise ValueError("Corrida invalida")
        out.extend([symbol] * count)
    if len(out) != original_size:
        raise ValueError("Tamano original inconsistente")
    return bytes(out)


def resuelto_3() -> dict:
    """RLE binario sobre b'AAAAAABBBBCCCCCCCCCC' y medición del tamaño total Sc = 8 + 3r."""
    data = b"AAAAAABBBBCCCCCCCCCC"
    payload = rle_compress(data)
    restored = rle_decompress(payload)
    assert restored == data and len(payload) == 17
    return {
        "original_bytes": len(data),
        "comprimido_bytes": len(payload),
        "formula": "8 + 3*3 = 17",
        "ahorro_pct": round((1.0 - len(payload) / len(data)) * 100.0, 2),
        "reconstruccion_exacta": restored == data,
    }


def main() -> None:
    for number, func in enumerate((resuelto_1, resuelto_2, resuelto_3), 1):
        print(f"Resuelto {number}: {func()}")


if __name__ == "__main__":
    main()
