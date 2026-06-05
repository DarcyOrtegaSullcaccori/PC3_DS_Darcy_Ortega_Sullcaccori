import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'

export default function CreateProposal() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ titulo: '', descripcion: '', contenido: '' })
  const [error, setError] = useState('')
  const set = k => e => setForm({ ...form, [k]: e.target.value })

  if (!user) return <div className="container"><p>Debes <a href="/login">ingresar</a> para crear una propuesta.</p></div>

  const submit = async e => {
    e.preventDefault()
    setError('')
    try {
      const { data } = await api.post('/proposals', form)
      navigate(`/proposals/${data.id}`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al crear la propuesta')
    }
  }

  return (
    <div className="container" style={{ maxWidth: 680 }}>
      <div className="card">
        <h2>Nueva Iniciativa Legislativa</h2>
        <p style={{ fontSize: '0.85rem', color: '#666', marginBottom: 16 }}>
          La propuesta necesita 25,000 firmas en 90 días para ser enviada al Congreso.
        </p>
        {error && <p className="error">{error}</p>}
        <form onSubmit={submit}>
          <label>Título de la propuesta</label>
          <input required value={form.titulo} onChange={set('titulo')} placeholder="Ej: Ley de protección ambiental..." />
          <label>Descripción breve</label>
          <textarea style={{ minHeight: 70 }} required value={form.descripcion} onChange={set('descripcion')}
            placeholder="Resumen en 2-3 oraciones" />
          <label>Contenido completo del proyecto de ley</label>
          <textarea style={{ minHeight: 180 }} required value={form.contenido} onChange={set('contenido')}
            placeholder="Articulado completo de la propuesta normativa..." />
          <div className="row" style={{ marginTop: 4 }}>
            <button className="btn btn-primary">Publicar Propuesta</button>
            <button className="btn btn-secondary" type="button" onClick={() => navigate('/')}>Cancelar</button>
          </div>
        </form>
      </div>
    </div>
  )
}
