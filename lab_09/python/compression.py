"""Biblioteca integrada de compresión sin pérdida (Guía 09, UNSAAC).

Implementa bajo una interfaz común (``Compressor``) y funciones puras:
1. Huffman canónico (con empaquetado real de bits y tabla símbolo-longitud).
2. RLE binario sobre pares (símbolo, corrida uint16).
3. LZ77 con ventana deslizante, bloques de 8 banderas y referencias empaquetadas.

Formato binario unificado ``CMP9`` (versión 1):
- Encabezado fijo (6 bytes): ``magic`` (4B = b"CMP9"), ``version`` (1B = 1),
  ``alg_id`` (1B: 1=Huffman, 2=RLE, 3=LZ77).
- Metadatos específicos de cada método (tamaño original, bits válidos/parámetros
  y tabla de longitudes o conteo de tokens).
- Datos codificados (flujo empaquetado de bits, corridas o bloques de tokens).
"""

from __future__ import annotations

from collections import Counter, defaultdict, deque
from dataclasses import dataclass
import heapq
import itertools
import math
import struct

MAGIC = b"CMP9"
FORMAT_VERSION = 1

ALG_HUFFMAN = 1
ALG_RLE = 2
ALG_LZ77 = 3

ALG_NAMES = {
    ALG_HUFFMAN: "huffman_canonico",
    ALG_RLE: "rle",
    ALG_LZ77: "lz77",
}

HEADER_STRUCT = struct.Struct(">4sBB")        # magic, version, alg_id (6 B)
HUFF_META_STRUCT = struct.Struct(">QBH")      # original_size, padding_bits, sym_count (11 B)
HUFF_SYM_STRUCT = struct.Struct(">BB")        # symbol, bit_length (2 B)
RLE_META_STRUCT = struct.Struct(">QI")        # original_size, num_runs (12 B)
RLE_RUN_STRUCT = struct.Struct(">BH")         # symbol, count (3 B)
LZ77_META_STRUCT = struct.Struct(">QHBBI")    # orig, win, min_m, max_m, tokens (16 B)
LZ77_MATCH_STRUCT = struct.Struct(">H")       # 12-bit (offset-1) | 4-bit (len-min) (2 B)

MAX_RLE_RUN = 65535
DEFAULT_LZ77_WINDOW = 4096
DEFAULT_LZ77_MIN_MATCH = 3
DEFAULT_LZ77_MAX_MATCH = 18


@dataclass
class HuffmanNode:
    """Nodo del árbol binario de Huffman."""

    freq: int
    symbol: int | None = None
    left: "HuffmanNode | None" = None
    right: "HuffmanNode | None" = None


@dataclass
class CompressionStats:
    """Desglose auditable de tamaños y métricas estructurales."""

    algorithm: str
    original_bytes: int
    header_bytes: int
    metadata_bytes: int
    data_bytes: int
    padding_bits: int
    total_bytes: int
    extra: dict

    def to_dict(self) -> dict:
        ratio = (self.original_bytes / self.total_bytes) if self.total_bytes else 0.0
        savings = (
            (1.0 - self.total_bytes / self.original_bytes) * 100.0
            if self.original_bytes
            else 0.0
        )
        out = {
            "algoritmo": self.algorithm,
            "original_bytes": self.original_bytes,
            "header_bytes": self.header_bytes,
            "metadata_bytes": self.metadata_bytes,
            "data_bytes": self.data_bytes,
            "padding_bits": self.padding_bits,
            "total_bytes": self.total_bytes,
            "compression_ratio": ratio,
            "savings_pct": savings,
        }
        out.update(self.extra)
        return out


class Compressor:
    """Interfaz mínima común para los algoritmos de compresión sin pérdida."""

    def compress(self, data: bytes) -> bytes:
        raise NotImplementedError

    def decompress(self, payload: bytes) -> bytes:
        raise NotImplementedError

    def stats(self) -> dict:
        """Retorna tamaño de encabezado, metadatos, datos y total."""
        raise NotImplementedError


def _ensure_bytes(value: object, name: str = "data") -> bytes:
    if not isinstance(value, bytes):
        raise TypeError(f"{name} debe ser exactamente de tipo bytes, no {type(value).__name__}")
    return value


def _pack_header(alg_id: int) -> bytes:
    return HEADER_STRUCT.pack(MAGIC, FORMAT_VERSION, alg_id)


