"""Modelo de referencia sencillo para validar el Link-Cut Tree.

No intenta ser eficiente: usa listas de adyacencia y BFS, por lo que sirve como
oráculo de corrección para las pruebas deterministas y diferenciales.
"""

from __future__ import annotations

from collections import deque
from typing import Hashable, Iterable


Vertex = Hashable


class ReferenceForest:
    """Bosque no dirigido con operaciones explícitas de costo lineal."""

    def __init__(self, values: dict[Vertex, int] | Iterable[tuple[Vertex, int]]) -> None:
        self.value = dict(values)
        self.adj: dict[Vertex, set[Vertex]] = {vertex: set() for vertex in self.value}

    def _check_vertex(self, vertex: Vertex) -> None:
        if vertex not in self.adj:
            raise KeyError(f"Vértice inexistente: {vertex!r}")

    def connected(self, source: Vertex, target: Vertex) -> bool:
        self._check_vertex(source)
        self._check_vertex(target)
        if source == target:
            return True
        queue: deque[Vertex] = deque([source])
        seen = {source}
        while queue:
            current = queue.popleft()
            for neighbor in self.adj[current]:
                if neighbor == target:
                    return True
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)
        return False

    def link(self, u: Vertex, v: Vertex) -> None:
        self._check_vertex(u)
        self._check_vertex(v)
        if u == v or self.connected(u, v):
            raise ValueError("LINK produciría un ciclo")
        self.adj[u].add(v)
        self.adj[v].add(u)

    def cut(self, u: Vertex, v: Vertex) -> None:
        self._check_vertex(u)
        self._check_vertex(v)
        if v not in self.adj[u]:
            raise ValueError("La arista no existe")
        self.adj[u].remove(v)
        self.adj[v].remove(u)

    def path(self, source: Vertex, target: Vertex) -> list[Vertex]:
        self._check_vertex(source)
        self._check_vertex(target)
        queue: deque[Vertex] = deque([source])
        parent: dict[Vertex, Vertex | None] = {source: None}
        while queue:
            current = queue.popleft()
            if current == target:
                break
            for neighbor in self.adj[current]:
                if neighbor not in parent:
                    parent[neighbor] = current
                    queue.append(neighbor)
        if target not in parent:
            raise ValueError("Los nodos no están conectados")

        result: list[Vertex] = []
        current: Vertex | None = target
        while current is not None:
            result.append(current)
            current = parent[current]
        result.reverse()
        return result

    def path_sum(self, u: Vertex, v: Vertex) -> int:
        return sum(self.value[vertex] for vertex in self.path(u, v))

    def edges(self) -> list[tuple[Vertex, Vertex]]:
        """Lista determinista de aristas no dirigidas sin duplicados."""

        result: list[tuple[Vertex, Vertex]] = []
        seen: set[frozenset[Vertex]] = set()
        for u, neighbors in self.adj.items():
            for v in neighbors:
                marker = frozenset((u, v))
                if marker not in seen:
                    seen.add(marker)
                    result.append((u, v))
        return result

    def copy(self) -> "ReferenceForest":
        clone = ReferenceForest(self.value)
        for u, v in self.edges():
            clone.link(u, v)
        return clone
