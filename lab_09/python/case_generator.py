"""Generador reproducible de casos de prueba y conjunto mínimo de datos (Guía 09)."""

from __future__ import annotations

from pathlib import Path
from random import Random
import struct
import zlib

SEED_UNIFORM = 20260901
SEED_RANDOM = 20260902
SEED_PNG = 20260903

DATASETS_DIR = Path(__file__).resolve().parent / "datasets"

_SPANISH_PARAGRAPHS = (
    "La compresión sin pérdida permite representar exactamente una secuencia de bytes "
    "mediante un flujo más compacto, garantizando que la descompresión recupere bit a bit "
    "la entrada original sin degradación alguna. Desde el teorema de codificación de fuentes "
    "de Shannon, la entropía H(X) fija un límite inferior teórico para la longitud promedio "
    "de cualquier código prefijo asignado símbolo a símbolo.\n\n"
    "En la práctica computacional de la Universidad Nacional de San Antonio Abad del Cusco, "
    "el análisis experimental demuestra que un algoritmo no puede evaluarse únicamente por su "
    "tasa teórica sobre flujos ideales. El archivo comprimido real incorpora encabezados de "
    "versión, tamaños originales, tablas de longitudes canónicas o parámetros de ventana, y "
    "bits de relleno al final del último byte.\n\n"
    "Mientras Huffman canónico explota las desigualdades de frecuencia estadística entre los "
    "símbolos presentes y RLE condensa corridas largas de un mismo octeto, los métodos de la "
    "familia Lempel-Ziv como LZ77 aprovechan la redundancia local mediante referencias hacia "
    "atrás en una ventana deslizante. En textos naturales en español, palabras frecuentes, "
    "artículos, preposiciones y terminaciones verbales aparecen repetidas a corta distancia, "
    "ofreciendo oportunidades directas para referencias de longitud y desplazamiento.\n\n"
)


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)


def make_synthetic_png(width: int = 128, height: int = 96, seed: int = SEED_PNG) -> bytes:
    """Construye un archivo PNG válido comprimido con zlib (licencia propia CC0)."""
    rng = Random(seed)
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filtro tipo None
        for x in range(width):
            r = (x * 2 + rng.randrange(0, 64)) & 0xFF
            g = (y * 3 + rng.randrange(0, 64)) & 0xFF
            b = ((x ^ y) + rng.randrange(0, 128)) & 0xFF
            raw.extend((r, g, b))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    idat = zlib.compress(bytes(raw), level=9)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", idat)
        + _png_chunk(b"IEND", b"")
    )