def _unpack_header(payload: bytes, expected_alg: int | None = None) -> tuple[int, bytes]:
    _ensure_bytes(payload, "payload")
    if len(payload) < HEADER_STRUCT.size:
        raise ValueError("Flujo truncado: encabezado CMP9 incompleto")
    magic, version, alg_id = HEADER_STRUCT.unpack_from(payload, 0)
    if magic != MAGIC:
        raise ValueError(f"Identificador de formato inválido: {magic!r}")
    if version != FORMAT_VERSION:
        raise ValueError(f"Versión de formato no soportada: {version}")
    if alg_id not in ALG_NAMES:
        raise ValueError(f"Identificador de algoritmo desconocido: {alg_id}")
    if expected_alg is not None and alg_id != expected_alg:
        raise ValueError(
            f"Algoritmo en flujo ({ALG_NAMES[alg_id]}) no coincide con {ALG_NAMES[expected_alg]}"
        )
    return alg_id, payload[HEADER_STRUCT.size:]


def inspect_payload(payload: bytes) -> dict:
    """Inspecciona encabezado y metadatos de un flujo CMP9 sin descomprimir el cuerpo."""
    alg_id, body = _unpack_header(payload)
    alg_name = ALG_NAMES[alg_id]
    if alg_id == ALG_HUFFMAN:
        if len(body) < HUFF_META_STRUCT.size:
            raise ValueError("Metadatos Huffman incompletos")
        orig_size, pad_bits, sym_count = HUFF_META_STRUCT.unpack_from(body, 0)
        meta_size = HUFF_META_STRUCT.size + sym_count * HUFF_SYM_STRUCT.size
        if len(body) < meta_size:
            raise ValueError("Tabla de longitudes Huffman truncada")
        return {
            "version": FORMAT_VERSION,
            "alg_id": alg_id,
            "algoritmo": alg_name,
            "original_bytes": orig_size,
            "header_bytes": HEADER_STRUCT.size,
            "metadata_bytes": meta_size,
            "data_bytes": len(body) - meta_size,
            "padding_bits": pad_bits,
            "total_bytes": len(payload),
            "simbolos_distintos": sym_count,
        }
    if alg_id == ALG_RLE:
        if len(body) < RLE_META_STRUCT.size:
            raise ValueError("Metadatos RLE incompletos")
        orig_size, num_runs = RLE_META_STRUCT.unpack_from(body, 0)
        return {
            "version": FORMAT_VERSION,
            "alg_id": alg_id,
            "algoritmo": alg_name,
            "original_bytes": orig_size,
            "header_bytes": HEADER_STRUCT.size,
            "metadata_bytes": RLE_META_STRUCT.size,
            "data_bytes": len(body) - RLE_META_STRUCT.size,
            "padding_bits": 0,
            "total_bytes": len(payload),
            "corridas": num_runs,
        }
    if len(body) < LZ77_META_STRUCT.size:
        raise ValueError("Metadatos LZ77 incompletos")
    orig_size, win, min_m, max_m, tok_count = LZ77_META_STRUCT.unpack_from(body, 0)
    return {
        "version": FORMAT_VERSION,
        "alg_id": alg_id,
        "algoritmo": alg_name,
        "original_bytes": orig_size,
        "header_bytes": HEADER_STRUCT.size,
        "metadata_bytes": LZ77_META_STRUCT.size,
        "data_bytes": len(body) - LZ77_META_STRUCT.size,
        "padding_bits": 0,
        "total_bytes": len(payload),
        "window_size": win,
        "min_match": min_m,
        "max_match": max_m,
        "tokens": tok_count,
    }


# ---------------------------------------------------------------------------
# Entropía, Huffman y Huffman canónico
# ---------------------------------------------------------------------------


def frequencies(data: bytes) -> dict[int, int]:
    """Calcula frecuencias absolutas de cada byte (0..255) en ``data``."""
    _ensure_bytes(data, "data")
    return dict(Counter(data))


def entropy(freq: dict[int, int]) -> float:
    """Entropía de Shannon H(X) en bits/símbolo a partir de frecuencias."""
    if not isinstance(freq, dict):
        raise TypeError("freq debe ser dict[int, int]")
    if not freq:
        return 0.0
    total = 0
    for sym, count in freq.items():
        if type(sym) is not int or not 0 <= sym <= 255:
            raise ValueError(f"Símbolo fuera de rango byte (0..255): {sym!r}")
        if type(count) is not int or count < 0:
            raise ValueError(f"Frecuencia negativa o no entera para {sym}: {count!r}")
        total += count
    if total == 0:
        return 0.0
    h = 0.0
    for count in freq.values():
        if count > 0:
            p = count / total
            h -= p * math.log2(p)
    return max(0.0, h)


def average_code_length(freq: dict[int, int], lengths: dict[int, int]) -> float:
    """Calcula la longitud promedio L = sum(p_i * l_i) en bits por símbolo."""
    total = sum(v for v in freq.values() if v > 0)
    if total == 0:
        return 0.0
    return sum((count / total) * lengths[sym] for sym, count in freq.items() if count > 0)


def build_huffman_tree(freq: dict[int, int], *, trace: list[dict] | None = None) -> HuffmanNode | None:
    """Construye un árbol binario de Huffman usando cola de prioridad."""
    if not isinstance(freq, dict):
        raise TypeError("freq debe ser dict[int, int]")
    positive = [(sym, cnt) for sym, cnt in freq.items() if cnt > 0]
    for sym, cnt in freq.items():
        if type(sym) is not int or not 0 <= sym <= 255:
            raise ValueError(f"Símbolo inválido: {sym!r}")
        if type(cnt) is not int or cnt < 0:
            raise ValueError(f"Frecuencia inválida para {sym}: {cnt!r}")
    if not positive:
        return None

    serial = itertools.count()
    heap: list[tuple[int, int, HuffmanNode]] = []
    for sym, count in sorted(positive):
        heapq.heappush(heap, (count, next(serial), HuffmanNode(freq=count, symbol=sym)))

    if len(heap) == 1:
        count, _, only = heapq.heappop(heap)
        root = HuffmanNode(freq=count, left=only)
        if trace is not None:
            trace.append({
                "paso": 1,
                "izq_label": _node_label(only),
                "izq_freq": count,
                "der_label": "(único)",
                "der_freq": 0,
                "nuevo_freq": count,
                "decision": f"Símbolo único {only.symbol:#04x}: se envuelve en raíz con longitud 1",
                "cola_restante": [(count, _node_label(root))],
            })
        return root

    step = 0
    while len(heap) > 1:
        f1, _, left = heapq.heappop(heap)
        f2, _, right = heapq.heappop(heap)
        parent = HuffmanNode(freq=f1 + f2, left=left, right=right)
        heapq.heappush(heap, (parent.freq, next(serial), parent))
        step += 1
        if trace is not None:
            remaining = sorted((item[0], _node_label(item[2])) for item in heap)
            trace.append({
                "paso": step,
                "izq_label": _node_label(left),
                "izq_freq": f1,
                "der_label": _node_label(right),
                "der_freq": f2,
                "nuevo_freq": parent.freq,
                "decision": f"Combinar {_node_label(left)}({f1}) + {_node_label(right)}({f2}) -> {parent.freq}",
                "cola_restante": remaining,
            })

    return heap[0][2]


def _node_label(node: HuffmanNode) -> str:
    if node.symbol is not None:
        ch = chr(node.symbol)
        if 32 <= node.symbol <= 126:
            return f"'{ch}'"
        return f"0x{node.symbol:02X}"
    return f"[{node.freq}]"


def build_code_lengths(tree: HuffmanNode | None) -> dict[int, int]:
    """Extrae la longitud de código en bits para cada hoja del árbol de Huffman."""
    if tree is None:
        return {}
    lengths: dict[int, int] = {}

    def walk(node: HuffmanNode, depth: int) -> None:
        if node.symbol is not None:
            lengths[node.symbol] = max(1, depth)
            return
        if node.left is not None:
            walk(node.left, depth + 1)
        if node.right is not None:
            walk(node.right, depth + 1)

    walk(tree, 0)
    return dict(sorted(lengths.items()))


def validate_prefix_codes(codes: dict[int, str]) -> bool:
    """Comprueba que ningún código binario sea prefijo estricto de otro."""
    ordered = sorted(codes.values())
    for i in range(len(ordered) - 1):
        if ordered[i + 1].startswith(ordered[i]):
            return False
    return True


def canonical_codes(lengths: dict[int, int]) -> dict[int, str]:
    """Asigna códigos Huffman canónicos deterministas ordenando por (longitud, símbolo)."""
    if not isinstance(lengths, dict):
        raise TypeError("lengths debe ser dict[int, int]")
    if not lengths:
        return {}
    for sym, length in lengths.items():
        if type(sym) is not int or not 0 <= sym <= 255:
            raise ValueError(f"Símbolo inválido: {sym!r}")
        if type(length) is not int or length < 1 or length > 255:
            raise ValueError(f"Longitud de código inválida para {sym}: {length!r}")

    # Desigualdad de Kraft: sum(2^-l_i) <= 1 (en escala entera sum(2^(max_l - l_i)) <= 2^max_l)
    max_len = max(lengths.values())
    kraft_scaled = sum(1 << (max_len - length) for length in lengths.values())
    if kraft_scaled > (1 << max_len):
        raise ValueError("Las longitudes violan la desigualdad de Kraft (código no prefijo)")

    ordered = sorted(lengths.items(), key=lambda item: (item[1], item[0]))
    codes: dict[int, str] = {}
    code = 0
    prev_len = ordered[0][1]
    for symbol, length in ordered:
        code <<= length - prev_len
        codes[symbol] = format(code, f"0{length}b")
        code += 1
        prev_len = length
    return codes


def encode_bits(data: bytes, codes: dict[int, str]) -> str:
    """Codifica ``data`` como cadena de bits ('0'/'1') usando la tabla ``codes``."""
    _ensure_bytes(data, "data")
    if not data:
        return ""
    try:
        return "".join(codes[b] for b in data)
    except KeyError as exc:
        raise ValueError(f"Símbolo sin código asignado: {exc.args[0]}") from exc


