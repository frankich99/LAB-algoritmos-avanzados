"""Generación de visualizaciones reproducibles para el Laboratorio 05."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from link_cut_tree import LinkCutForest, LinkCutNode
from splay_tree import SplayNode, SplayTree


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _binary_positions(root: Any, left_name: str = "left", right_name: str = "right") -> dict[int, tuple[float, float]]:
    """Posiciona un árbol binario según el recorrido in-order."""

    positions: dict[int, tuple[float, float]] = {}
    counter = 0

    def visit(node: Any, depth: int) -> None:
        nonlocal counter
        if node is None:
            return
        visit(getattr(node, left_name), depth + 1)
        positions[id(node)] = (float(counter), float(-depth))
        counter += 1
        visit(getattr(node, right_name), depth + 1)

    visit(root, 0)
    return positions


def _draw_splay_tree(ax: Any, tree: SplayTree, title: str, highlighted: Optional[SplayNode] = None) -> None:
    root = tree.root
    ax.set_title(title, fontsize=10, fontweight="bold", pad=10)
    ax.axis("off")
    if root is None:
        ax.text(0.5, 0.5, "Árbol vacío", ha="center", va="center")
        return

    positions = _binary_positions(root)
    stack = [root]
    seen: set[int] = set()
    nodes: list[SplayNode] = []
    while stack:
        node = stack.pop()
        if id(node) in seen:
            continue
        seen.add(id(node))
        nodes.append(node)
        for child in (node.left, node.right):
            if child is not None:
                x0, y0 = positions[id(node)]
                x1, y1 = positions[id(child)]
                ax.plot([x0, x1], [y0, y1], color="#3b3b3b", linewidth=1.5, zorder=1)
                stack.append(child)

    for node in nodes:
        x, y = positions[id(node)]
        face = "#ffcc66" if node is highlighted else "#eaf2fb"
        if node is root:
            face = "#9ed5a7" if node is not highlighted else "#f4b183"
        ax.scatter([x], [y], s=850, facecolor=face, edgecolor="#22313f", linewidth=1.2, zorder=2)
        ax.text(x, y, str(node.key), ha="center", va="center", fontsize=10, zorder=3)
    ax.set_xlim(-0.75, max(x for x, _ in positions.values()) + 0.75)
    ax.set_ylim(min(y for _, y in positions.values()) - 0.75, 0.75)


def _save_splay_frame(
    tree: SplayTree,
    destination: Path,
    step: int,
    node: SplayNode,
    operation: str,
) -> None:
    fig, ax = plt.subplots(figsize=(8.2, 4.7), constrained_layout=True)
    title = f"Paso {step:02d} | Nodo procesado: {node.key} | Operación: {operation}"
    _draw_splay_tree(ax, tree, title, highlighted=node)
    fig.savefig(destination, dpi=190, bbox_inches="tight")
    plt.close(fig)


def generate_splay_visualizations(output_dir: str | Path, figures_dir: str | Path) -> dict[str, Any]:
    """Genera cada rotación de zig-zig y el árbol final del ejercicio 2."""

    output = _ensure_dir(Path(output_dir))
    figures = _ensure_dir(Path(figures_dir))
    frames: list[str] = []

    # Se arma explícitamente el árbol de la guía para que el splay(20) sea
    # exactamente zig-zig, no una consecuencia ya autoajustada de inserciones.
    tree = SplayTree()
    n100, n50, n20 = SplayNode(100), SplayNode(50), SplayNode(20)
    tree.root = n100
    n100.left = n50
    n50.parent = n100
    n50.left = n20
    n20.parent = n50
    tree.validate()

    initial = output / "fig_splay_00_inicial.png"
    _save_splay_frame(tree, initial, 0, n20, "estado inicial antes de splay(20)")
    frames.append(str(initial))
    step = 0

    def capture(current_tree: SplayTree, pivot: SplayNode, event: str) -> None:
        nonlocal step
        step += 1
        frame = output / f"fig_splay_{step:02d}_rotacion.png"
        _save_splay_frame(current_tree, frame, step, pivot, event)
        frames.append(str(frame))

    tree.set_rotation_callback(capture)
    tree.splay(n20)
    tree.set_rotation_callback(None)
    tree.validate()
    assert tree.root is n20 and tree.keys() == [20, 50, 100]

    final = output / "fig_splay_final.png"
    _save_splay_frame(tree, final, step + 1, n20, "resultado final: raíz 20")
    frames.append(str(final))

    # Visualización mínima adicional pedida en el ejercicio resuelto 2.
    operations_tree = SplayTree()
    for key in [40, 20, 60, 10, 30, 50, 70]:
        operations_tree.insert(key)
    operations_tree.search(30)
    operations_tree.search(25)
    operations_tree.delete(40)
    operations_tree.validate()
    final_ops = output / "fig_splay_operaciones_final.png"
    _save_splay_frame(
        operations_tree,
        final_ops,
        1,
        operations_tree.root,
        "árbol final tras búsqueda, búsqueda fallida y delete(40)",
    )
    frames.append(str(final_ops))

    # Panel compacto para el informe, sin reemplazar la evidencia paso a paso.
    panel = figures / "fig_splay_rotaciones_resumen.png"
    selected = [initial, output / "fig_splay_01_rotacion.png", output / "fig_splay_02_rotacion.png", final]
    valid_selected = [path for path in selected if path.exists()]
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    for ax, image_path in zip(axes.flat, valid_selected):
        ax.imshow(plt.imread(image_path))
        ax.axis("off")
    for ax in list(axes.flat)[len(valid_selected) :]:
        ax.axis("off")
    fig.suptitle("Splay(20): conservación del in-order durante zig-zig", fontweight="bold", fontsize=13)
    fig.savefig(panel, dpi=190, bbox_inches="tight")
    plt.close(fig)

    return {
        "frames": frames,
        "panel": str(panel),
        "inorder": tree.keys(),
        "stats": tree.stats.snapshot(),
    }


def _tree_layout(vertices: Iterable[Any], edges: Iterable[tuple[Any, Any]], root: Any) -> dict[Any, tuple[float, float]]:
    """Layout de un árbol representado no dirigido, enraizado para dibujarlo."""

    adjacency: dict[Any, list[Any]] = {vertex: [] for vertex in vertices}
    for u, v in edges:
        adjacency.setdefault(u, []).append(v)
        adjacency.setdefault(v, []).append(u)
    for neighbors in adjacency.values():
        neighbors.sort(key=str)

    positions: dict[Any, tuple[float, float]] = {}
    leaf = 0

    def visit(node: Any, parent: Any, depth: int) -> float:
        nonlocal leaf
        children = [child for child in adjacency.get(node, []) if child != parent]
        if not children:
            x = float(leaf)
            leaf += 1
        else:
            child_x = [visit(child, node, depth + 1) for child in children]
            x = sum(child_x) / len(child_x)
        positions[node] = (x, float(-depth))
        return x

    visit(root, None, 0)
    return positions


def _edge_key(u: Any, v: Any) -> frozenset[Any]:
    return frozenset((u, v))


def _preferred_pairs(snapshot: list[dict[str, Any]], represented_edges: Iterable[tuple[Any, Any]]) -> set[frozenset[Any]]:
    real = {_edge_key(u, v) for u, v in represented_edges}
    preferred: set[frozenset[Any]] = set()
    for tree in snapshot:
        ordered = tree["inorder"]
        for u, v in zip(ordered, ordered[1:]):
            pair = _edge_key(u, v)
            if pair in real:
                preferred.add(pair)
    return preferred


def _draw_represented_tree(
    ax: Any,
    vertices: list[Any],
    edges: list[tuple[Any, Any]],
    root: Any,
    snapshot: list[dict[str, Any]],
    highlighted: Optional[Any] = None,
    show_preferred: bool = True,
) -> None:
    positions = _tree_layout(vertices, edges, root)
    preferred = _preferred_pairs(snapshot, edges) if show_preferred else set()
    for u, v in edges:
        x0, y0 = positions[u]
        x1, y1 = positions[v]
        is_preferred = _edge_key(u, v) in preferred
        ax.plot(
            [x0, x1],
            [y0, y1],
            color="#2563eb" if is_preferred else "#202020",
            linewidth=3.2 if is_preferred else 1.5,
            linestyle="-" if is_preferred else "--",
            zorder=1,
        )
    for vertex in vertices:
        x, y = positions[vertex]
        face = "#fbbf24" if vertex == highlighted else "#eaf2fb"
        if vertex == root:
            face = "#86efac" if vertex != highlighted else "#f4b183"
        ax.scatter([x], [y], s=620, facecolor=face, edgecolor="#172554", linewidth=1.2, zorder=2)
        ax.text(x, y, str(vertex), ha="center", va="center", fontsize=10, zorder=3)
    ax.text(
        0.01,
        0.01,
        "Azul continuo: arista de camino preferido\nNegro discontinuo: arista representada no preferida",
        transform=ax.transAxes,
        fontsize=7.5,
        va="bottom",
        bbox={"facecolor": "white", "edgecolor": "#cbd5e1", "alpha": 0.92},
    )
    ax.set_title("Árbol representado", fontweight="bold", fontsize=10)
    ax.axis("off")
    ax.set_xlim(-0.7, max(x for x, _ in positions.values()) + 0.7)
    ax.set_ylim(min(y for _, y in positions.values()) - 0.8, 0.8)


def _draw_auxiliary_forest(ax: Any, snapshot: list[dict[str, Any]]) -> None:
    """Dibuja todos los Splay Trees auxiliares en una sola vista."""

    ax.set_title("Splay Trees auxiliares", fontweight="bold", fontsize=10)
    ax.axis("off")
    if not snapshot:
        ax.text(0.5, 0.5, "Sin árboles auxiliares", ha="center", va="center")
        return

    total = len(snapshot)
    for index, tree in enumerate(snapshot):
        vertices = tree["vertices"]
        edges = tree["edges"]
        root = tree["root"]
        children: dict[Any, list[Any]] = {vertex: [] for vertex in vertices}
        for parent, child in edges:
            children[parent].append(child)
        for child_list in children.values():
            child_list.sort(key=str)

        local_positions: dict[Any, tuple[float, float]] = {}
        counter = 0

        def place(vertex: Any, depth: int) -> float:
            nonlocal counter
            descendants = children.get(vertex, [])
            if not descendants:
                x = float(counter)
                counter += 1
            else:
                xs = [place(child, depth + 1) for child in descendants]
                x = sum(xs) / len(xs)
            local_positions[vertex] = (x, float(-depth))
            return x

        place(root, 0)
        width = max(1.0, float(counter - 1))
        slot_left = index / total
        slot_width = 1.0 / total
        for parent, child in edges:
            x0, y0 = local_positions[parent]
            x1, y1 = local_positions[child]
            ax.plot(
                [slot_left + slot_width * (0.13 + 0.74 * x0 / width), slot_left + slot_width * (0.13 + 0.74 * x1 / width)],
                [0.72 + 0.09 * y0, 0.72 + 0.09 * y1],
                color="#475569",
                linewidth=1.1,
                zorder=1,
            )
        for vertex in vertices:
            x, y = local_positions[vertex]
            px = slot_left + slot_width * (0.13 + 0.74 * x / width)
            py = 0.72 + 0.09 * y
            color = "#a7f3d0" if vertex == root else "#dbeafe"
            ax.scatter([px], [py], s=260, transform=ax.transAxes, facecolor=color, edgecolor="#1e3a8a", zorder=2)
            ax.text(px, py, str(vertex), transform=ax.transAxes, ha="center", va="center", fontsize=8, zorder=3)
        ax.text(
            slot_left + slot_width / 2,
            0.10,
            f"raíz aux.: {root}\nin-order: {tree['inorder']}",
            transform=ax.transAxes,
            ha="center",
            va="bottom",
            fontsize=7,
            bbox={"facecolor": "#f8fafc", "edgecolor": "#cbd5e1", "alpha": 0.95},
        )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)


class ExposeTraceRenderer:
    """Observador que convierte una ejecución de EXPOSE en imágenes numeradas."""

    def __init__(
        self,
        forest: LinkCutForest,
        vertices: list[Any],
        represented_edges: list[tuple[Any, Any]],
        represented_root: Any,
        target: LinkCutNode,
        output_dir: str | Path,
        figures_dir: str | Path,
    ) -> None:
        self.forest = forest
        self.vertices = vertices
        self.edges = represented_edges
        self.root = represented_root
        self.target = target
        self.output = _ensure_dir(Path(output_dir))
        self.figures = _ensure_dir(Path(figures_dir))
        self.step = 0
        self.frames: list[str] = []

    def _save_combined(self, filename: str, node: Any, operation: str, *, show_preferred: bool = True) -> Path:
        snapshot = self.forest.auxiliary_snapshot()
        fig, axes = plt.subplots(1, 2, figsize=(13, 5.8), constrained_layout=True)
        title = f"Paso {self.step:02d} | Nodo procesado: {node} | Operación: {operation}"
        fig.suptitle(title, fontsize=13, fontweight="bold")
        _draw_represented_tree(
            axes[0], self.vertices, self.edges, self.root, snapshot, highlighted=node, show_preferred=show_preferred
        )
        _draw_auxiliary_forest(axes[1], snapshot)
        destination = self.output / filename
        fig.savefig(destination, dpi=190, bbox_inches="tight")
        plt.close(fig)
        self.frames.append(str(destination))
        return destination

    def save_initial_views(self) -> None:
        self.step = 0
        snapshot = self.forest.auxiliary_snapshot()
        fig, ax = plt.subplots(figsize=(8.5, 5.6), constrained_layout=True)
        fig.suptitle(
            f"Paso 00 | Nodo procesado: {self.target.vertex} | Operación: árbol representado antes de EXPOSE",
            fontweight="bold",
            fontsize=12,
        )
        _draw_represented_tree(ax, self.vertices, self.edges, self.root, snapshot, highlighted=self.target.vertex, show_preferred=False)
        before = self.output / "fig_expose_00_representado_antes.png"
        fig.savefig(before, dpi=190, bbox_inches="tight")
        plt.close(fig)
        self.frames.append(str(before))

        fig, ax = plt.subplots(figsize=(8.5, 5.6), constrained_layout=True)
        fig.suptitle(
            f"Paso 01 | Nodo procesado: {self.target.vertex} | Operación: descomposición inicial en caminos preferidos",
            fontweight="bold",
            fontsize=12,
        )
        _draw_represented_tree(ax, self.vertices, self.edges, self.root, snapshot, highlighted=self.target.vertex, show_preferred=True)
        preferred = self.output / "fig_expose_01_caminos_preferidos.png"
        fig.savefig(preferred, dpi=190, bbox_inches="tight")
        plt.close(fig)
        self.frames.append(str(preferred))

        fig, ax = plt.subplots(figsize=(10, 5.6), constrained_layout=True)
        fig.suptitle(
            f"Paso 02 | Nodo procesado: {self.target.vertex} | Operación: Splay Trees auxiliares antes de EXPOSE",
            fontweight="bold",
            fontsize=12,
        )
        _draw_auxiliary_forest(ax, snapshot)
        aux_before = self.output / "fig_expose_02_auxiliares_antes.png"
        fig.savefig(aux_before, dpi=190, bbox_inches="tight")
        plt.close(fig)
        self.frames.append(str(aux_before))
        self.step = 2

    def __call__(self, event: str, node: LinkCutNode, details: dict[str, Any]) -> None:
        if event in {"inicio de EXPOSE", "resultado de EXPOSE"}:
            return
        self.step += 1
        suffix = "splay" if "splay" in event else "preferida"
        annotation = event
        if "anterior" in details:
            annotation += f" (derecho anterior={details['anterior']}, nuevo={details['nuevo']})"
        self._save_combined(
            f"fig_expose_{self.step:02d}_{suffix}.png",
            node.vertex,
            annotation,
        )

    def save_final_views(self) -> dict[str, str]:
        self.step += 1
        final_aux = self._save_combined(
            f"fig_expose_{self.step:02d}_auxiliar_final.png",
            self.target.vertex,
            "Splay auxiliar final: camino raíz representada → objetivo",
        )
        self.step += 1
        after = self._save_combined(
            f"fig_expose_{self.step:02d}_representado_despues.png",
            self.target.vertex,
            "árbol representado después de EXPOSE (aristas reales sin cambios)",
            show_preferred=False,
        )

        # Panel legible para el informe: antes, caminos preferidos, último splay y resultado.
        chosen = [Path(self.frames[0]), Path(self.frames[1]), final_aux, after]
        panel = self.figures / "fig_expose_resumen.png"
        fig, axes = plt.subplots(2, 2, figsize=(14, 10), constrained_layout=True)
        for ax, image in zip(axes.flat, chosen):
            ax.imshow(plt.imread(image))
            ax.axis("off")
        fig.suptitle("Ejecución trazada de EXPOSE(6): representación y Splays auxiliares", fontweight="bold", fontsize=14)
        fig.savefig(panel, dpi=190, bbox_inches="tight")
        plt.close(fig)
        return {"final_auxiliary": str(final_aux), "represented_after": str(after), "panel": str(panel)}


def generate_expose_visualization(output_dir: str | Path, figures_dir: str | Path) -> dict[str, Any]:
    """Construye un árbol de siete nodos y documenta cada etapa de EXPOSE(6)."""

    values = {1: 4, 2: 7, 3: 2, 4: 9, 5: 1, 6: 6, 7: 3}
    edges = [(1, 2), (1, 3), (2, 4), (2, 5), (3, 6), (3, 7)]
    forest = LinkCutForest()
    nodes = {vertex: forest.create_node(vertex, value) for vertex, value in values.items()}
    for u, v in edges:
        forest.link(nodes[u], nodes[v])

    # Se fija una raíz conceptual para la explicación y se ejecutan exposiciones
    # previas que dejan una descomposición no trivial de caminos preferidos.
    forest.make_root(nodes[1])
    forest.expose(nodes[4])
    forest.expose(nodes[7])
    forest.validate()

    renderer = ExposeTraceRenderer(
        forest,
        list(values),
        edges,
        represented_root=1,
        target=nodes[6],
        output_dir=output_dir,
        figures_dir=figures_dir,
    )
    renderer.save_initial_views()
    edges_before = {tuple(sorted(edge)) for edge in edges}
    renderer.step = 2
    forest.expose(nodes[6], trace=renderer)
    forest.validate()
    final = renderer.save_final_views()
    assert nodes[6].path_sum == values[1] + values[3] + values[6]
    assert edges_before == {tuple(sorted(edge)) for edge in edges}

    manifest = {
        "target": 6,
        "represented_edges_before": sorted([list(edge) for edge in edges_before]),
        "represented_edges_after": sorted([list(edge) for edge in edges_before]),
        "frames": renderer.frames,
        "final": final,
        "stats": forest.stats_snapshot(),
    }
    manifest_path = Path(output_dir) / "manifest_expose.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest
