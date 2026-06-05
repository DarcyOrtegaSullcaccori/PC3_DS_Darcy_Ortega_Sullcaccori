"""
Patrón Estructural: Proxy
Controla y valida el acceso al servicio de firmas antes de delegarlo
al servicio real. Actúa como guardián de las reglas de negocio.
"""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from fastapi import HTTPException


# Interfaz del servicio de firmas

class ISignatureService(ABC):
    @abstractmethod
    def firmar(self, proposal_id: int, user_id: int, db) -> object: ...


# Servicio real

class RealSignatureService(ISignatureService):
    def firmar(self, proposal_id: int, user_id: int, db) -> object:
        import hashlib
        from models import Signature, Proposal, FIRMA_LIMITE

        ts = datetime.now(timezone.utc).replace(tzinfo=None)
        user = db.query(__import__("models").User).filter_by(id=user_id).first()
        raw = f"{user.dni}:{proposal_id}:{ts.isoformat()}"
        hash_firma = hashlib.sha256(raw.encode()).hexdigest()

        sig = Signature(
            proposal_id=proposal_id,
            user_id=user_id,
            timestamp=ts,
            hash_firma=hash_firma,
        )
        db.add(sig)

        proposal = db.query(Proposal).filter_by(id=proposal_id).first()
        proposal.firmas_count += 1
        db.commit()
        db.refresh(sig)
        return sig


# Proxy de validación

class SignatureValidationProxy(ISignatureService):
    """
    Proxy que intercepta la operación de firma y verifica:
    1. Que la propuesta exista y esté activa.
    2. Que el plazo de 90 días no haya vencido.
    3. Que el usuario no haya firmado ya.
    Sólo delega al servicio real si todas las validaciones pasan.
    """

    def __init__(self, real_service: RealSignatureService):
        self._real = real_service

    def firmar(self, proposal_id: int, user_id: int, db) -> object:
        from models import Proposal, Signature

        proposal = db.query(Proposal).filter_by(id=proposal_id).first()
        if not proposal:
            raise HTTPException(404, "Propuesta no encontrada")

        if proposal.estado != "activa":
            raise HTTPException(400, f"La propuesta está '{proposal.estado}' y no acepta firmas")

        if proposal.deadline and datetime.now(timezone.utc).replace(tzinfo=None) > proposal.deadline:
            proposal.estado = "expirada"
            db.commit()
            raise HTTPException(400, "El plazo de 90 días para firmar ha vencido")

        existing = db.query(Signature).filter_by(
            proposal_id=proposal_id, user_id=user_id
        ).first()
        if existing:
            raise HTTPException(409, "Ya has firmado esta propuesta anteriormente")

        return self._real.firmar(proposal_id, user_id, db)
