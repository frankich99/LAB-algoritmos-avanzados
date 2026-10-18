"""Pipeline reproducible de pruebas, experimentos y evidencias del Laboratorio 05.

Ejecutar este módulo genera los CSV, trazas, figuras y resúmenes que alimentan
el informe LaTeX. La semilla se fija para que cualquier resultado pueda
reproducirse sin depender de datos manualmente transcritos.
"""

from __future__ import annotations

import csv
import json
import platform
import random
import shutil
import sys
import time
from collections import Counter, deque
from pathlib import Path
from typing import Any, Iterable, Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from link_cut_tree import LinkCutForest, LinkCutNode
from reference_forest import ReferenceForest
from splay_tree import SplayNode, SplayTree
from visualizations import generate_expose_visualization, generate_splay_visualizations


BASE_DIR = Path(__file__).resolve().parent
FIGURES_DIR = BASE_DIR / "figuras"
RESULTS_DIR = BASE_DIR / "resultados"
TRACES_DIR = BASE_DIR / "trazas"
VISUAL_SPLAY_DIR = BASE_DIR / "visualizaciones" / "splay"
VISUAL_EXPOSE_DIR = BASE_DIR / "visualizaciones" / "expose"
LATEX_DIR = BASE_DIR.parent / "latex"
LATEX_FIGURES_DIR = LATEX_DIR / "figuras"
SEED = 2026


DETERMINISTIC_FIELDS = [
    "grupo",
    "operacion",
    "entrada",
    "esperado",
    "obtenido_link_cut",
    "obtenido_referencia",
    "validate",
    "estado",
]
DIFFERENTIAL_FIELDS = [
    "n",
    "semilla",
    "operaciones_totales",
    "link",
    "cut",
    "connected",
    "path_sum",
    "make_root",
    "discrepancias",
    "validaciones",
    "rotaciones",
    "splays",
    "exposes",
    "inversiones_perezosas",
    "estado",
]
EXPERIMENT_FIELDS = [
    "escenario",
    "forma",
    "n",
    "semilla",
    "lote",
    "operaciones",
    "tiempo_ms",
    "rotaciones",
    "splays",
    "exposes",
    "inversiones_perezosas",
    "updates",
    "rotaciones_por_operacion",
    "splays_por_operacion",
    "exposes_por_operacion",
    "estado",
]
REJECTION_FIELDS = ["operacion", "entrada", "error_esperado", "error_obtenido", "estado"]


