import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const { login } = useAuth()
  const navigate = useNavigate()

  const submit = async e => {
    e.preventDefault()
    setError('')
    try {
      const { data } = await api.post('/auth/login', form)
      login(data.access_token, data.user)
      navigate('/')
    } catch (err) {
      const detail = err.response?.data?.detail
      setError(Array.isArray(detail) ? detail.map(d => d.msg).join(', ') : detail || 'Error al ingresar')
    }
  }

  return (
    <div className="container" style={{ maxWidth: 420 }}>
      <div className="card">
        <h2>Ingresar</h2>
        {error && <p className="error">{error}</p>}
        <form onSubmit={submit}>
          <label>Correo electrónico</label>
          <input type="email" required value={form.email}
            onChange={e => setForm({ ...form, email: e.target.value })} />
          <label>Contraseña</label>
          <input type="password" required value={form.password}
            onChange={e => setForm({ ...form, password: e.target.value })} />
          <button className="btn btn-primary" style={{ width: '100%' }}>Ingresar</button>
        </form>
        <p style={{ marginTop: 12, fontSize: '0.85rem', textAlign: 'center' }}>
          ¿No tienes cuenta? <Link to="/register">Regístrate</Link>
        </p>
      </div>
    </div>
  )
}
