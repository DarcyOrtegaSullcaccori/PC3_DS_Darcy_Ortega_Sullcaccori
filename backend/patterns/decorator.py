"""
Patrón Estructural: Decorator
Añade responsabilidades a un objeto/función dinámicamente.
Aquí se usa para auditar y registrar operaciones críticas del sistema.
"""
import functools
from datetime import datetime, timezone
from typing import Callable, Any

# Registro en memoria del audit log (en produccin ira a BD o archivo)
_audit_log: list[dict] = []


def get_audit_log() -> list[dict]:
    return _audit_log


def log_operation(operation_name: str):
    """Decorator de función que registra inicio, fin y errores de operaciones críticas."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            entry = {
                "operation": operation_name,
                "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
                "status": "INICIADO",
            }
            _audit_log.append(entry)
            try:
                result = func(*args, **kwargs)
                entry["status"] = "OK"
                return result
            except Exception as exc:
                entry["status"] = f"ERROR: {exc}"
                raise
        return wrapper
    return decorator


class AuditServiceDecorator:
    """
    Decorator de clase que envuelve cualquier servicio y registra cada llamada
    a método en el audit log.
    """
    def __init__(self, service: Any, service_name: str):
        self._service = service
        self._name = service_name

    def __getattr__(self, attr: str) -> Any:
        original = getattr(self._service, attr)
        if callable(original):
            @functools.wraps(original)
            def audited(*args, **kwargs):
                entry = {
                    "service": self._name,
                    "method": attr,
                    "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
                    "status": "INICIADO",
                }
                _audit_log.append(entry)
                try:
                    result = original(*args, **kwargs)
                    entry["status"] = "OK"
                    return result
                except Exception as exc:
                    entry["status"] = f"ERROR: {exc}"
                    raise
            return audited
        return original
