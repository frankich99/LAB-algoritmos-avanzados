"""Visualización didáctica obligatoria paso a paso para Huffman canónico y LZ77."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from compression import (
    HuffmanNode,
    average_code_length,
    build_code_lengths,
    build_huffman_tree,
    canonical_codes,
    entropy,
    frequencies,
    lz77_tokenize,
)

FIGURES_DIR = Path(__file__).resolve().parent / "figures"


def _fmt_sym(sym: int) -> str:
    if 32 <= sym <= 126:
        return chr(sym)
    return f"0x{sym:02X}"


def _make_tree_codes(node: HuffmanNode | None, prefix: str = "", out: dict[int, str] | None = None) -> dict[int, str]:
    if out is None:
        out = {}
    if node is None:
        return out
    if node.symbol is not None:
        out[node.symbol] = prefix or "0"
        return out
    if node.left is not None:
        _make_tree_codes(node.left, prefix + "0", out)
    if node.right is not None:
        _make_tree_codes(node.right, prefix + "1", out)
    return out


def _assign_positions(root: HuffmanNode) -> dict[int, tuple[float, float]]:
    positions: dict[int, tuple[float, float]] = {}
    counter = [0]

    def dfs(node: HuffmanNode, depth: int) -> float:
        if node.symbol is not None:
            x = float(counter[0])
            counter[0] += 1
            positions[id(node)] = (x, float(-depth))
            return x
        xs = []
        if node.left is not None:
            xs.append(dfs(node.left, depth + 1))
        if node.right is not None:
            xs.append(dfs(node.right, depth + 1))
        x = sum(xs) / len(xs)
        positions[id(node)] = (x, float(-depth))
        return x

    dfs(root, 0)
    return positions


def plot_huffman_didactic(
    sample: bytes = b"ABRACADABRA",
    output_path: Path | None = None,
) -> Path:
    """Genera diagrama amplio de Huffman: combinaciones, árbol final y tabla canónica."""
    if output_path is None:
        output_path = FIGURES_DIR / "fig_didactica_huffman.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    freq = frequencies(sample)
    trace: list[dict] = []
    tree = build_huffman_tree(freq, trace=trace)
    assert tree is not None
    lengths = build_code_lengths(tree)
    tree_codes = _make_tree_codes(tree)
    canon = canonical_codes(lengths)
    h_val = entropy(freq)
    l_val = average_code_length(freq, lengths)

    fig = plt.figure(figsize=(16.5, 8.0))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.22, 1.18, 1.05], wspace=0.12)

    # Panel 1: Combinaciones sucesivas
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.axis("off")
    ax1.set_title("1. Combinaciones sucesivas (cola de prioridad)", fontsize=13, fontweight="bold", pad=12)
    ax1.text(
        0.01, 0.96,
        f"Entrada: {sample.decode('ascii', errors='replace')!r} (n = {len(sample)} B)\n"
        + "Frecuencias: "
        + ", ".join(f"{_fmt_sym(s)}:{c}" for s, c in sorted(freq.items())),
        transform=ax1.transAxes,
        va="top",
        fontsize=10.5,
        bbox=dict(boxstyle="round,pad=0.45", facecolor="#eef4fb", edgecolor="#5b8cc7", linewidth=1.3),
    )

    y_pos = 0.78
    step_gap = 0.185
    for item in trace:
        queue_txt = ", ".join(
            lbl if lbl.startswith("[") else f"{lbl}({f})"
            for f, lbl in item["cola_restante"]
        )
        text = (
            f"Paso {item['paso']}: {item['decision']}\n"
            f"Cola tras insertar: [{queue_txt}]"
        )
        ax1.text(
            0.01,
            y_pos,
            text,
            transform=ax1.transAxes,
            va="top",
            fontsize=10.2,
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#f8f9fa", edgecolor="#94a3b8", linewidth=1.1),
        )
        y_pos -= step_gap

    # Panel 2: Árbol final
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.axis("off")
    ax2.set_title("2. Árbol binario de Huffman final", fontsize=13, fontweight="bold", pad=12)
    pos = _assign_positions(tree)

    def draw_edges(node: HuffmanNode) -> None:
        x0, y0 = pos[id(node)]
        for child, bit, dx_off in ((node.left, "0", -0.15), (node.right, "1", 0.15)):
            if child is not None:
                x1, y1 = pos[id(child)]
                ax2.plot([x0, x1], [y0, y1], color="#475569", linewidth=2.2, zorder=1)
                ax2.text(
                    (x0 + x1) / 2 + dx_off,
                    (y0 + y1) / 2 + 0.06,
                    bit,
                    fontsize=12,
                    fontweight="bold",
                    color="#0b5394" if bit == "0" else "#b45309",
                    ha="center",
                    va="center",
                )
                draw_edges(child)

    def draw_nodes(node: HuffmanNode) -> None:
        x, y = pos[id(node)]
        is_leaf = node.symbol is not None
        label = f"{_fmt_sym(node.symbol)}\n({node.freq})" if is_leaf else f"{node.freq}"
        ax2.scatter(
            [x], [y],
            s=1450 if is_leaf else 980,
            color="#d1e7dd" if is_leaf else "#cfe2ff",
            edgecolors="#146c43" if is_leaf else "#084298",
            linewidths=2.1,
            zorder=3,
        )
        ax2.text(x, y, label, ha="center", va="center", fontsize=10.8, fontweight="bold", zorder=4)
        if node.left is not None:
            draw_nodes(node.left)
        if node.right is not None:
            draw_nodes(node.right)

    draw_edges(tree)
    draw_nodes(tree)
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    ax2.set_xlim(min(xs) - 0.55, max(xs) + 0.55)
    ax2.set_ylim(min(ys) - 0.45, max(ys) + 0.42)

    # Panel 3: Tabla canónica
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.axis("off")
    ax3.set_title("3. Tabla Huffman canónica", fontsize=13, fontweight="bold", pad=12)

    rows = []
    ordered = sorted(lengths.items(), key=lambda item: (item[1], item[0]))
    for sym, length in ordered:
        rows.append([
            f"{_fmt_sym(sym)} (0x{sym:02X})",
            str(freq[sym]),
            str(length),
            tree_codes[sym],
            canon[sym],
        ])

    table = ax3.table(
        cellText=rows,
        colLabels=["Símbolo", "Freq", "l_i", "Árbol", "Canónico"],
        colWidths=[0.24, 0.14, 0.11, 0.22, 0.29],
        cellLoc="center",
        loc="upper center",
        bbox=[0.0, 0.30, 1.0, 0.64],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10.0)
    for (r, _c), cell in table.get_celld().items():
        if r == 0:
            cell.set_facecolor("#1f4e78")
            cell.set_text_props(color="white", fontweight="bold")
        elif r % 2 == 1:
            cell.set_facecolor("#f8fafc")

    ax3.text(
        0.02, 0.22,
        f"Entropía H(X) = {h_val:.4f} bits/símbolo\n"
        f"Longitud media L = {l_val:.4f} bits/símbolo\n"
        f"Eficiencia H/L = {(h_val / l_val) * 100:.2f}%\n"
        "Orden canónico: (longitud, valor byte).",
        transform=ax3.transAxes,
        va="top",
        fontsize=10.8,
        bbox=dict(boxstyle="round,pad=0.45", facecolor="#fff7ed", edgecolor="#d97706", linewidth=1.3),
    )

    fig.suptitle(
        "Visualización didáctica de Huffman canónico (Guía 09 — Grupo 5, UNSAAC)",
        fontsize=15,
        fontweight="bold",
        y=0.98,
    )
    fig.savefig(output_path, dpi=300, bbox_inches="tight", pad_inches=0.14)
    plt.close(fig)
    return output_path


def plot_lz77_didactic(
    sample: bytes = b"ABABABCABABA",
    window_size: int = 12,
    min_match: int = 3,
    max_match: int = 18,
    output_path: Path | None = None,
) -> Path:
    """Genera diagrama amplio paso a paso de LZ77 sin márgenes desperdiciados."""
    if output_path is None:
        output_path = FIGURES_DIR / "fig_didactica_lz77.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    tokens, steps = lz77_tokenize(
        sample, window_size=window_size, min_match=min_match, max_match=max_match, trace=True
    )
    text_str = sample.decode("ascii", errors="replace")
    n = len(sample)

    fig, ax = plt.subplots(figsize=(17.5, 9.2))
    ax.axis("off")

    row_h = 1.46
    total_h = len(steps) * row_h + 1.02
    ax.set_xlim(0, 19.6)
    ax.set_ylim(-0.32, total_h)

    ax.text(
        0.15,
        total_h - 0.32,
        f"Entrada: {text_str!r} ({n} bytes)  |  Parámetros: ventana={window_size}, "
        f"min_match={min_match}, max_match={max_match}  |  Tokens emitidos: {len(tokens)}",
        fontsize=12.0,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.38", facecolor="#eef4fb", edgecolor="#3b82f6", linewidth=1.3),
    )

    def draw_strip(x0: float, y0: float, cursor: int, highlight_end: int | None = None, label: str = "") -> None:
        ax.text(x0, y0 + 0.50, label, fontsize=10.2, fontweight="bold", color="#1e293b")
        win_start = max(0, cursor - window_size)
        box_w = 0.72
        for idx, ch in enumerate(text_str):
            if idx < win_start:
                fc, ec = "#f1f5f9", "#cbd5e1"
            elif idx < cursor:
                fc, ec = "#dbeafe", "#2563eb"
            elif highlight_end is not None and cursor <= idx < highlight_end:
                fc, ec = "#fde68a", "#d97706"
            else:
                fc, ec = "#dcfce7", "#16a34a"
            rect = FancyBboxPatch(
                (x0 + idx * box_w, y0),
                box_w - 0.06,
                0.42,
                boxstyle="round,pad=0.02",
                facecolor=fc,
                edgecolor=ec,
                linewidth=1.2,
            )
            ax.add_patch(rect)
            ax.text(
                x0 + idx * box_w + (box_w - 0.06) / 2,
                y0 + 0.21,
                ch,
                ha="center",
                va="center",
                fontsize=10.5,
                fontweight="bold",
            )
        sep_x = x0 + cursor * box_w - 0.03
        ax.plot([sep_x, sep_x], [y0 - 0.05, y0 + 0.47], color="#dc2626", linewidth=2.4)

    for i, st in enumerate(steps):
        y_base = total_h - 1.32 - i * row_h
        is_match = st["token"][0] == "M"
        badge_fc = "#fef3c7" if is_match else "#f1f5f9"
        badge_ec = "#d97706" if is_match else "#64748b"

        ax.text(
            0.15,
            y_base + 0.72,
            f"Paso {st['paso']}  |  {st['decision']}",
            fontsize=11.0,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.25", facecolor=badge_fc, edgecolor=badge_ec, linewidth=1.2),
        )
        draw_strip(
            0.15,
            y_base - 0.06,
            st["pos_antes"],
            highlight_end=st["pos_despues"],
            label=f"Antes (pos={st['pos_antes']}): ventana='{st['ventana_antes'].decode('ascii')}' | prelectura='{st['prelectura_antes'].decode('ascii')}'",
        )
        draw_strip(
            10.2,
            y_base - 0.06,
            st["pos_despues"],
            highlight_end=None,
            label=f"Después (pos={st['pos_despues']}): ventana='{st['ventana_despues'].decode('ascii')}' | restante='{st['prelectura_despues'].decode('ascii')}'",
        )

    ax.text(
        0.15,
        -0.22,
        "Colores: Azul = ventana de búsqueda  |  Amarillo = bytes consumidos en el paso  |  "
        "Verde = búfer de prelectura restante  |  Línea roja = cursor",
        fontsize=10.5,
        color="#334155",
    )

    fig.suptitle(
        "Visualización didáctica paso a paso de LZ77 (Guía 09 — Grupo 5, UNSAAC)",
        fontsize=14.8,
        fontweight="bold",
        y=0.99,
    )
    fig.savefig(output_path, dpi=300, bbox_inches="tight", pad_inches=0.14)
    plt.close(fig)
    return output_path


def main() -> None:
    p1 = plot_huffman_didactic()
    p2 = plot_lz77_didactic()
    print(f"Visualizaciones guardadas: {p1.name}, {p2.name}")


if __name__ == "__main__":
    main()
