from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime


# Auth

class UserCreate(BaseModel):
    nombre: str
    dni: str
    email: EmailStr
    password: str
    colectivo: Optional[str] = None

    @field_validator("dni")
    @classmethod
    def dni_length(cls, v: str) -> str:
        if len(v) != 8 or not v.isdigit():
            raise ValueError("El DNI debe tener exactamente 8 dígitos numéricos")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    nombre: str
    dni: str
    email: str
    colectivo: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


# Proposals

class ProposalCreate(BaseModel):
    titulo: str
    descripcion: str
    contenido: str


class ProposalOut(BaseModel):
    id: int
    titulo: str
    descripcion: str
    estado: str
    firmas_count: int
    porcentaje_firmas: float
    dias_restantes: int
    hash_congelamiento: Optional[str]
    tracking_congreso: Optional[str]
    autor_id: int
    created_at: datetime
    deadline: Optional[datetime]
    congelada_at: Optional[datetime]
    autor_nombre: Optional[str] = None
    autor_colectivo: Optional[str] = None
    ya_firme: bool = False

    model_config = {"from_attributes": True}


class ProposalDetail(ProposalOut):
    contenido: str


# Signatures

class SignatureOut(BaseModel):
    id: int
    proposal_id: int
    user_id: int
    timestamp: datetime
    hash_firma: str

    model_config = {"from_attributes": True}


# Resources

class ResourceCreate(BaseModel):
    tipo: str
    contenido: str
    parent_id: Optional[int] = None

    @field_validator("tipo")
    @classmethod
    def tipo_valido(cls, v: str) -> str:
        allowed = {"comentario", "documento", "modificacion"}
        if v not in allowed:
            raise ValueError(f"tipo debe ser uno de: {allowed}")
        return v


class ResourceOut(BaseModel):
    id: int
    proposal_id: int
    user_id: int
    tipo: str
    contenido: str
    parent_id: Optional[int]
    created_at: datetime
    autor_nombre: Optional[str] = None
    children: list["ResourceOut"] = []

    model_config = {"from_attributes": True}


ResourceOut.model_rebuild()
