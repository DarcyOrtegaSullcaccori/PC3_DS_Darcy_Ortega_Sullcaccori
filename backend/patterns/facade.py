"""
Patrón Estructural: Facade
Provee una interfaz simplificada para el conjunto de subsistemas:
  - Servicio de propuestas (CRUD en BD)
  - Servicio criptográfico (congelamiento)
  - Adaptador de notificaciones al Congreso
  - Decorador de auditoría
"""
import hashlib
import json
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import Proposal, Signature, User, FIRMA_LIMITE, PLAZO_DIAS
from patterns.decorator import AuditServiceDecorator, log_operation
from patterns.adapter import CongressNotificationAdapter
from patterns.proxy import SignatureValidationProxy, RealSignatureService


class CryptoService:
    """Sub-sistema de congelamiento criptográfico (SHA-256)."""

    def freeze(self, proposal: Proposal, signatures: list[Signature]) -> str:
        payload = {
            "proposal_id": proposal.id,
            "titulo": proposal.titulo,
            "contenido": proposal.contenido,
            "autor_id": proposal.autor_id,
            "firmas": sorted([s.hash_firma for s in signatures]),
            "congelado_en": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        }
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class ProposalFacade:
    """
    Facade principal: interfaz única para toda la lógica de negocio de
    Iniciativas Legislativas Ciudadanas.
    """

    def __init__(self, db: Session):
        self._db = db
        self._crypto = CryptoService()
        self._congress = CongressNotificationAdapter()
        # Envuelve el congreso con auditora (Decorator)
        self._congress_audited = AuditServiceDecorator(self._congress, "CongressAdapter")
        # Proxy de firma
        self._signature_proxy = SignatureValidationProxy(RealSignatureService())

    # Creación de propuesta

    @log_operation("CREAR_PROPUESTA")
    def crear_propuesta(
        self, titulo: str, descripcion: str, contenido: str, autor_id: int
    ) -> Proposal:
        deadline = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=PLAZO_DIAS)
        proposal = Proposal(
            titulo=titulo,
            descripcion=descripcion,
            contenido=contenido,
            autor_id=autor_id,
            deadline=deadline,
            estado="activa",
        )
        self._db.add(proposal)
        self._db.commit()
        self._db.refresh(proposal)
        return proposal

    # Firma de propuesta

    @log_operation("FIRMAR_PROPUESTA")
    def firmar_propuesta(self, proposal_id: int, user_id: int) -> Signature:
        sig = self._signature_proxy.firmar(proposal_id, user_id, self._db)
        # Verificar si alcanz el lmite
        proposal = self._db.query(Proposal).filter_by(id=proposal_id).first()
        if proposal.firmas_count >= FIRMA_LIMITE:
            self._congelar_y_enviar(proposal)
        return sig

    # Congelamiento criptográfico

    @log_operation("CONGELAR_PROPUESTA")
    def _congelar_y_enviar(self, proposal: Proposal) -> None:
        signatures = self._db.query(Signature).filter_by(proposal_id=proposal.id).all()
        hash_value = self._crypto.freeze(proposal, signatures)

        proposal.estado = "congelada"
        proposal.hash_congelamiento = hash_value
        proposal.congelada_at = datetime.now(timezone.utc).replace(tzinfo=None)
        self._db.commit()

        # Enviar al Congreso va Adapter (con auditora Decorator)
        resultado = self._congress_audited.enviar_iniciativa({
            "titulo": proposal.titulo,
            "contenido": proposal.contenido,
            "firmas_count": proposal.firmas_count,
            "hash": hash_value,
        })

        if resultado.get("success"):
            proposal.estado = "enviada"
            proposal.tracking_congreso = resultado.get("tracking_id")
            self._db.commit()

    # Congelar manualmente (autor/admin)

    @log_operation("CONGELAR_MANUAL")
    def congelar_manual(self, proposal_id: int, user_id: int) -> Proposal:
        proposal = self._db.query(Proposal).filter_by(id=proposal_id).first()
        if not proposal:
            raise HTTPException(404, "Propuesta no encontrada")
        if proposal.autor_id != user_id:
            raise HTTPException(403, "Solo el autor puede congelar la propuesta")
        if proposal.estado != "activa":
            raise HTTPException(400, f"La propuesta ya está '{proposal.estado}'")
        self._congelar_y_enviar(proposal)
        self._db.refresh(proposal)
        return proposal
