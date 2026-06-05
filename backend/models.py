from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref
from datetime import datetime, timedelta, timezone
from database import Base

FIRMA_LIMITE = 25000
PLAZO_DIAS = 90


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    dni = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    colectivo = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    proposals = relationship("Proposal", back_populates="autor")
    signatures = relationship("Signature", back_populates="user")


class Proposal(Base):
    __tablename__ = "proposals"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    descripcion = Column(Text, nullable=False)
    contenido = Column(Text, nullable=False)
    # activa | congelada | enviada | expirada
    estado = Column(String, default="activa")
    firmas_count = Column(Integer, default=0)
    hash_congelamiento = Column(String, nullable=True)
    tracking_congreso = Column(String, nullable=True)
    autor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    deadline = Column(DateTime, nullable=True)
    congelada_at = Column(DateTime, nullable=True)

    autor = relationship("User", back_populates="proposals")
    signatures = relationship("Signature", back_populates="proposal")
    resources = relationship(
        "Resource",
        primaryjoin="and_(Resource.proposal_id==Proposal.id, Resource.parent_id==None)",
        foreign_keys="Resource.proposal_id",
        lazy="dynamic"
    )

    @property
    def dias_restantes(self) -> int:
        if self.deadline is None:
            return 0
        delta = self.deadline - datetime.now(timezone.utc).replace(tzinfo=None)
        return max(0, delta.days)

    @property
    def porcentaje_firmas(self) -> float:
        return min(100.0, round(self.firmas_count / FIRMA_LIMITE * 100, 2))


class Signature(Base):
    __tablename__ = "signatures"

    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, ForeignKey("proposals.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    hash_firma = Column(String, nullable=False, unique=True)

    proposal = relationship("Proposal", back_populates="signatures")
    user = relationship("User", back_populates="signatures")


class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, ForeignKey("proposals.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # comentario | documento | modificacion
    tipo = Column(String, nullable=False)
    contenido = Column(Text, nullable=False)
    parent_id = Column(Integer, ForeignKey("resources.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Composite: self-referential tree
    children = relationship(
        "Resource",
        backref=backref("parent", remote_side="Resource.id"),
        foreign_keys="Resource.parent_id"
    )
    user = relationship("User")
