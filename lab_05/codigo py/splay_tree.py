"""Splay Tree de diccionario para el Laboratorio 05.

La implementación mantiene punteros padre y aplica splay al nodo visitado en
búsquedas, inserciones y eliminaciones.  Incluye validación estructural,
``split`` y ``join`` destructivos para poder usarla también como evidencia del
trabajo preparatorio de la guía.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Optional


@dataclass
class SplayStats:
    """Contadores de los casos de autoajuste ejecutados."""

    rotations: int = 0
    zig: int = 0
    zig_zig: int = 0
    zig_zag: int = 0
    splays: int = 0

    def snapshot(self) -> dict[str, int]:
        return {
            "rotations": self.rotations,
            "zig": self.zig,
            "zig_zig": self.zig_zig,
            "zig_zag": self.zig_zag,
            "splays": self.splays,
        }


class SplayNode:
    """Nodo de un árbol binario de búsqueda autoajustable."""

    def __init__(self, key: Any, value: Any = None) -> None:
        self.key = key
        self.value = value
        self.left: Optional[SplayNode] = None
        self.right: Optional[SplayNode] = None
        self.parent: Optional[SplayNode] = None

    def __repr__(self) -> str:
        return f"SplayNode(key={self.key!r}, value={self.value!r})"


RotationCallback = Callable[["SplayTree", SplayNode, str], None]


class SplayTree:
    """Árbol binario de búsqueda con las operaciones clásicas de splay."""

    def __init__(self) -> None:
        self.root: Optional[SplayNode] = None
        self.stats = SplayStats()
        self._rotation_callback: Optional[RotationCallback] = None

    def set_rotation_callback(self, callback: Optional[RotationCallback]) -> None:
        """Registra un observador llamado después de cada rotación.

        Se usa únicamente para la visualización didáctica y no interviene en la
        lógica del árbol.
        """

        self._rotation_callback = callback

    def _replace_parent_link(self, old: SplayNode, new: SplayNode) -> None:
        parent = old.parent
        if parent is None:
            self.root = new
        elif parent.left is old:
            parent.left = new
        elif parent.right is old:
            parent.right = new
        else:
            raise AssertionError("El padre no reconoce al nodo que se rota")
        new.parent = parent

    def _rotate(self, node: SplayNode, event: str = "rotación") -> None:
        """Rota ``node`` sobre su padre en tiempo constante."""

        parent = node.parent
        if parent is None:
            raise ValueError("No se puede rotar la raíz")

        if parent.left is node:  # rotación a la derecha
            beta = node.right
            self._replace_parent_link(parent, node)
            node.right = parent
            parent.parent = node
            parent.left = beta
            direction = "rotación derecha"
        elif parent.right is node:  # rotación a la izquierda
            beta = node.left
            self._replace_parent_link(parent, node)
            node.left = parent
            parent.parent = node
            parent.right = beta
            direction = "rotación izquierda"
        else:
            raise AssertionError("El nodo no es hijo de su padre")

        if beta is not None:
            beta.parent = parent

        self.stats.rotations += 1
        if self._rotation_callback is not None:
            self._rotation_callback(self, node, f"{event}: {direction}")

    def _splay(self, node: SplayNode) -> None:
        """Lleva ``node`` a la raíz aplicando zig, zig-zig y zig-zag."""

        self.stats.splays += 1
        while node.parent is not None:
            parent = node.parent
            grandparent = parent.parent
            if grandparent is None:
                self.stats.zig += 1
                self._rotate(node, "zig")
            elif (grandparent.left is parent) == (parent.left is node):
                self.stats.zig_zig += 1
                self._rotate(parent, "zig-zig (primera)")
                self._rotate(node, "zig-zig (segunda)")
            else:
                self.stats.zig_zag += 1
                self._rotate(node, "zig-zag (primera)")
                self._rotate(node, "zig-zag (segunda)")

    def splay(self, node: SplayNode) -> SplayNode:
        """API pública para autoajustar un manejador de nodo existente."""

        self._splay(node)
        return node

    def search(self, key: Any) -> Optional[SplayNode]:
        """Busca una clave y hace splay del hallado o del último visitado."""

        current = self.root
        last: Optional[SplayNode] = None
        while current is not None:
            last = current
            if key == current.key:
                self._splay(current)
                return current
            current = current.left if key < current.key else current.right

        if last is not None:
            self._splay(last)
        return None

    def insert(self, key: Any, value: Any = None) -> SplayNode:
        """Inserta una clave o devuelve la existente, siempre en la raíz."""

        if self.root is None:
            self.root = SplayNode(key, value)
            return self.root

        current = self.root
        while True:
            if key == current.key:
                if value is not None:
                    current.value = value
                self._splay(current)
                return current
            if key < current.key:
                if current.left is None:
                    current.left = SplayNode(key, value)
                    current.left.parent = current
                    self._splay(current.left)
                    return self.root
                current = current.left
            else:
                if current.right is None:
                    current.right = SplayNode(key, value)
                    current.right.parent = current
                    self._splay(current.right)
                    return self.root
                current = current.right

    def delete(self, key: Any) -> bool:
        """Elimina una clave mediante separación de subárboles y join."""

        node = self.search(key)
        if node is None or self.root is None or self.root.key != key:
            return False

        left, right = self.root.left, self.root.right
        if left is not None:
            left.parent = None
        if right is not None:
            right.parent = None

        # Aísla el nodo eliminado, útil para depuración de punteros.
        self.root.left = self.root.right = None
        self.root = left

        if left is None:
            self.root = right
            return True

        maximum = self._maximum(left)
        self._splay(maximum)
        self.root.right = right
        if right is not None:
            right.parent = self.root
        return True

    def split(self, key: Any) -> tuple["SplayTree", "SplayTree"]:
        """Separa destructivamente en claves ``< key`` y claves ``>= key``.

        El árbol receptor queda vacío.  Esta semántica evita que un mismo nodo
        pertenezca accidentalmente a dos árboles Python distintos.
        """

        left_tree, right_tree = SplayTree(), SplayTree()
        if self.root is None:
            return left_tree, right_tree

        self.search(key)  # deja en la raíz la clave o el último candidato
        assert self.root is not None
        root = self.root
        if root.key < key:
            detached = root.right
            root.right = None
            if detached is not None:
                detached.parent = None
            left_tree.root = root
            right_tree.root = detached
        else:
            detached = root.left
            root.left = None
            if detached is not None:
                detached.parent = None
            left_tree.root = detached
            right_tree.root = root

        self.root = None
        return left_tree, right_tree

    def join(self, other: "SplayTree") -> "SplayTree":
        """Une destructivamente dos árboles con claves ordenadas.

        Requiere que toda clave de ``self`` sea menor que toda clave de
        ``other``.  El árbol ``other`` queda vacío al terminar.
        """

        if other.root is None:
            return self
        if self.root is None:
            self.root, other.root = other.root, None
            return self

        maximum = self._maximum(self.root)
        minimum = self._minimum(other.root)
        if not maximum.key < minimum.key:
            raise ValueError("join requiere que las claves del primer árbol sean menores")

        self._splay(maximum)
        assert self.root is maximum and self.root.right is None
        self.root.right = other.root
        other.root.parent = self.root
        other.root = None
        return self

    @staticmethod
    def _minimum(node: SplayNode) -> SplayNode:
        while node.left is not None:
            node = node.left
        return node

    @staticmethod
    def _maximum(node: SplayNode) -> SplayNode:
        while node.right is not None:
            node = node.right
        return node

    def inorder_items(self) -> list[tuple[Any, Any]]:
        """Devuelve el recorrido in-order iterativo para comprobar el BST."""

        result: list[tuple[Any, Any]] = []
        stack: list[SplayNode] = []
        current = self.root
        while stack or current is not None:
            while current is not None:
                stack.append(current)
                current = current.left
            current = stack.pop()
            result.append((current.key, current.value))
            current = current.right
        return result

    def keys(self) -> list[Any]:
        return [key for key, _ in self.inorder_items()]

    def validate(self) -> bool:
        """Comprueba orden BST, enlaces padre-hijo y ausencia de ciclos."""

        if self.root is None:
            return True
        if self.root.parent is not None:
            raise AssertionError("La raíz del Splay Tree tiene padre")

        visited: set[int] = set()

        def visit(node: Optional[SplayNode], low: Any, high: Any) -> None:
            if node is None:
                return
            if id(node) in visited:
                raise AssertionError("Ciclo detectado en el Splay Tree")
            visited.add(id(node))
            if low is not None and not low < node.key:
                raise AssertionError("Violación de orden BST por el límite inferior")
            if high is not None and not node.key < high:
                raise AssertionError("Violación de orden BST por el límite superior")
            if node.left is not None and node.left.parent is not node:
                raise AssertionError("Hijo izquierdo con padre inconsistente")
            if node.right is not None and node.right.parent is not node:
                raise AssertionError("Hijo derecho con padre inconsistente")
            visit(node.left, low, node.key)
            visit(node.right, node.key, high)

        visit(self.root, None, None)
        ordered = self.keys()
        if ordered != sorted(ordered):
            raise AssertionError("El recorrido in-order no está ordenado")
        return True

    @classmethod
    def from_items(cls, items: Iterable[tuple[Any, Any]]) -> "SplayTree":
        tree = cls()
        for key, value in items:
            tree.insert(key, value)
        return tree