def decode_bits(bits: str, codes: dict[int, str], original_size: int) -> bytes:
    """Decodifica una cadena de bits hasta recuperar exactamente ``original_size`` bytes."""
    if not isinstance(bits, str):
        raise TypeError("bits debe ser str de '0' y '1'")
    if type(original_size) is not int or original_size < 0:
        raise ValueError("original_size debe ser entero no negativo")
    if original_size == 0:
        return b""
    if not codes or not validate_prefix_codes(codes):
        raise ValueError("La tabla de códigos no satisface la propiedad prefijo")

    reverse = {code: sym for sym, code in codes.items()}
    out = bytearray()
    buf: list[str] = []
    for ch in bits:
        if ch not in ("0", "1"):
            raise ValueError(f"Bit inválido en cadena: {ch!r}")
        buf.append(ch)
        candidate = "".join(buf)
        sym = reverse.get(candidate)
        if sym is not None:
            out.append(sym)
            buf.clear()
            if len(out) == original_size:
                break
    if len(out) != original_size:
        raise ValueError("Flujo de bits insuficiente para reconstruir original_size bytes")
    return bytes(out)


def _pack_canonical_bitstream(data: bytes, codes: dict[int, str]) -> tuple[bytes, int]:
    """Empaqueta bits MSB-first en bytes reales sin construir cadenas enormes."""
    if not data:
        return b"", 0
    int_codes = {sym: (int(code, 2), len(code)) for sym, code in codes.items()}
    out = bytearray()
    acc = 0
    acc_bits = 0
    for byte in data:
        val, width = int_codes[byte]
        acc = (acc << width) | val
        acc_bits += width
        while acc_bits >= 8:
            shift = acc_bits - 8
            out.append((acc >> shift) & 0xFF)
            acc &= (1 << shift) - 1
            acc_bits = shift
    if acc_bits > 0:
        padding_bits = 8 - acc_bits
        out.append((acc << padding_bits) & 0xFF)
    else:
        padding_bits = 0
    return bytes(out), padding_bits


def _build_decode_tree(codes: dict[int, str]) -> HuffmanNode:
    root = HuffmanNode(freq=0)
    for sym, code in codes.items():
        node = root
        for bit in code:
            if bit == "0":
                if node.left is None:
                    node.left = HuffmanNode(freq=0)
                node = node.left
            else:
                if node.right is None:
                    node.right = HuffmanNode(freq=0)
                node = node.right
            if node.symbol is not None and bit != code[-1]:
                raise ValueError("Tabla de códigos viola la propiedad prefijo")
        if node.left is not None or node.right is not None or node.symbol is not None:
            raise ValueError("Tabla de códigos viola la propiedad prefijo")
        node.symbol = sym
    return root


