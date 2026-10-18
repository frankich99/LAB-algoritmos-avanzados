"""Link-Cut Tree con agregación de suma de caminos para el Laboratorio 05.

La estructura usa Splay Trees auxiliares.  El puntero ``parent`` tiene dos
papeles deliberados: enlaza nodos dentro de un árbol auxiliar y, cuando el
padre no reconoce al nodo como hijo, actúa como *path-parent* o conexión
virtual.  Por eso ``_is_aux_root`` nunca se reduce a ``parent is None``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass
class LinkCutStats:
    """Instrumentación solicitada por la guía."""

    rotations: int = 0
    splays: int = 0
    exposes: int = 0
    lazy_reversals: int = 0
    pushes: int = 0
    updates: int = 0
    links: int = 0
    cuts: int = 0
    validations: int = 0

    def snapshot(self) -> dict[str, int]:
        return {
            "rotations": self.rotations,
            "splays": self.splays,
            "exposes": self.exposes,
            "lazy_reversals": self.lazy_reversals,
            "pushes": self.pushes,
            "updates": self.updates,
            "links": self.links,
            "cuts": self.cuts,
            "validations": self.validations,
        }

    def reset(self) -> None:
        for field_name in self.snapshot():
            setattr(self, field_name, 0)


class LinkCutNode:
    """Manejador de un vértice del bosque representado."""

    def __init__(self, vertex: Any, value: int = 0) -> None:
        self.vertex = vertex
        self.value = value
        self.left: Optional[LinkCutNode] = None
        self.right: Optional[LinkCutNode] = None
        self.parent: Optional[LinkCutNode] = None
        self.reversed = False
        self.path_sum = value
        self.size = 1

    def __repr__(self) -> str:
        return (
            f"LinkCutNode(vertex={self.vertex!r}, value={self.value!r}, "
            f"size={self.size}, sum={self.path_sum})"
        )


ExposeTrace = Callable[[str, LinkCutNode, dict[str, Any]], None]


class LinkCutForest:
    """Bosque dinámico basado en Link-Cut Trees.

    Los métodos públicos reciben y devuelven manejadores ``LinkCutNode``.  La
    búsqueda por identificador no forma parte de las operaciones: el usuario
    conserva los manejadores creados con ``create_node``.
    """

    def __init__(self) -> None:
        self.nodes: list[LinkCutNode] = []
        self._nodes_by_vertex: dict[Any, LinkCutNode] = {}
        self.stats = LinkCutStats()

    def create_node(self, vertex: Any, value: int = 0) -> LinkCutNode:
        """Crea y devuelve el manejador de un vértice nuevo."""

        if vertex in self._nodes_by_vertex:
            raise ValueError(f"El vértice ya existe: {vertex!r}")
        node = LinkCutNode(vertex, value)
        self.nodes.append(node)
        self._nodes_by_vertex[vertex] = node
        return node

    def _ensure_known(self, node: LinkCutNode) -> None:
        if not isinstance(node, LinkCutNode) or node not in self.nodes:
            raise ValueError("El nodo no pertenece a este LinkCutForest")

    @staticmethod
    def _is_aux_root(node: LinkCutNode) -> bool:
        """Indica si el padre no reconoce a ``node`` como hijo auxiliar."""

        parent = node.parent
        return parent is None or (parent.left is not node and parent.right is not node)

    @staticmethod
    def _size(node: Optional[LinkCutNode]) -> int:
        return 0 if node is None else node.size

    @staticmethod
    def _sum(node: Optional[LinkCutNode]) -> int:
        return 0 if node is None else node.path_sum

    def _apply_reverse(self, node: Optional[LinkCutNode], *, record: bool = True) -> None:
        if node is None:
            return
        node.reversed = not node.reversed
        if record:
            self.stats.lazy_reversals += 1

    def _push(self, node: LinkCutNode, *, record: bool = True) -> None:
        """Propaga la inversión diferida antes de bajar o rotar."""

        if record:
            self.stats.pushes += 1
        if not node.reversed:
            return
        node.left, node.right = node.right, node.left
        self._apply_reverse(node.left, record=record)
        self._apply_reverse(node.right, record=record)
        node.reversed = False

    def _update(self, node: LinkCutNode, *, record: bool = True) -> None:
        """Recalcula los agregados únicamente desde el árbol auxiliar."""

        node.size = 1 + self._size(node.left) + self._size(node.right)
        node.path_sum = node.value + self._sum(node.left) + self._sum(node.right)
        if record:
            self.stats.updates += 1

    def _rotate(self, node: LinkCutNode) -> None:
        """Rota dentro del Splay auxiliar, preservando el path-parent."""

        parent = node.parent
        if parent is None:
            raise AssertionError("No se puede rotar un nodo sin padre")

        # Cumple la precondición de aplicar las marcas perezosas antes de usar
        # la orientación de los hijos.
        self._push(parent)
        self._push(node)
        grandparent = parent.parent

        if parent.left is node:
            beta = node.right
            parent.left = beta
            if beta is not None:
                beta.parent = parent
            node.right = parent
        elif parent.right is node:
            beta = node.left
            parent.right = beta
            if beta is not None:
                beta.parent = parent
            node.left = parent
        else:
            raise AssertionError("El padre no reconoce al nodo durante una rotación")

        parent.parent = node
        node.parent = grandparent
        if grandparent is not None:
            if grandparent.left is parent:
                grandparent.left = node
            elif grandparent.right is parent:
                grandparent.right = node
            # Si el abuelo no reconoce a parent, era un path-parent; node pasa
            # a ocupar esa misma conexión virtual y no debe convertirse en hijo.

        self._update(parent)
        self._update(node)
        self.stats.rotations += 1

    def _splay(self, node: LinkCutNode) -> None:
        """Splay auxiliar con propagación completa de marcas antes de rotar."""

        self.stats.splays += 1
        ancestors = [node]
        current = node
        while not self._is_aux_root(current):
            assert current.parent is not None
            current = current.parent
            ancestors.append(current)
        while ancestors:
            self._push(ancestors.pop())

        while not self._is_aux_root(node):
            parent = node.parent
            assert parent is not None
            grandparent = parent.parent
            if not self._is_aux_root(parent):
                assert grandparent is not None
                if (parent.left is node) == (grandparent.left is parent):
                    self._rotate(parent)
                else:
                    self._rotate(node)
            self._rotate(node)
        self._update(node)

    @staticmethod
    def _emit(
        trace: Optional[ExposeTrace], event: str, node: LinkCutNode, **details: Any
    ) -> None:
        if trace is not None:
            trace(event, node, details)

    def _expose(self, node: LinkCutNode, trace: Optional[ExposeTrace] = None) -> None:
        """Implementación interna de EXPOSE/ACCESS sobre un nodo conocido."""

        self._emit(trace, "inicio de EXPOSE", node)
        last: Optional[LinkCutNode] = None
        current: Optional[LinkCutNode] = node
        iteration = 0
        while current is not None:
            iteration += 1
            self._splay(current)
            self._emit(
                trace,
                "splay durante EXPOSE",
                current,
                iteration=iteration,
            )

            path_parent = current.parent
            old_right = current.right
            if old_right is not last:
                current.right = last
                if last is not None:
                    last.parent = current
                self._update(current)
                self._emit(
                    trace,
                    "cambio de arista preferida",
                    current,
                    iteration=iteration,
                    anterior=None if old_right is None else old_right.vertex,
                    nuevo=None if last is None else last.vertex,
                )
            last = current
            current = path_parent

        self._splay(node)
        self._emit(trace, "splay final de EXPOSE", node, iteration=iteration)
        self._emit(trace, "resultado de EXPOSE", node, iteration=iteration)

    def expose(self, node: LinkCutNode, trace: Optional[ExposeTrace] = None) -> None:
        """Expone el camino raíz representada → ``node`` en un Splay auxiliar."""

        self._ensure_known(node)
        self.stats.exposes += 1
        self._expose(node, trace)

    def make_root(self, node: LinkCutNode) -> None:
        """Convierte ``node`` en la raíz lógica de su árbol representado."""

        self._ensure_known(node)
        self.expose(node)
        self._apply_reverse(node)

    def find_root(self, node: LinkCutNode) -> LinkCutNode:
        """Devuelve la raíz vigente del árbol representado de ``node``."""

        self._ensure_known(node)
        self.expose(node)
        current = node
        self._push(current)
        while current.left is not None:
            current = current.left
            self._push(current)
        self._splay(current)
        return current

    def connected(self, u: LinkCutNode, v: LinkCutNode) -> bool:
        """Determina si dos manejadores pertenecen a la misma componente."""

        self._ensure_known(u)
        self._ensure_known(v)
        if u is v:
            return True
        return self.find_root(u) is self.find_root(v)

    def link(self, u: LinkCutNode, v: LinkCutNode) -> None:
        """Une componentes distintas; rechaza enlaces que formen ciclos."""

        self._ensure_known(u)
        self._ensure_known(v)
        if u is v or self.connected(u, v):
            raise ValueError("LINK produciría un ciclo")
        self.make_root(u)
        u.parent = v  # conexión virtual del nuevo árbol representado
        self.stats.links += 1

    def cut(self, u: LinkCutNode, v: LinkCutNode) -> None:
        """Elimina únicamente la arista real y directa ``(u, v)``."""

        self._ensure_known(u)
        self._ensure_known(v)
        if u is v:
            raise ValueError("CUT requiere dos vértices distintos")
        self.make_root(u)
        self.expose(v)
        # Tras make_root(u); expose(v), una arista directa deja exactamente a
        # u como hijo izquierdo de v y a u sin hijo derecho auxiliar.
        if v.left is not u or u.right is not None:
            raise ValueError("CUT solo puede eliminar una arista existente y directa")
        v.left.parent = None
        v.left = None
        self._update(v)
        self.stats.cuts += 1

    def path_sum(self, u: LinkCutNode, v: LinkCutNode) -> int:
        """Suma los valores sobre el camino simple entre nodos conectados."""

        self._ensure_known(u)
        self._ensure_known(v)
        if not self.connected(u, v):
            raise ValueError("PATH-SUM requiere nodos conectados")
        self.make_root(u)
        self.expose(v)
        return v.path_sum

    def stats_snapshot(self) -> dict[str, int]:
        return self.stats.snapshot()

    def reset_stats(self) -> None:
        self.stats.reset()

    def _materialize_auxiliary_trees(self) -> None:
        """Aplica lazy flags sin contaminar la instrumentación.

        Se usa para una visualización/validación fiel de la geometría actual de
        los Splays auxiliares. No modifica el bosque representado.
        """

        roots = [node for node in self.nodes if self._is_aux_root(node)]
        seen: set[int] = set()

        def visit(node: Optional[LinkCutNode]) -> None:
            if node is None or id(node) in seen:
                return
            seen.add(id(node))
            self._push(node, record=False)
            visit(node.left)
            visit(node.right)

        for root in roots:
            visit(root)

    def auxiliary_snapshot(self) -> list[dict[str, Any]]:
        """Describe los Splay Trees auxiliares para la visualización didáctica."""

        self._materialize_auxiliary_trees()
        roots = [node for node in self.nodes if self._is_aux_root(node)]
        roots.sort(key=lambda node: str(node.vertex))
        result: list[dict[str, Any]] = []

        def inorder(node: Optional[LinkCutNode], output: list[Any]) -> None:
            if node is None:
                return
            inorder(node.left, output)
            output.append(node.vertex)
            inorder(node.right, output)

        def collect(
            node: Optional[LinkCutNode],
            vertices: list[Any],
            edges: list[tuple[Any, Any]],
            seen: set[int],
        ) -> None:
            if node is None or id(node) in seen:
                return
            seen.add(id(node))
            vertices.append(node.vertex)
            if node.left is not None:
                edges.append((node.vertex, node.left.vertex))
                collect(node.left, vertices, edges, seen)
            if node.right is not None:
                edges.append((node.vertex, node.right.vertex))
                collect(node.right, vertices, edges, seen)

        for root in roots:
            vertices: list[Any] = []
            edges: list[tuple[Any, Any]] = []
            collect(root, vertices, edges, set())
            ordered: list[Any] = []
            inorder(root, ordered)
            result.append(
                {
                    "root": root.vertex,
                    "vertices": vertices,
                    "edges": edges,
                    "inorder": ordered,
                }
            )
        return result

    def validate(self) -> bool:
        """Verifica relaciones auxiliares, agregados y ausencia de ciclos.

        El método comprueba exclusivamente la representación de Link-Cut; la
        equivalencia con el bosque real se verifica en las pruebas con
        ``ReferenceForest``.  La propagación de flags dentro de la validación
        no se contabiliza para no distorsionar las métricas experimentales.
        """

        self.stats.validations += 1
        registered = {id(node) for node in self.nodes}
        if len(registered) != len(self.nodes):
            raise AssertionError("Un manejador fue registrado dos veces")

        roots = [node for node in self.nodes if self._is_aux_root(node)]
        seen: set[int] = set()

        def check_aux(node: Optional[LinkCutNode]) -> tuple[int, int]:
            if node is None:
                return 0, 0
            marker = id(node)
            if marker in seen:
                raise AssertionError("Ciclo o nodo compartido entre Splays auxiliares")
            seen.add(marker)
            self._push(node, record=False)
            if node.left is not None and node.left.parent is not node:
                raise AssertionError("Hijo izquierdo con parent inconsistente")
            if node.right is not None and node.right.parent is not node:
                raise AssertionError("Hijo derecho con parent inconsistente")
            left_size, left_sum = check_aux(node.left)
            right_size, right_sum = check_aux(node.right)
            expected_size = 1 + left_size + right_size
            expected_sum = node.value + left_sum + right_sum
            if node.size != expected_size:
                raise AssertionError(
                    f"size incorrecto en {node.vertex!r}: {node.size} != {expected_size}"
                )
            if node.path_sum != expected_sum:
                raise AssertionError(
                    f"path_sum incorrecto en {node.vertex!r}: {node.path_sum} != {expected_sum}"
                )
            return expected_size, expected_sum

        for root in roots:
            check_aux(root)
        if seen != registered:
            raise AssertionError("No todos los nodos aparecen en el bosque auxiliar")

        # Las cadenas parent (auxiliares y virtuales) deben terminar en None.
        for node in self.nodes:
            current: Optional[LinkCutNode] = node
            chain: set[int] = set()
            while current is not None:
                marker = id(current)
                if marker not in registered:
                    raise AssertionError("Parent apunta a un nodo externo")
                if marker in chain:
                    raise AssertionError("Ciclo detectado en punteros parent")
                chain.add(marker)
                current = current.parent
        return True
