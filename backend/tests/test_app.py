"""
Casos de Prueba — Voz del Ciudadano
CP-01: Registro con DNI inválido
CP-02: Firmar una propuesta dos veces
CP-03: Firmar sin autenticación
CP-04: Congelamiento automático al alcanzar el límite de firmas
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.pool import StaticPool
from database import Base, get_db
from main import app

# BD en memoria compartida entre conexiones (StaticPool)
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)

def override_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_db
client = TestClient(app)


def _registrar(dni: str, email: str) -> str:
    client.post("/auth/register", json={
        "nombre": "Usuario Test", "dni": dni,
        "email": email, "password": "pass1234"
    })
    r = client.post("/auth/login", json={"email": email, "password": "pass1234"})
    return r.json()["access_token"]

def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}

def _crear_propuesta(token: str) -> int:
    r = client.post("/proposals", json={
        "titulo": "Propuesta Test",
        "descripcion": "Descripción de prueba",
        "contenido": "Artículo 1: contenido de la propuesta."
    }, headers=_auth(token))
    return r.json()["id"]


# CP-01

def test_cp01_registro_dni_invalido():
    """DNI con 7 dígitos debe retornar error de validación (422)."""
    r = client.post("/auth/register", json={
        "nombre": "Test", "dni": "1234567",
        "email": "cp01@test.com", "password": "pass1234"
    })
    assert r.status_code == 422
    assert "DNI" in r.text


# CP-02

def test_cp02_doble_firma():
    """Un mismo usuario no puede firmar la misma propuesta dos veces (409)."""
    token_autor = _registrar("20000001", "autor_cp02@test.com")
    token_firma = _registrar("20000002", "firma_cp02@test.com")
    pid = _crear_propuesta(token_autor)

    r1 = client.post(f"/proposals/{pid}/sign", headers=_auth(token_firma))
    assert r1.status_code == 200

    r2 = client.post(f"/proposals/{pid}/sign", headers=_auth(token_firma))
    assert r2.status_code == 409
    assert "Ya has firmado" in r2.json()["detail"]


# CP-03

def test_cp03_firmar_sin_autenticacion():
    """Firmar sin token debe retornar 401 Unauthorized."""
    token = _registrar("30000001", "cp03@test.com")
    pid = _crear_propuesta(token)

    r = client.post(f"/proposals/{pid}/sign")
    assert r.status_code == 401


# CP-04

def test_cp04_congelamiento_automatico(monkeypatch):
    """Al alcanzar el límite de firmas la propuesta se congela y genera hash SHA-256."""
    import patterns.facade as facade_module
    monkeypatch.setattr(facade_module, "FIRMA_LIMITE", 1)

    token_autor = _registrar("40000001", "autor_cp04@test.com")
    token_firmante = _registrar("40000002", "firmante_cp04@test.com")
    pid = _crear_propuesta(token_autor)

    client.post(f"/proposals/{pid}/sign", headers=_auth(token_firmante))

    r = client.get(f"/proposals/{pid}")
    data = r.json()
    assert data["estado"] in ("congelada", "enviada")
    assert data["hash_congelamiento"] is not None
    assert len(data["hash_congelamiento"]) == 64  # SHA-256 hex