class CanonicalHuffmanCompressor(Compressor):
    """Compresor Huffman canónico con contenedor binario CMP9."""

    def __init__(self) -> None:
        self._last_stats: CompressionStats | None = None

    def compress(self, data: bytes) -> bytes:
        _ensure_bytes(data, "data")
        header = _pack_header(ALG_HUFFMAN)
        original_size = len(data)
        if original_size == 0:
            meta = HUFF_META_STRUCT.pack(0, 0, 0)
            payload = header + meta
            self._last_stats = CompressionStats(
                algorithm=ALG_NAMES[ALG_HUFFMAN],
                original_bytes=0,
                header_bytes=len(header),
                metadata_bytes=len(meta),
                data_bytes=0,
                padding_bits=0,
                total_bytes=len(payload),
                extra={
                    "entropy_H": 0.0,
                    "avg_length_L": 0.0,
                    "efficiency_eta": 1.0,
                    "simbolos_distintos": 0,
                    "nodos_arbol": 0,
                },
            )
            return payload

        freq = frequencies(data)
        h_val = entropy(freq)
        tree = build_huffman_tree(freq)
        lengths = build_code_lengths(tree)
        codes = canonical_codes(lengths)
        l_val = average_code_length(freq, lengths)
        eta = (h_val / l_val) if l_val > 0 else 0.0

        ordered_lengths = sorted(lengths.items(), key=lambda x: (x[1], x[0]))
        meta_parts = [HUFF_META_STRUCT.pack(original_size, 0, len(ordered_lengths))]
        for sym, length in ordered_lengths:
            meta_parts.append(HUFF_SYM_STRUCT.pack(sym, length))
        coded_bytes, padding_bits = _pack_canonical_bitstream(data, codes)
        meta_parts[0] = HUFF_META_STRUCT.pack(original_size, padding_bits, len(ordered_lengths))
        meta = b"".join(meta_parts)
        payload = header + meta + coded_bytes

        nodos_arbol = (2 * len(ordered_lengths) - 1) if len(ordered_lengths) > 1 else 2
        self._last_stats = CompressionStats(
            algorithm=ALG_NAMES[ALG_HUFFMAN],
            original_bytes=original_size,
            header_bytes=len(header),
            metadata_bytes=len(meta),
            data_bytes=len(coded_bytes),
            padding_bits=padding_bits,
            total_bytes=len(payload),
            extra={
                "entropy_H": h_val,
                "avg_length_L": l_val,
                "efficiency_eta": eta,
                "simbolos_distintos": len(ordered_lengths),
                "nodos_arbol": nodos_arbol,
            },
        )
        return payload

    def decompress(self, payload: bytes) -> bytes:
        _, body = _unpack_header(payload, expected_alg=ALG_HUFFMAN)
        if len(body) < HUFF_META_STRUCT.size:
            raise ValueError("Metadatos Huffman truncados")
        original_size, padding_bits, sym_count = HUFF_META_STRUCT.unpack_from(body, 0)
        if padding_bits > 7:
            raise ValueError(f"Bits de relleno inválidos: {padding_bits}")
        if sym_count > 256:
            raise ValueError(f"Cantidad de símbolos imposible: {sym_count}")

        table_end = HUFF_META_STRUCT.size + sym_count * HUFF_SYM_STRUCT.size
        if len(body) < table_end:
            raise ValueError("Tabla canónica truncada")

        if original_size == 0:
            if sym_count != 0 or padding_bits != 0 or len(body) != table_end:
                raise ValueError("Encabezado Huffman inconsistente para entrada vacía")
            self._last_stats = CompressionStats(
                algorithm=ALG_NAMES[ALG_HUFFMAN],
                original_bytes=0,
                header_bytes=HEADER_STRUCT.size,
                metadata_bytes=table_end,
                data_bytes=0,
                padding_bits=0,
                total_bytes=len(payload),
                extra={"simbolos_distintos": 0},
            )
            return b""

        if sym_count == 0:
            raise ValueError("Entrada no vacía sin símbolos en tabla Huffman")

        lengths: dict[int, int] = {}
        pos = HUFF_META_STRUCT.size
        for _ in range(sym_count):
            sym, length = HUFF_SYM_STRUCT.unpack_from(body, pos)
            pos += HUFF_SYM_STRUCT.size
            if sym in lengths:
                raise ValueError(f"Símbolo duplicado en tabla canónica: {sym}")
            if length == 0:
                raise ValueError(f"Longitud nula inválida para símbolo {sym}")
            lengths[sym] = length

        if sym_count == 1 and next(iter(lengths.values())) != 1:
            raise ValueError("Para un único símbolo, la longitud canónica esperada es 1")
        if sym_count >= 2:
            max_l = max(lengths.values())
            if sum(1 << (max_l - l) for l in lengths.values()) != (1 << max_l):
                raise ValueError("Tabla Huffman incompleta o inconsistente (suma de Kraft != 1)")

        codes = canonical_codes(lengths)
        root = _build_decode_tree(codes)
        data_section = body[table_end:]
        if not data_section:
            raise ValueError("Datos codificados Huffman ausentes")
        if padding_bits > 0 and (data_section[-1] & ((1 << padding_bits) - 1)) != 0:
            raise ValueError("Bits de relleno no nulos en el último byte")

        total_valid_bits = len(data_section) * 8 - padding_bits
        out = bytearray()
        node = root
        consumed_bits = 0
        last_idx = len(data_section) - 1
        for byte_idx, byte in enumerate(data_section):
            limit = 8 - padding_bits if byte_idx == last_idx else 8
            for shift in range(7, 7 - limit, -1):
                bit = (byte >> shift) & 1
                node = node.right if bit else node.left
                consumed_bits += 1
                if node is None:
                    raise ValueError("Secuencia de bits inválida para la tabla canónica")
                if node.symbol is not None:
                    out.append(node.symbol)
                    node = root
                    if len(out) == original_size:
                        break
            if len(out) == original_size:
                if byte_idx != last_idx:
                    raise ValueError("Bytes sobrantes después de completar original_size")
                break

        if len(out) != original_size:
            raise ValueError("Flujo Huffman truncado antes de completar original_size")
        if consumed_bits != total_valid_bits:
            raise ValueError("Bits válidos inconsistentes con tamaño original y relleno")

        self._last_stats = CompressionStats(
            algorithm=ALG_NAMES[ALG_HUFFMAN],
            original_bytes=original_size,
            header_bytes=HEADER_STRUCT.size,
            metadata_bytes=table_end,
            data_bytes=len(data_section),
            padding_bits=padding_bits,
            total_bytes=len(payload),
            extra={"simbolos_distintos": sym_count},
        )
        return bytes(out)

    def stats(self) -> dict:
        if self._last_stats is None:
            raise RuntimeError("No se ha ejecutado compress() o decompress() aún")
        return self._last_stats.to_dict()


