from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from models import Proposal, Signature, Resource, User
from schemas import (
    ProposalCreate, ProposalOut, ProposalDetail,
    SignatureOut, ResourceCreate, ResourceOut,
)
from auth import get_current_user, get_current_user_optional
from patterns.facade import ProposalFacade
from patterns.composite import ResourceTreeBuilder
from patterns.decorator import get_audit_log

router = APIRouter(prefix="/proposals", tags=["Propuestas"])


def _enrich(proposal: Proposal, current_user: Optional[User], db: Session) -> dict:
    data = {
        "id": proposal.id,
        "titulo": proposal.titulo,
        "descripcion": proposal.descripcion,
        "estado": proposal.estado,
        "firmas_count": proposal.firmas_count,
        "porcentaje_firmas": proposal.porcentaje_firmas,
        "dias_restantes": proposal.dias_restantes,
        "hash_congelamiento": proposal.hash_congelamiento,
        "tracking_congreso": proposal.tracking_congreso,
        "autor_id": proposal.autor_id,
        "created_at": proposal.created_at,
        "deadline": proposal.deadline,
        "congelada_at": proposal.congelada_at,
        "autor_nombre": proposal.autor.nombre if proposal.autor else None,
        "autor_colectivo": proposal.autor.colectivo if proposal.autor else None,
        "ya_firme": False,
    }
    if current_user:
        sig = db.query(Signature).filter_by(
            proposal_id=proposal.id, user_id=current_user.id
        ).first()
        data["ya_firme"] = sig is not None
    return data


# CRUD de propuestas

@router.get("", response_model=list[ProposalOut])
def list_proposals(
    estado: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    query = db.query(Proposal)
    if estado:
        query = query.filter(Proposal.estado == estado)
    if q:
        query = query.filter(Proposal.titulo.ilike(f"%{q}%"))
    proposals = query.order_by(Proposal.created_at.desc()).all()
    return [_enrich(p, current_user, db) for p in proposals]


@router.post("", response_model=ProposalDetail, status_code=201)
def create_proposal(
    body: ProposalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    facade = ProposalFacade(db)
    proposal = facade.crear_propuesta(
        titulo=body.titulo,
        descripcion=body.descripcion,
        contenido=body.contenido,
        autor_id=current_user.id,
    )
    data = _enrich(proposal, current_user, db)
    data["contenido"] = proposal.contenido
    return data


@router.get("/{proposal_id}", response_model=ProposalDetail)
def get_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    proposal = db.query(Proposal).filter_by(id=proposal_id).first()
    if not proposal:
        raise HTTPException(404, "Propuesta no encontrada")
    data = _enrich(proposal, current_user, db)
    data["contenido"] = proposal.contenido
    return data


# Firmar

@router.post("/{proposal_id}/sign", response_model=SignatureOut)
def sign_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    facade = ProposalFacade(db)
    sig = facade.firmar_propuesta(proposal_id, current_user.id)
    return sig


# Congelar manualmente

@router.post("/{proposal_id}/freeze", response_model=ProposalDetail)
def freeze_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    facade = ProposalFacade(db)
    proposal = facade.congelar_manual(proposal_id, current_user.id)
    data = _enrich(proposal, current_user, db)
    data["contenido"] = proposal.contenido
    return data


# Recursos (Composite)

@router.get("/{proposal_id}/resources", response_model=list[ResourceOut])
def get_resources(
    proposal_id: int,
    db: Session = Depends(get_db),
):
    proposal = db.query(Proposal).filter_by(id=proposal_id).first()
    if not proposal:
        raise HTTPException(404, "Propuesta no encontrada")

    # Carga todos los recursos (hojas y compuestos) en plano
    resources = (
        db.query(Resource)
        .filter_by(proposal_id=proposal_id)
        .order_by(Resource.created_at)
        .all()
    )
    builder = ResourceTreeBuilder()
    return builder.build(resources)


@router.post("/{proposal_id}/resources", response_model=ResourceOut, status_code=201)
def add_resource(
    proposal_id: int,
    body: ResourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    proposal = db.query(Proposal).filter_by(id=proposal_id).first()
    if not proposal:
        raise HTTPException(404, "Propuesta no encontrada")

    if body.parent_id:
        parent = db.query(Resource).filter_by(id=body.parent_id, proposal_id=proposal_id).first()
        if not parent:
            raise HTTPException(404, "Recurso padre no encontrado en esta propuesta")

    resource = Resource(
        proposal_id=proposal_id,
        user_id=current_user.id,
        tipo=body.tipo,
        contenido=body.contenido,
        parent_id=body.parent_id,
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)

    return {
        "id": resource.id,
        "proposal_id": resource.proposal_id,
        "user_id": resource.user_id,
        "tipo": resource.tipo,
        "contenido": resource.contenido,
        "parent_id": resource.parent_id,
        "created_at": resource.created_at,
        "autor_nombre": current_user.nombre,
        "children": [],
    }


# Audit log

@router.get("/admin/audit-log")
def audit_log():
    return get_audit_log()
