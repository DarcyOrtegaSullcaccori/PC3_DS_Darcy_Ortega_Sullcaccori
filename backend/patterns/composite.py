"""
Patrón Estructural: Composite
Compone los recursos de apoyo (comentarios, documentos, modificaciones)
en una estructura de árbol parte-todo, permitiendo tratarlos uniformemente.
"""
from abc import ABC, abstractmethod
from datetime import datetime


# Interfaz común del componente

class ResourceComponent(ABC):
    @abstractmethod
    def get_tipo(self) -> str: ...

    @abstractmethod
    def get_contenido(self) -> str: ...

    @abstractmethod
    def to_dict(self) -> dict: ...

    def add(self, component: "ResourceComponent") -> None:
        raise NotImplementedError("Las hojas no soportan hijos")

    def remove(self, component: "ResourceComponent") -> None:
        raise NotImplementedError("Las hojas no soportan hijos")


# Hoja: recurso sin hijos

class ResourceLeaf(ResourceComponent):
    def __init__(
        self,
        id: int,
        tipo: str,
        contenido: str,
        autor: str,
        created_at: datetime,
        parent_id: int | None = None,
        proposal_id: int = 0,
        user_id: int = 0,
    ):
        self._id = id
        self._tipo = tipo
        self._contenido = contenido
        self._autor = autor
        self._created_at = created_at
        self._parent_id = parent_id
        self._proposal_id = proposal_id
        self._user_id = user_id

    def get_tipo(self) -> str:
        return self._tipo

    def get_contenido(self) -> str:
        return self._contenido

    def to_dict(self) -> dict:
        return {
            "id": self._id,
            "tipo": self._tipo,
            "contenido": self._contenido,
            "autor_nombre": self._autor,
            "created_at": self._created_at.isoformat(),
            "parent_id": self._parent_id,
            "proposal_id": self._proposal_id,
            "user_id": self._user_id,
            "children": [],
        }


# Compuesto: recurso con hijos

class ResourceComposite(ResourceComponent):
    def __init__(
        self,
        id: int,
        tipo: str,
        contenido: str,
        autor: str,
        created_at: datetime,
        parent_id: int | None = None,
        proposal_id: int = 0,
        user_id: int = 0,
    ):
        self._id = id
        self._tipo = tipo
        self._contenido = contenido
        self._autor = autor
        self._created_at = created_at
        self._parent_id = parent_id
        self._proposal_id = proposal_id
        self._user_id = user_id
        self._children: list[ResourceComponent] = []

    def add(self, component: ResourceComponent) -> None:
        self._children.append(component)

    def remove(self, component: ResourceComponent) -> None:
        self._children.remove(component)

    def get_tipo(self) -> str:
        return self._tipo

    def get_contenido(self) -> str:
        return self._contenido

    def to_dict(self) -> dict:
        return {
            "id": self._id,
            "tipo": self._tipo,
            "contenido": self._contenido,
            "autor_nombre": self._autor,
            "created_at": self._created_at.isoformat(),
            "parent_id": self._parent_id,
            "proposal_id": self._proposal_id,
            "user_id": self._user_id,
            "children": [c.to_dict() for c in self._children],
        }


# Builder del árbol desde registros de BD

class ResourceTreeBuilder:
    """Construye el árbol Composite a partir de registros planos de BD."""

    def build(self, db_resources: list) -> list[dict]:
        if not db_resources:
            return []

        nodes: dict[int, ResourceComponent] = {}

        for r in db_resources:
            autor = r.user.nombre if r.user else "Desconocido"
            has_children = bool(r.children)
            if has_children:
                node = ResourceComposite(
                    r.id, r.tipo, r.contenido, autor, r.created_at,
                    r.parent_id, r.proposal_id, r.user_id
                )
            else:
                node = ResourceLeaf(
                    r.id, r.tipo, r.contenido, autor, r.created_at,
                    r.parent_id, r.proposal_id, r.user_id
                )
            nodes[r.id] = node

        roots: list[ResourceComponent] = []
        for r in db_resources:
            node = nodes[r.id]
            if r.parent_id is None:
                roots.append(node)
            elif r.parent_id in nodes:
                parent = nodes[r.parent_id]
                if isinstance(parent, ResourceComposite):
                    parent.add(node)

        return [n.to_dict() for n in roots]