# ---------------------------------------------------------------------------
# RLE binario
# ---------------------------------------------------------------------------


class RLECompressor(Compressor):
    """Compresor Run-Length Encoding binario en pares (símbolo 1B, cantidad 2B)."""

    def __init__(self) -> None:
        self._last_stats: CompressionStats | None = None

    def compress(self, data: bytes) -> bytes:
        _ensure_bytes(data, "data")
        header = _pack_header(ALG_RLE)
        original_size = len(data)
        if original_size == 0:
            meta = RLE_META_STRUCT.pack(0, 0)
            payload = header + meta
            self._last_stats = CompressionStats(
                algorithm=ALG_NAMES[ALG_RLE],
                original_bytes=0,
                header_bytes=len(header),
                metadata_bytes=len(meta),
                data_bytes=0,
                padding_bits=0,
                total_bytes=len(payload),
                extra={"corridas": 0},
            )
            return payload

        runs = bytearray()
        num_runs = 0
        symbol = data[0]
        count = 1
        for current in data[1:]:
            if current == symbol and count < MAX_RLE_RUN:
                count += 1
            else:
                runs.extend(RLE_RUN_STRUCT.pack(symbol, count))
                num_runs += 1
                symbol = current
                count = 1
        runs.extend(RLE_RUN_STRUCT.pack(symbol, count))
        num_runs += 1

        meta = RLE_META_STRUCT.pack(original_size, num_runs)
        payload = header + meta + bytes(runs)
        self._last_stats = CompressionStats(
            algorithm=ALG_NAMES[ALG_RLE],
            original_bytes=original_size,
            header_bytes=len(header),
            metadata_bytes=len(meta),
            data_bytes=len(runs),
            padding_bits=0,
            total_bytes=len(payload),
            extra={"corridas": num_runs},
        )
        return payload

    def decompress(self, payload: bytes) -> bytes:
        _, body = _unpack_header(payload, expected_alg=ALG_RLE)
        if len(body) < RLE_META_STRUCT.size:
            raise ValueError("Metadatos RLE truncados")
        original_size, num_runs = RLE_META_STRUCT.unpack_from(body, 0)
        data_section = body[RLE_META_STRUCT.size:]
        if len(data_section) != num_runs * RLE_RUN_STRUCT.size:
            raise ValueError("Cuerpo RLE truncado o inconsistente con el número de corridas")

        out = bytearray()
        for pos in range(0, len(data_section), RLE_RUN_STRUCT.size):
            symbol, count = RLE_RUN_STRUCT.unpack_from(data_section, pos)
            if count == 0:
                raise ValueError("Corrida RLE inválida con longitud 0")
            out.extend(bytes([symbol]) * count)
            if len(out) > original_size:
                raise ValueError("Corridas RLE exceden el tamaño original declarado")

        if len(out) != original_size:
            raise ValueError("Tamaño reconstruido RLE inconsistente con el encabezado")

        self._last_stats = CompressionStats(
            algorithm=ALG_NAMES[ALG_RLE],
            original_bytes=original_size,
            header_bytes=HEADER_STRUCT.size,
            metadata_bytes=RLE_META_STRUCT.size,
            data_bytes=len(data_section),
            padding_bits=0,
            total_bytes=len(payload),
            extra={"corridas": num_runs},
        )
        return bytes(out)

    def stats(self) -> dict:
        if self._last_stats is None:
            raise RuntimeError("No se ha ejecutado compress() o decompress() aún")
        return self._last_stats.to_dict()


def rle_encode(data: bytes) -> bytes:
    """Codifica ``data`` usando RLE binario con formato CMP9."""
    return RLECompressor().compress(data)


def rle_decode(payload: bytes) -> bytes:
    """Decodifica un flujo RLE binario en formato CMP9."""
    return RLECompressor().decompress(payload)


# ---------------------------------------------------------------------------
# LZ77 con ventana deslizante
# ---------------------------------------------------------------------------


def _find_longest_match(
    data: bytes,
    pos: int,
    window_size: int,
    min_match: int,
    max_match: int,
    index_table: dict[bytes, deque[int]],
) -> tuple[int, int]:
    """Busca la coincidencia más larga en la ventana; ante empate elige menor offset."""
    n = len(data)
    remaining = n - pos
    if remaining < min_match:
        return 0, 0
    limit = min(max_match, remaining)
    win_start = max(0, pos - window_size)

    prefix = data[pos:pos + min_match]
    candidates = index_table.get(prefix)
    if not candidates:
        return 0, 0

    best_len = 0
    best_offset = 0
    # Se recorre desde el candidato más reciente (menor offset) hacia atrás;
    # como solo actualizamos con `length > best_len`, los empates conservan menor offset.
    for cand_pos in reversed(candidates):
        if cand_pos < win_start:
            break
        length = min_match
        while length < limit and data[cand_pos + length] == data[pos + length]:
            length += 1
        if length > best_len:
            best_len = length
            best_offset = pos - cand_pos
            if best_len == limit:
                break
    return best_offset, best_len