def build_benchmark_corpus() -> list[dict]:
    """Construye en memoria los 9 archivos del conjunto mínimo de la Guía 09."""
    # 1-3: vacío, un byte y pocos bytes
    vacio = b""
    un_byte = b"Z"
    pocos_bytes = b"UNSAAC-2026-L09!"

    # 4: un único símbolo repetido (32 KiB)
    unico_simbolo = b"A" * 32768

    # 5: texto natural en español (~36 KiB)
    texto_base = _SPANISH_PARAGRAPHS.encode("utf-8")
    repeats = (36000 // len(texto_base)) + 1
    texto_espanol = (texto_base * repeats)[:36000]

    # 6: archivo con patrones repetitivos estructurados (~32 KiB)
    patron_bloque = bytearray()
    for idx in range(64):
        linea = (
            f"REGISTRO|ESTACION=CUSCO-{(idx % 4) + 1:02d}|"
            f"METRICA=COMPRESION|ESTADO=OK|BLOQUE={(idx % 8):02d};\n"
        ).encode("ascii")
        patron_bloque.extend(linea)
    patrones_repetitivos = (bytes(patron_bloque) * 10)[:32768]

    # 7: distribución exactamente uniforme sobre los 256 valores de byte (32 KiB)
    rng_u = Random(SEED_UNIFORM)
    buf_u = bytearray(list(range(256)) * 128)
    rng_u.shuffle(buf_u)
    uniforme_256 = bytes(buf_u)

    # 8: bytes pseudoaleatorios reproducibles (32 KiB)
    aleatorio = Random(SEED_RANDOM).randbytes(32768)

    # 9: archivo ya comprimido (PNG válido generado con zlib)
    imagen_png = make_synthetic_png()

    return [
        {
            "id": "01_vacio",
            "archivo": "01_vacio.bin",
            "categoria": "vacio",
            "descripcion": "Archivo vacío de 0 bytes",
            "procedencia": "Generación sintética determinista (Grupo 5, CC0)",
            "data": vacio,
        },
        {
            "id": "02_un_byte",
            "archivo": "02_un_byte.bin",
            "categoria": "un_byte",
            "descripcion": "Archivo de 1 byte (0x5A)",
            "procedencia": "Generación sintética determinista (Grupo 5, CC0)",
            "data": un_byte,
        },
        {
            "id": "03_pocos_bytes",
            "archivo": "03_pocos_bytes.bin",
            "categoria": "pocos_bytes",
            "descripcion": "Entrada corta de 16 bytes (sobrecarga de metadatos)",
            "procedencia": "Generación sintética determinista (Grupo 5, CC0)",
            "data": pocos_bytes,
        },
        {
            "id": "04_unico_simbolo",
            "archivo": "04_unico_simbolo.bin",
            "categoria": "unico_simbolo",
            "descripcion": "Único símbolo 0x41 repetido 32 768 veces",
            "procedencia": "Generación sintética determinista (Grupo 5, CC0)",
            "data": unico_simbolo,
        },
        {
            "id": "05_texto_espanol",
            "archivo": "05_texto_espanol.txt",
            "categoria": "texto_espanol",
            "descripcion": "Texto natural académico en español UTF-8 (36 000 bytes)",
            "procedencia": "Redacción propia del Grupo 5 sobre teoría de compresión (CC0)",
            "data": texto_espanol,
        },
        {
            "id": "06_patrones_repetitivos",
            "archivo": "06_patrones_repetitivos.bin",
            "categoria": "patrones_repetitivos",
            "descripcion": "Registros estructurados con subcadenas repetitivas (32 768 bytes)",
            "procedencia": "Generación sintética determinista (Grupo 5, CC0)",
            "data": patrones_repetitivos,
        },
        {
            "id": "07_uniforme_256",
            "archivo": "07_uniforme_256.bin",
            "categoria": "uniforme",
            "descripcion": "Distribución uniforme de 256 valores (128 copias c/u, semilla 20260901)",
            "procedencia": "Generación sintética determinista (Grupo 5, CC0)",
            "data": uniforme_256,
        },
        {
            "id": "08_aleatorio",
            "archivo": "08_aleatorio.bin",
            "categoria": "aleatorio",
            "descripcion": "Bytes pseudoaleatorios reproducibles (semilla 20260902, 32 768 bytes)",
            "procedencia": "Random(20260902).randbytes(32768) (Grupo 5, CC0)",
            "data": aleatorio,
        },
        {
            "id": "09_imagen_comprimida",
            "archivo": "09_imagen_comprimida.png",
            "categoria": "ya_comprimido",
            "descripcion": "Imagen PNG RGB 128x96 comprimida internamente con zlib nivel 9",
            "procedencia": "PNG sintético determinista con zlib/DEFLATE (semilla 20260903, CC0)",
            "data": imagen_png,
        },
    ]


def materialize_corpus(dest: Path = DATASETS_DIR) -> list[dict]:
    """Escribe los archivos del corpus y su registro de licencias/procedencia en disco."""
    dest.mkdir(parents=True, exist_ok=True)
    corpus = build_benchmark_corpus()
    lines = [
        "# Procedencia y Licencias del Conjunto de Datos de Prueba (Guía 09)",
        "",
        "Todos los archivos son generados de forma determinista y reproducible por el Grupo 5 "
        "(UNSAAC, 2026-II) bajo licencia abierta **CC0 1.0 (Dominio Público)**, sin dependencias "
        "de material propietario externo.",
        "",
        "| Archivo | Categoría | Tamaño (bytes) | Procedencia |",
        "| :--- | :--- | :---: | :--- |",
    ]
    for item in corpus:
        file_path = dest / item["archivo"]
        file_path.write_bytes(item["data"])
        lines.append(
            f"| `{item['archivo']}` | `{item['categoria']}` | "
            f"{len(item['data'])} | {item['procedencia']} |"
        )
    (dest / "PROCEDENCIA_Y_LICENCIAS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return corpus


if __name__ == "__main__":
    items = materialize_corpus()
    for item in items:
        print(f"Generado {item['archivo']} ({len(item['data'])} bytes)")
