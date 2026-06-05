import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'

const LIMITE = 25000

export default function Home() {
  const [proposals, setProposals] = useState([])
  const [q, setQ] = useState('')
  const [estado, setEstado] = useState('')

  useEffect(() => {
    api.get('/proposals', { params: { q: q || undefined, estado: estado || undefined } })
      .then(r => setProposals(r.data))
      .catch(() => {})
  }, [q, estado])

  return (
    <div className="container">
      <h1>Iniciativas Legislativas Ciudadanas</h1>
      <div className="row" style={{ marginBottom: 16 }}>
        <input style={{ flex: 1, margin: 0 }} placeholder="Buscar propuesta..."
          value={q} onChange={e => setQ(e.target.value)} />
        <select style={{ width: 160, margin: 0 }} value={estado} onChange={e => setEstado(e.target.value)}>
          <option value="">Todos los estados</option>
          <option value="activa">Activa</option>
          <option value="congelada">Congelada</option>
          <option value="enviada">Enviada al Congreso</option>
          <option value="expirada">Expirada</option>
        </select>
      </div>

      {proposals.length === 0 && <p style={{ color: '#888' }}>No hay propuestas aún.</p>}

      {proposals.map(p => (
        <Link to={`/proposals/${p.id}`} key={p.id} style={{ textDecoration: 'none', color: 'inherit' }}>
          <div className="card" style={{ cursor: 'pointer' }}>
            <div className="row" style={{ marginBottom: 6 }}>
              <strong style={{ flex: 1 }}>{p.titulo}</strong>
              <span className={`badge badge-${p.estado}`}>{p.estado}</span>
            </div>
            <p style={{ fontSize: '0.9rem', color: '#555', marginBottom: 10 }}>{p.descripcion}</p>
            <div className="progress-bar">
              <div className="progress-bar-fill" style={{ width: `${p.porcentaje_firmas}%` }} />
            </div>
            <div className="row" style={{ fontSize: '0.82rem', color: '#666' }}>
              <span>{p.firmas_count.toLocaleString()} / {LIMITE.toLocaleString()} firmas ({p.porcentaje_firmas}%)</span>
              <span className="spacer" />
              {p.estado === 'activa' && <span>{p.dias_restantes} días restantes</span>}
              <span>por {p.autor_nombre}</span>
            </div>
          </div>
        </Link>
      ))}
    </div>
  )
}