def lz77_tokenize(
    data: bytes,
    window_size: int = DEFAULT_LZ77_WINDOW,
    min_match: int = DEFAULT_LZ77_MIN_MATCH,
    max_match: int = DEFAULT_LZ77_MAX_MATCH,
    *,
    trace: bool = False,
) -> tuple[list[tuple], list[dict]]:
    """Genera lista de tokens ('L', byte) o ('M', offset, length) y traza opcional."""
    _ensure_bytes(data, "data")
    if not 1 <= window_size <= 4096:
        raise ValueError("window_size debe estar en [1, 4096]")
    if min_match < 1 or max_match < min_match or (max_match - min_match) > 15:
        raise ValueError("max_match debe satisfacer min_match <= max_match <= min_match + 15")

    tokens: list[tuple] = []
    steps: list[dict] = []
    index_table: dict[bytes, deque[int]] = defaultdict(lambda: deque(maxlen=64))
    n = len(data)
    pos = 0
    step_num = 0

    def record_index(position: int) -> None:
        if position + min_match <= n:
            index_table[data[position:position + min_match]].append(position)

    while pos < n:
        win_before = data[max(0, pos - window_size):pos]
        look_before = data[pos:min(n, pos + max_match)]
        offset, length = _find_longest_match(
            data, pos, window_size, min_match, max_match, index_table
        )
        step_num += 1
        if length >= min_match:
            token = ("M", offset, length)
            tokens.append(token)
            for k in range(length):
                record_index(pos + k)
            pos_after = pos + length
            decision = f"COINCIDENCIA (offset={offset}, len={length}): {data[pos:pos_after]!r}"
        else:
            byte_val = data[pos]
            token = ("L", byte_val)
            tokens.append(token)
            record_index(pos)
            pos_after = pos + 1
            decision = f"LITERAL (0x{byte_val:02X} = {bytes([byte_val])!r})"

        if trace:
            steps.append({
                "paso": step_num,
                "pos_antes": pos,
                "ventana_antes": win_before,
                "prelectura_antes": look_before,
                "token": token,
                "decision": decision,
                "pos_despues": pos_after,
                "ventana_despues": data[max(0, pos_after - window_size):pos_after],
                "prelectura_despues": data[pos_after:min(n, pos_after + max_match)],
            })
        pos = pos_after

    return tokens, steps


