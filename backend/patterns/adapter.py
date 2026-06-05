"""
Patrón Estructural: Adapter
Permite que la interfaz interna del sistema trabaje con la API externa
del Congreso, que usa un formato incompatible.
"""
from abc import ABC, abstractmethod
from datetime import datetime, timezone


# Interfaz objetivo que el sistema interno espera

class ICongressNotifier(ABC):
    @abstractmethod
    def enviar_iniciativa(self, datos: dict) -> dict:
        """Envía la iniciativa legislativa al Congreso y retorna confirmación."""


# API externa del Congreso (interfaz incompatible)

class CongressAPIExterna:
    """Simula la API real del Congreso con su propio formato y métodos."""

    def submit_citizen_initiative(
        self,
        initiative_title: str,
        initiative_body: str,
        total_signatures: int,
        integrity_hash: str,
        submission_date: str,
        committees: list[str],
    ) -> dict:
        tracking = f"INIT-{integrity_hash[:8].upper()}-{datetime.now(timezone.utc).replace(tzinfo=None).year}"
        print(
            f"[CONGRESO API] Iniciativa recibida: '{initiative_title}' | "
            f"Firmas: {total_signatures} | Hash: {integrity_hash[:16]}... | "
            f"Tracking: {tracking}"
        )
        return {
            "success": True,
            "tracking_id": tracking,
            "received_at": submission_date,
            "assigned_committees": committees,
        }


# Adapter que traduce el formato interno al externo

class CongressNotificationAdapter(ICongressNotifier):
    """
    Adapta el formato interno de Propuesta al formato requerido por
    la API externa del Congreso.
    """

    _COMISIONES_POR_TEMA = {
        "educacion": ["Comisión de Educación", "Comisión de Presupuesto"],
        "salud": ["Comisión de Salud", "Comisión de Presupuesto"],
        "justicia": ["Comisión de Justicia y DDHH"],
        "ambiente": ["Comisión de Ambiente"],
        "default": ["Comisión de Constitución", "Comisión de Justicia y DDHH"],
    }

    def __init__(self):
        self._api = CongressAPIExterna()

    def enviar_iniciativa(self, datos: dict) -> dict:
        comisiones = self._determinar_comisiones(datos.get("titulo", ""))
        return self._api.submit_citizen_initiative(
            initiative_title=datos["titulo"],
            initiative_body=datos["contenido"],
            total_signatures=datos["firmas_count"],
            integrity_hash=datos["hash"],
            submission_date=datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            committees=comisiones,
        )

    def _determinar_comisiones(self, titulo: str) -> list[str]:
        titulo_lower = titulo.lower()
        for tema, comisiones in self._COMISIONES_POR_TEMA.items():
            if tema in titulo_lower:
                return comisiones
        return self._COMISIONES_POR_TEMA["default"]
