import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'

export default function Register() {
  const [form, setForm] = useState({ nombre: '', dni: '', email: '', password: '', colectivo: '' })
  const [error, setError] = useState('')
  const { login } = useAuth()
  const navigate = useNavigate()
  const set = k => e => setForm({ ...form, [k]: e.target.value })

  const submit = async e => {
    e.preventDefault()
    setError('')
    try {
      const { data } = await api.post('/auth/register', form)
      login(data.access_token, data.user)
      navigate('/')
    } catch (err) {
      const detail = err.response?.data?.detail
      setError(Array.isArray(detail) ? detail.map(d => d.msg).join(', ') : detail || 'Error al registrarse')
    }
  }

  return (
    <div className="container" style={{ maxWidth: 460 }}>
      <div className="card">
        <h2>Registrarse</h2>
        {error && <p className="error">{error}</p>}
        <form onSubmit={submit}>
          <label>Nombre completo</label>
          <input required value={form.nombre} onChange={set('nombre')} />
          <label>DNI (8 dígitos)</label>
          <input required maxLength={8} value={form.dni} onChange={set('dni')} />
          <label>Correo electrónico</label>
          <input type="email" required value={form.email} onChange={set('email')} />
          <label>Contraseña</label>
          <input type="password" required value={form.password} onChange={set('password')} />
          <label>Colectivo civil (opcional)</label>
          <input value={form.colectivo} onChange={set('colectivo')} />
          <button className="btn btn-primary" style={{ width: '100%' }}>Crear cuenta</button>
        </form>
        <p style={{ marginTop: 12, fontSize: '0.85rem', textAlign: 'center' }}>
          ¿Ya tienes cuenta? <Link to="/login">Ingresar</Link>
        </p>
      </div>
    </div>
  )
}