class LZ77Compressor(Compressor):
    """Compresor LZ77 con grupos de 8 banderas y referencias de 16 bits."""

    def __init__(
        self,
        window_size: int = DEFAULT_LZ77_WINDOW,
        min_match: int = DEFAULT_LZ77_MIN_MATCH,
        max_match: int = DEFAULT_LZ77_MAX_MATCH,
    ) -> None:
        if type(window_size) is not int or not 1 <= window_size <= 4096:
            raise ValueError("window_size debe ser entero en [1, 4096]")
        if type(min_match) is not int or type(max_match) is not int:
            raise TypeError("min_match y max_match deben ser enteros")
        if min_match < 1 or max_match < min_match or (max_match - min_match) > 15:
            raise ValueError("Debe cumplirse 1 <= min_match <= max_match <= min_match + 15")
        self.window_size = window_size
        self.min_match = min_match
        self.max_match = max_match
        self._last_stats: CompressionStats | None = None

    def compress(self, data: bytes) -> bytes:
        _ensure_bytes(data, "data")
        header = _pack_header(ALG_LZ77)
        tokens, _ = lz77_tokenize(data, self.window_size, self.min_match, self.max_match)
        meta = LZ77_META_STRUCT.pack(
            len(data), self.window_size, self.min_match, self.max_match, len(tokens)
        )

        body = bytearray()
        literals = 0
        matches = 0
        for group_start in range(0, len(tokens), 8):
            chunk = tokens[group_start:group_start + 8]
            flags = 0
            chunk_bytes = bytearray()
            for bit_idx, token in enumerate(chunk):
                if token[0] == "L":
                    literals += 1
                    chunk_bytes.append(token[1])
                else:
                    matches += 1
                    flags |= 1 << bit_idx
                    _, offset, length = token
                    packed = ((offset - 1) << 4) | (length - self.min_match)
                    chunk_bytes.extend(LZ77_MATCH_STRUCT.pack(packed))
            body.append(flags)
            body.extend(chunk_bytes)

        payload = header + meta + bytes(body)
        self._last_stats = CompressionStats(
            algorithm=ALG_NAMES[ALG_LZ77],
            original_bytes=len(data),
            header_bytes=len(header),
            metadata_bytes=len(meta),
            data_bytes=len(body),
            padding_bits=0,
            total_bytes=len(payload),
            extra={
                "window_size": self.window_size,
                "tokens": len(tokens),
                "literales": literals,
                "coincidencias": matches,
            },
        )
        return payload

    def decompress(self, payload: bytes) -> bytes:
        _, body = _unpack_header(payload, expected_alg=ALG_LZ77)
        if len(body) < LZ77_META_STRUCT.size:
            raise ValueError("Metadatos LZ77 truncados")
        original_size, window_size, min_match, max_match, token_count = (
            LZ77_META_STRUCT.unpack_from(body, 0)
        )
        if not 1 <= window_size <= 4096 or min_match < 1 or max_match < min_match or (max_match - min_match) > 15:
            raise ValueError("Parámetros LZ77 inválidos en encabezado")

        data_section = body[LZ77_META_STRUCT.size:]
        if token_count == 0:
            if original_size != 0 or data_section:
                raise ValueError("Flujo LZ77 inconsistente para entrada vacía")
            self._last_stats = CompressionStats(
                algorithm=ALG_NAMES[ALG_LZ77],
                original_bytes=0,
                header_bytes=HEADER_STRUCT.size,
                metadata_bytes=LZ77_META_STRUCT.size,
                data_bytes=0,
                padding_bits=0,
                total_bytes=len(payload),
                extra={"window_size": window_size, "tokens": 0},
            )
            return b""

        out = bytearray()
        pos = 0
        decoded_tokens = 0
        literals = 0
        matches = 0
        while decoded_tokens < token_count:
            if pos >= len(data_section):
                raise ValueError("Flujo LZ77 truncado antes de leer byte de banderas")
            flags = data_section[pos]
            pos += 1
            group_size = min(8, token_count - decoded_tokens)
            if group_size < 8 and (flags >> group_size) != 0:
                raise ValueError("Banderas no nulas en relleno de grupo LZ77")
            for bit_idx in range(group_size):
                if (flags >> bit_idx) & 1:
                    if pos + LZ77_MATCH_STRUCT.size > len(data_section):
                        raise ValueError("Token de coincidencia LZ77 truncado")
                    (packed,) = LZ77_MATCH_STRUCT.unpack_from(data_section, pos)
                    pos += LZ77_MATCH_STRUCT.size
                    offset = (packed >> 4) + 1
                    length = (packed & 0x0F) + min_match
                    if offset > window_size or offset > len(out):
                        raise ValueError(f"Offset LZ77 fuera de ventana: {offset}")
                    if length > max_match or len(out) + length > original_size:
                        raise ValueError("Longitud de coincidencia LZ77 inconsistente")
                    for _ in range(length):
                        out.append(out[-offset])
                    matches += 1
                else:
                    if pos >= len(data_section):
                        raise ValueError("Token literal LZ77 truncado")
                    out.append(data_section[pos])
                    pos += 1
                    literals += 1
                decoded_tokens += 1

        if pos != len(data_section):
            raise ValueError("Bytes sobrantes al final del flujo LZ77")
        if len(out) != original_size:
            raise ValueError("Tamaño reconstruido LZ77 inconsistente con el encabezado")

        self._last_stats = CompressionStats(
            algorithm=ALG_NAMES[ALG_LZ77],
            original_bytes=original_size,
            header_bytes=HEADER_STRUCT.size,
            metadata_bytes=LZ77_META_STRUCT.size,
            data_bytes=len(data_section),
            padding_bits=0,
            total_bytes=len(payload),
            extra={
                "window_size": window_size,
                "tokens": token_count,
                "literales": literals,
                "coincidencias": matches,
            },
        )
        return bytes(out)

    def stats(self) -> dict:
        if self._last_stats is None:
            raise RuntimeError("No se ha ejecutado compress() o decompress() aún")
        return self._last_stats.to_dict()


def lz77_encode(
    data: bytes,
    window_size: int = DEFAULT_LZ77_WINDOW,
    min_match: int = DEFAULT_LZ77_MIN_MATCH,
    max_match: int = DEFAULT_LZ77_MAX_MATCH,
) -> bytes:
    """Codifica ``data`` usando LZ77 en formato CMP9."""
    return LZ77Compressor(window_size, min_match, max_match).compress(data)


def lz77_decode(payload: bytes) -> bytes:
    """Decodifica un flujo LZ77 en formato CMP9."""
    return LZ77Compressor().decompress(payload)


def get_compressor(name: str, **kwargs) -> Compressor:
    """Fábrica de compresores por nombre ('huffman', 'rle', 'lz77')."""
    normalized = name.strip().lower()
    if normalized in ("huffman", "huffman_canonico", "canonical_huffman"):
        return CanonicalHuffmanCompressor()
    if normalized == "rle":
        return RLECompressor()
    if normalized == "lz77":
        return LZ77Compressor(**kwargs)
    raise ValueError(f"Algoritmo no soportado: {name!r}")