def _prepare_directories() -> None:
    for directory in (FIGURES_DIR, RESULTS_DIR, TRACES_DIR, VISUAL_SPLAY_DIR, VISUAL_EXPOSE_DIR, LATEX_FIGURES_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def _write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _components(reference: ReferenceForest) -> list[list[int]]:
    """Componentes del modelo BFS sin alterar su estado."""

    unseen = set(reference.adj)
    result: list[list[int]] = []
    while unseen:
        start = min(unseen)
        queue: deque[int] = deque([start])
        component: list[int] = []
        unseen.remove(start)
        while queue:
            current = queue.popleft()
            component.append(current)
            for neighbor in reference.adj[current]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        result.append(sorted(component))
    return result


def _pick_disconnected_pair(reference: ReferenceForest, rng: random.Random) -> tuple[int, int]:
    components = _components(reference)
    if len(components) < 2:
        raise ValueError("No existen componentes distintas para LINK")
    first, second = rng.sample(components, 2)
    return rng.choice(first), rng.choice(second)


def _pick_connected_pair(reference: ReferenceForest, rng: random.Random) -> tuple[int, int]:
    components = _components(reference)
    nontrivial = [component for component in components if len(component) >= 2]
    component = rng.choice(nontrivial or components)
    if len(component) == 1:
        return component[0], component[0]
    return tuple(rng.sample(component, 2))  # type: ignore[return-value]


def _new_pair(values: dict[int, int]) -> tuple[LinkCutForest, dict[int, LinkCutNode], ReferenceForest]:
    forest = LinkCutForest()
    nodes = {vertex: forest.create_node(vertex, value) for vertex, value in values.items()}
    reference = ReferenceForest(values)
    return forest, nodes, reference


def _record(
    rows: list[dict[str, Any]],
    group: str,
    operation: str,
    input_text: str,
    expected: Any,
    lct: Any,
    reference: Any,
    valid: bool,
    state: str = "OK",
) -> None:
    rows.append(
        {
            "grupo": group,
            "operacion": operation,
            "entrada": input_text,
            "esperado": expected,
            "obtenido_link_cut": lct,
            "obtenido_referencia": reference,
            "validate": valid,
            "estado": state,
        }
    )


def run_splay_exercises() -> list[dict[str, Any]]:
    """Ejecuta y registra los dos ejercicios resueltos de Splay Tree."""

    rows: list[dict[str, Any]] = []

    # Ejercicio 1: cadena 100 <- 50 <- 20 y un zig-zig explícito.
    tree = SplayTree()
    n100, n50, n20 = SplayNode(100), SplayNode(50), SplayNode(20)
    tree.root = n100
    n100.left, n50.parent = n50, n100
    n50.left, n20.parent = n20, n50
    before = tree.keys()
    tree.splay(n20)
    valid = tree.validate()
    assert tree.root is n20 and tree.keys() == before and tree.stats.zig_zig == 1 and tree.stats.rotations == 2
    _record(rows, "Splay resuelto 1", "splay(20)", "100 <- 50 <- 20", "raíz=20; in-order=[20,50,100]", tree.root.key, tree.keys(), valid)

    # Ejercicio 2: interfaz indicada en la guía.
    dictionary = SplayTree()
    for key in [40, 20, 60, 10, 30, 50, 70]:
        dictionary.insert(key)
    assert dictionary.root is not None and dictionary.root.key == 70
    _record(rows, "Splay resuelto 2", "insert", "[40,20,60,10,30,50,70]", "raíz=70", dictionary.root.key, "n/a", dictionary.validate())

    found = dictionary.search(30)
    assert found is not None and dictionary.root is found and found.key == 30
    _record(rows, "Splay resuelto 2", "search(30)", "clave existente", "nodo=30 y raíz=30", dictionary.root.key, "n/a", dictionary.validate())

    missing = dictionary.search(25)
    assert missing is None and dictionary.root is not None and dictionary.root.key in {20, 30}
    _record(rows, "Splay resuelto 2", "search(25)", "clave ausente", "None; último visitado cerca de raíz", None, dictionary.root.key, dictionary.validate())

    deleted = dictionary.delete(40)
    absent_delete = dictionary.delete(999)
    assert deleted and not absent_delete
    _record(rows, "Splay resuelto 2", "delete", "40 y 999", "True y False", f"{deleted}, {absent_delete}", "n/a", dictionary.validate())

    # Split/join son parte de la interfaz mínima aunque no aparezcan en el
    # código reducido de la guía; se documentan como prueba explícita.
    split_tree = SplayTree()
    for key in [40, 20, 60, 10, 30, 50, 70]:
        split_tree.insert(key)
    lower, upper = split_tree.split(40)
    assert lower.keys() == [10, 20, 30] and upper.keys() == [40, 50, 60, 70]
    valid = lower.validate() and upper.validate()
    _record(rows, "Splay adicional", "split(40)", "[10,20,30,40,50,60,70]", "[10,20,30] | [40,50,60,70]", lower.keys(), upper.keys(), valid)
    lower.join(upper)
    assert lower.keys() == [10, 20, 30, 40, 50, 60, 70] and lower.validate()
    _record(rows, "Splay adicional", "join", "dos árboles separados por 40", "[10,20,30,40,50,60,70]", lower.keys(), "n/a", True)
    return rows


def run_reference_exercise() -> list[dict[str, Any]]:
    """Ejecuta el modelo BFS/DFS de la sección resuelta 3."""

    rows: list[dict[str, Any]] = []
    values = {1: 4, 2: 7, 3: 2, 4: 9, 5: 1, 6: 6, 7: 3}
    reference = ReferenceForest(values)
    for u, v in [(1, 2), (1, 3), (2, 4), (2, 5), (3, 6), (3, 7)]:
        reference.link(u, v)
    path = reference.path(4, 6)
    total = reference.path_sum(4, 6)
    assert path == [4, 2, 1, 3, 6] and total == 28 and reference.connected(5, 7)
    _record(rows, "Bosque referencia", "path(4,6)", "árbol de siete nodos", "[4,2,1,3,6]", "n/a", path, True)
    _record(rows, "Bosque referencia", "path_sum(4,6)", "valores de guía", 28, "n/a", total, True)
    reference.cut(1, 3)
    disconnected = reference.connected(4, 6)
    assert not disconnected
    _record(rows, "Bosque referencia", "cut(1,3)", "arista existente", False, "n/a", disconnected, True)
    return rows


def run_lct_deterministic() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Casos funcionales, de invariante y de rechazo explícito del LCT."""

    rows: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []
    values = {1: 4, 2: 7, 3: 2, 4: 9, 5: 1, 6: 6, 7: 3}
    forest, nodes, reference = _new_pair(values)
    assert forest.validate()

    # Nodos aislados y construcción del árbol de la guía.
    roots = [forest.find_root(nodes[v]).vertex for v in values]
    assert roots == list(values)
    _record(rows, "LCT aislados", "find_root", "vértices 1..7 aislados", list(values), roots, "n/a", forest.validate())
    guide_edges = [(1, 2), (1, 3), (2, 4), (2, 5), (3, 6), (3, 7)]
    for u, v in guide_edges:
        forest.link(nodes[u], nodes[v])
        reference.link(u, v)
        _record(rows, "LCT construcción", "link", f"({u},{v})", "componentes distintas", "aceptado", "aceptado", forest.validate())

    # Consultas requeridas por el escenario A.
    for u, v, expected in [(4, 5, 17), (4, 6, 28), (6, 7, 11)]:
        lct_total = forest.path_sum(nodes[u], nodes[v])
        ref_total = reference.path_sum(u, v)
        assert lct_total == ref_total == expected
        _record(rows, "Escenario A", "path_sum", f"({u},{v})", expected, lct_total, ref_total, forest.validate())

    # Cambios de raíz y exposiciones consecutivas.
    forest.make_root(nodes[4])
    root_after_reroot = forest.find_root(nodes[6]).vertex
    assert root_after_reroot == 4
    _record(rows, "LCT re-root", "make_root(4); find_root(6)", "misma componente", 4, root_after_reroot, "n/a", forest.validate())
    for vertex in [2, 7, 5, 6]:
        forest.expose(nodes[vertex])
        assert forest.validate()
    _record(rows, "LCT exposición", "expose sucesivos", "2,7,5,6", "invariantes preservados", "OK", "n/a", True)

    # Rechazos: ciclo y corte de una no-arista. En ambos casos se valida que
    # el bosque representado permanezca correcto tras el error controlado.
    try:
        forest.link(nodes[4], nodes[6])
    except ValueError as error:
        valid = forest.validate()
        rejections.append(
            {
                "operacion": "LINK",
                "entrada": "(4,6), nodos ya conectados",
                "error_esperado": "ciclo",
                "error_obtenido": str(error),
                "estado": "OK" if valid else "FALLO",
            }
        )
    else:
        raise AssertionError("LINK cíclico fue aceptado")

    try:
        forest.cut(nodes[4], nodes[6])
    except ValueError as error:
        valid = forest.validate()
        rejections.append(
            {
                "operacion": "CUT",
                "entrada": "(4,6), no es arista directa",
                "error_esperado": "arista inexistente/no directa",
                "error_obtenido": str(error),
                "estado": "OK" if valid else "FALLO",
            }
        )
    else:
        raise AssertionError("CUT de no-arista fue aceptado")

    # Corte real y re-enlace para verificar conectividad y suma después de
    # modificaciones dinámicas.
    forest.cut(nodes[1], nodes[3])
    reference.cut(1, 3)
    lct_connected = forest.connected(nodes[4], nodes[6])
    ref_connected = reference.connected(4, 6)
    assert lct_connected == ref_connected is False
    _record(
        rows,
        "Escenario A",
        "cut(1,3); connected(4,6)",
        "corte de una arista real y consulta entre componentes",
        False,
        lct_connected,
        ref_connected,
        forest.validate(),
    )
    forest.link(nodes[1], nodes[3])
    reference.link(1, 3)
    lct_total = forest.path_sum(nodes[4], nodes[6])
    ref_total = reference.path_sum(4, 6)
    assert lct_total == ref_total == 28
    _record(
        rows,
        "Escenario A",
        "link(1,3); path_sum(4,6)",
        "reconexión válida y consulta de camino",
        28,
        lct_total,
        ref_total,
        forest.validate(),
    )

    # Valores positivos, cero y negativos.
    signed, signed_nodes, signed_ref = _new_pair({1: 5, 2: 0, 3: -3})
    signed.link(signed_nodes[1], signed_nodes[2]); signed_ref.link(1, 2); assert signed.validate()
    signed.link(signed_nodes[2], signed_nodes[3]); signed_ref.link(2, 3); assert signed.validate()
    lct_signed = signed.path_sum(signed_nodes[1], signed_nodes[3])
    ref_signed = signed_ref.path_sum(1, 3)
    assert lct_signed == ref_signed == 2
    _record(rows, "LCT valores", "path_sum", "5 + 0 + (-3)", 2, lct_signed, ref_signed, signed.validate())
    return rows, rejections


def _choose_operation(reference: ReferenceForest, rng: random.Random) -> str:
    has_link = len(_components(reference)) > 1
    has_cut = bool(reference.edges())
    choices: list[tuple[str, int]] = [("connected", 22), ("path_sum", 23), ("make_root", 8)]
    if has_link:
        choices.append(("link", 28))
    if has_cut:
        choices.append(("cut", 19))
    labels, weights = zip(*choices)
    return rng.choices(labels, weights=weights, k=1)[0]


def run_differential_scenario(n: int, seed: int = SEED, operations: int = 5_000) -> tuple[dict[str, Any], Path]:
    """Compara al LCT contra BFS/DFS en una secuencia válida reproducible."""

    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed + n * 10_003)
    values = {vertex: rng.randint(-20, 20) for vertex in range(1, n + 1)}
    forest, nodes, reference = _new_pair(values)
    forest.validate()
    counts: Counter[str] = Counter()
    sequence: list[dict[str, Any]] = [
        {"kind": "metadata", "n": n, "seed": seed, "effective_seed": seed + n * 10_003, "values": values}
    ]
    discrepancy: Optional[dict[str, Any]] = None

    for step in range(1, operations + 1):
        operation = _choose_operation(reference, rng)
        entry: dict[str, Any] = {"kind": "operation", "step": step, "operation": operation}
        try:
            if operation == "link":
                u, v = _pick_disconnected_pair(reference, rng)
                forest.link(nodes[u], nodes[v])
                reference.link(u, v)
                entry.update({"u": u, "v": v, "expected": "linked"})
            elif operation == "cut":
                u, v = rng.choice(reference.edges())
                forest.cut(nodes[u], nodes[v])
                reference.cut(u, v)
                entry.update({"u": u, "v": v, "expected": "cut"})
            elif operation == "connected":
                u, v = rng.sample(range(1, n + 1), 2)
                expected = reference.connected(u, v)
                observed = forest.connected(nodes[u], nodes[v])
                assert observed == expected, f"connected({u},{v})={observed}, esperado={expected}"
                entry.update({"u": u, "v": v, "expected": expected, "observed": observed})
            elif operation == "path_sum":
                u, v = _pick_connected_pair(reference, rng)
                expected = reference.path_sum(u, v)
                observed = forest.path_sum(nodes[u], nodes[v])
                assert observed == expected, f"path_sum({u},{v})={observed}, esperado={expected}"
                entry.update({"u": u, "v": v, "expected": expected, "observed": observed})
            elif operation == "make_root":
                u = rng.randrange(1, n + 1)
                forest.make_root(nodes[u])
                root = forest.find_root(nodes[u]).vertex
                assert root == u, f"find_root({u})={root} tras make_root"
                entry.update({"u": u, "expected": u, "observed": root})
            else:
                raise AssertionError(f"Operación no soportada: {operation}")

            assert forest.validate()
            counts[operation] += 1
            entry["validate"] = True
            sequence.append(entry)
        except Exception as error:  # Persistimos toda la secuencia si algo falla.
            entry["error"] = repr(error)
            sequence.append(entry)
            discrepancy = {"step": step, "operation": operation, "error": repr(error)}
            break

    trace_path = TRACES_DIR / f"secuencia_diferencial_n{n}.jsonl"
    with trace_path.open("w", encoding="utf-8") as file:
        for entry in sequence:
            file.write(json.dumps(entry, ensure_ascii=False) + "\n")

    if discrepancy is not None:
        failure_path = TRACES_DIR / f"DISCREPANCIA_n{n}_semilla_{seed}.json"
        failure_path.write_text(
            json.dumps({"discrepancia": discrepancy, "secuencia": sequence}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        raise AssertionError(f"Discrepancia diferencial n={n}: {discrepancy}")

    stats = forest.stats_snapshot()
    return (
        {
            "n": n,
            "semilla": seed,
            "operaciones_totales": operations,
            "link": counts["link"],
            "cut": counts["cut"],
            "connected": counts["connected"],
            "path_sum": counts["path_sum"],
            "make_root": counts["make_root"],
            "discrepancias": 0,
            "validaciones": stats["validations"],
            "rotaciones": stats["rotations"],
            "splays": stats["splays"],
            "exposes": stats["exposes"],
            "inversiones_perezosas": stats["lazy_reversals"],
            "estado": "OK",
        },
        trace_path,
    )


def run_differential_experiments() -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    traces: list[str] = []
    for n in (30, 60, 120):
        row, trace = run_differential_scenario(n)
        rows.append(row)
        traces.append(str(trace))
    return rows, traces


def _topology(shape: str, n: int, rng: random.Random) -> list[tuple[int, int]]:
    if shape == "cadena":
        return [(vertex, vertex + 1) for vertex in range(1, n)]
    if shape == "estrella":
        return [(1, vertex) for vertex in range(2, n + 1)]
    if shape == "aleatorio":
        return [(vertex, rng.randrange(1, vertex)) for vertex in range(2, n + 1)]
    raise ValueError(f"Forma desconocida: {shape}")


def _build_experiment_forest(shape: str, n: int, rng: random.Random) -> tuple[LinkCutForest, dict[int, LinkCutNode], ReferenceForest]:
    values = {vertex: rng.randint(-50, 50) for vertex in range(1, n + 1)}
    forest, nodes, reference = _new_pair(values)
    for u, v in _topology(shape, n, rng):
        forest.link(nodes[u], nodes[v])
        reference.link(u, v)
    assert forest.validate()
    forest.reset_stats()
    return forest, nodes, reference


def _row_from_stats(
    shape: str,
    n: int,
    batch: str,
    operations: int,
    elapsed_ns: int,
    stats: dict[str, int],
) -> dict[str, Any]:
    divisor = max(1, operations)
    return {
        "escenario": "C",
        "forma": shape,
        "n": n,
        "semilla": SEED,
        "lote": batch,
        "operaciones": operations,
        "tiempo_ms": round(elapsed_ns / 1_000_000, 4),
        "rotaciones": stats["rotations"],
        "splays": stats["splays"],
        "exposes": stats["exposes"],
        "inversiones_perezosas": stats["lazy_reversals"],
        "updates": stats["updates"],
        "rotaciones_por_operacion": round(stats["rotations"] / divisor, 5),
        "splays_por_operacion": round(stats["splays"] / divisor, 5),
        "exposes_por_operacion": round(stats["exposes"] / divisor, 5),
        "estado": "OK",
    }


def _make_mixed_plan(reference: ReferenceForest, rng: random.Random, rounds: int) -> list[dict[str, Any]]:
    planner = reference.copy()
    plan: list[dict[str, Any]] = []
    vertices = sorted(planner.adj)
    for _ in range(rounds):
        u, v = rng.choice(planner.edges())
        planner.cut(u, v)
        plan.append({"operation": "cut", "u": u, "v": v})
        a, b = _pick_disconnected_pair(planner, rng)
        plan.append({"operation": "connected", "u": a, "v": b, "expected": False})
        root = rng.choice(vertices)
        plan.append({"operation": "make_root", "u": root})
        planner.link(a, b)
        plan.append({"operation": "link", "u": a, "v": b})
        p, q = rng.sample(vertices, 2)
        plan.append({"operation": "path_sum", "u": p, "v": q, "expected": planner.path_sum(p, q)})
    return plan


def run_experimental_scenario() -> list[dict[str, Any]]:
    """Escenario C: cadena, estrella y árbol aleatorio para cinco tamaños."""

    rows: list[dict[str, Any]] = []
    for n in (100, 200, 400, 800, 1600):
        for shape_index, shape in enumerate(("cadena", "estrella", "aleatorio")):
            rng = random.Random(SEED + n * 31 + shape_index)
            forest, nodes, reference = _build_experiment_forest(shape, n, rng)

            # Lote de conectividad y sumas: se calcula el oráculo fuera de la
            # zona medida, de modo que el tiempo sea solamente del Link-Cut Tree.
            pair_count = 120
            pairs = [tuple(rng.sample(range(1, n + 1), 2)) for _ in range(pair_count)]
            expected = [(reference.connected(u, v), reference.path_sum(u, v)) for u, v in pairs]
            forest.reset_stats()
            start = time.perf_counter_ns()
            for (u, v), (expected_connected, expected_sum) in zip(pairs, expected):
                assert forest.connected(nodes[u], nodes[v]) == expected_connected
                assert forest.path_sum(nodes[u], nodes[v]) == expected_sum
            elapsed = time.perf_counter_ns() - start
            assert forest.validate()
            rows.append(_row_from_stats(shape, n, "consultas_connected_y_path_sum", pair_count * 2, elapsed, forest.stats_snapshot()))

            # Secuencia mixta: corte válido, verificación de desconexión,
            # make_root, enlace válido y consulta de camino; cada ronda conserva
            # la condición de bosque.
            mixed_rounds = 45
            plan = _make_mixed_plan(reference, rng, mixed_rounds)
            forest.reset_stats()
            start = time.perf_counter_ns()
            for event in plan:
                operation = event["operation"]
                if operation == "cut":
                    forest.cut(nodes[event["u"]], nodes[event["v"]])
                elif operation == "connected":
                    assert forest.connected(nodes[event["u"]], nodes[event["v"]]) == event["expected"]
                elif operation == "make_root":
                    forest.make_root(nodes[event["u"]])
                elif operation == "link":
                    forest.link(nodes[event["u"]], nodes[event["v"]])
                elif operation == "path_sum":
                    assert forest.path_sum(nodes[event["u"]], nodes[event["v"]]) == event["expected"]
                else:
                    raise AssertionError(operation)
            elapsed = time.perf_counter_ns() - start
            assert forest.validate()
            rows.append(_row_from_stats(shape, n, "secuencia_mixta_link_cut", len(plan), elapsed, forest.stats_snapshot()))
    return rows


def _plot_differential(rows: list[dict[str, Any]]) -> Path:
    path = FIGURES_DIR / "fig_pruebas_diferenciales.png"
    operations = ["link", "cut", "connected", "path_sum", "make_root"]
    labels = [str(row["n"]) for row in rows]
    x = list(range(len(rows)))
    width = 0.15
    fig, ax = plt.subplots(figsize=(10, 5.5), constrained_layout=True)
    for index, operation in enumerate(operations):
        positions = [value + (index - 2) * width for value in x]
        ax.bar(positions, [row[operation] for row in rows], width=width, label=operation)
    ax.set_xticks(x, labels)
    ax.set_xlabel("Número de vértices n")
    ax.set_ylabel("Operaciones verificadas")
    ax.set_title("Pruebas diferenciales reproducibles: al menos 5000 operaciones por n")
    ax.legend(ncol=3)
    ax.grid(axis="y", linestyle=":", alpha=0.55)
    fig.savefig(path, dpi=210, bbox_inches="tight")
    plt.close(fig)
    return path


def _plot_experiments(rows: list[dict[str, Any]]) -> list[Path]:
    shapes = ("cadena", "estrella", "aleatorio")
    colors = {"cadena": "#2563eb", "estrella": "#d97706", "aleatorio": "#059669"}
    outputs: list[Path] = []

    for metric, ylabel, filename, title in [
        ("tiempo_ms", "Tiempo total (ms)", "fig_tiempo_por_forma.png", "Tiempo total por forma de árbol"),
        ("rotaciones_por_operacion", "Rotaciones promedio por operación", "fig_rotaciones_promedio.png", "Rotaciones promedio por operación"),
        ("splays_por_operacion", "Splays promedio por operación", "fig_operaciones_auxiliares.png", "Operaciones auxiliares promedio"),
    ]:
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharex=True, constrained_layout=True)
        for axis, batch, subtitle in zip(
            axes,
            ("consultas_connected_y_path_sum", "secuencia_mixta_link_cut"),
            ("Lote de connected + path_sum", "Secuencia mixta link/cut/make-root"),
        ):
            for shape in shapes:
                subset = [row for row in rows if row["forma"] == shape and row["lote"] == batch]
                subset.sort(key=lambda row: row["n"])
                axis.plot(
                    [row["n"] for row in subset],
                    [row[metric] for row in subset],
                    marker="o",
                    linewidth=2,
                    label=shape.capitalize(),
                    color=colors[shape],
                )
            axis.set_title(subtitle)
            axis.set_xlabel("n")
            axis.grid(True, linestyle=":", alpha=0.55)
        axes[0].set_ylabel(ylabel)
        axes[1].legend()
        fig.suptitle(title, fontweight="bold")
        path = FIGURES_DIR / filename
        fig.savefig(path, dpi=210, bbox_inches="tight")
        plt.close(fig)
        outputs.append(path)
    return outputs


def _sync_figures_to_latex() -> list[str]:
    """Copia solamente evidencias generadas por este pipeline al informe."""

    LATEX_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    sources = list(FIGURES_DIR.glob("*.png"))
    sources.extend(VISUAL_SPLAY_DIR.glob("*.png"))
    sources.extend(VISUAL_EXPOSE_DIR.glob("*.png"))
    for source in sources:
        destination = LATEX_FIGURES_DIR / source.name
        shutil.copy2(source, destination)
        copied.append(str(destination))
    return copied


def run_all() -> dict[str, Any]:
    """Ejecuta el laboratorio completo y exporta evidencias para el informe."""

    _prepare_directories()
    started = time.perf_counter()
    deterministic_rows = run_splay_exercises() + run_reference_exercise()
    lct_rows, rejection_rows = run_lct_deterministic()
    deterministic_rows.extend(lct_rows)

    splay_visual = generate_splay_visualizations(VISUAL_SPLAY_DIR, FIGURES_DIR)
    expose_visual = generate_expose_visualization(VISUAL_EXPOSE_DIR, FIGURES_DIR)
    differential_rows, traces = run_differential_experiments()
    experiment_rows = run_experimental_scenario()

    _write_csv(RESULTS_DIR / "casos_deterministas.csv", DETERMINISTIC_FIELDS, deterministic_rows)
    _write_csv(RESULTS_DIR / "pruebas_diferenciales.csv", DIFFERENTIAL_FIELDS, differential_rows)
    _write_csv(RESULTS_DIR / "metricas_experimento.csv", EXPERIMENT_FIELDS, experiment_rows)
    _write_csv(RESULTS_DIR / "rechazos_invalidos.csv", REJECTION_FIELDS, rejection_rows)
    differential_plot = _plot_differential(differential_rows)
    experiment_plots = _plot_experiments(experiment_rows)
    copied_figures = _sync_figures_to_latex()

    elapsed_seconds = time.perf_counter() - started
    summary = {
        "laboratorio": "05",
        "tema": "Splay Trees y árboles dinámicos Link-Cut",
        "semilla_global": SEED,
        "python": sys.version,
        "platform": platform.platform(),
        "duracion_segundos": round(elapsed_seconds, 3),
        "casos_deterministas": len(deterministic_rows),
        "pruebas_diferenciales": differential_rows,
        "filas_experimento": len(experiment_rows),
        "figuras_principales": [str(splay_visual["panel"]), str(expose_visual["final"]["panel"]), str(differential_plot)] + [str(path) for path in experiment_plots],
        "trazas": traces,
        "figuras_sincronizadas": copied_figures,
        "estado": "OK",
    }
    (RESULTS_DIR / "manifest_evidencias.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    text = [
        "=" * 76,
        "LABORATORIO 05 — RESUMEN DE EJECUCIÓN",
        "Splay Trees y árboles dinámicos Link-Cut",
        "=" * 76,
        f"Semilla global: {SEED}",
        f"Python: {sys.version.split()[0]}",
        f"Plataforma: {platform.platform()}",
        f"Duración total: {elapsed_seconds:.3f} s",
        f"Casos deterministas superados: {len(deterministic_rows)}",
        "Pruebas diferenciales: " + ", ".join(f"n={row['n']}: {row['operaciones_totales']} OK" for row in differential_rows),
        f"Filas de métricas experimentales: {len(experiment_rows)}",
        "Rechazos válidos comprobados: LINK cíclico y CUT inexistente/no directo.",
        "Visualizaciones generadas: splay paso a paso y EXPOSE paso a paso.",
        "Estado global: OK",
    ]
    (RESULTS_DIR / "resumen_ejecucion.txt").write_text("\n".join(text) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    result = run_all()
    print(json.dumps(result, ensure_ascii=False, indent=2))
