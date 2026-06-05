import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'

const LIMITE = 25000

function ResourceNode({ r, depth = 0 }) {
  const [reply, setReply] = useState(false)
  const [text, setText] = useState('')
  const { user } = useAuth()

  const postReply = async () => {
    if (!text.trim()) return
    await api.post(`/proposals/${r.proposal_id}/resources`, { tipo: 'comentario', contenido: text, parent_id: r.id })
    window.location.reload()
  }

  return (
    <div style={{ marginLeft: depth * 16 }}>
      <div className="resource-item">
        <span className="badge" style={{ background: '#eee', color: '#555', marginRight: 8 }}>{r.tipo}</span>
        <strong style={{ fontSize: '0.8rem' }}>{r.autor_nombre}</strong>
        <p style={{ fontSize: '0.9rem', marginTop: 4 }}>{r.contenido}</p>
        {user && <button className="btn btn-secondary" style={{ marginTop: 6, padding: '2px 10px', fontSize: '0.8rem' }}
          onClick={() => setReply(!reply)}>Responder</button>}
        {reply && (
          <div style={{ marginTop: 8 }}>
            <textarea style={{ minHeight: 60, marginBottom: 6 }} value={text} onChange={e => setText(e.target.value)} />
            <button className="btn btn-primary" style={{ padding: '4px 12px' }} onClick={postReply}>Enviar</button>
          </div>
        )}
      </div>
      {r.children?.map(c => <ResourceNode key={c.id} r={c} depth={depth + 1} />)}
    </div>
  )
}

export default function ProposalDetail() {
  const { id } = useParams()
  const { user } = useAuth()
  const [proposal, setProposal] = useState(null)
  const [resources, setResources] = useState([])
  const [newResource, setNewResource] = useState({ tipo: 'comentario', contenido: '' })
  const [msg, setMsg] = useState('')

  const load = () => {
    api.get(`/proposals/${id}`).then(r => setProposal(r.data))
    api.get(`/proposals/${id}/resources`).then(r => setResources(r.data))
  }

  useEffect(() => { load() }, [id])

  const sign = async () => {
    try {
      await api.post(`/proposals/${id}/sign`)
      setMsg('¡Firma registrada exitosamente!')
      load()
    } catch (err) {
      setMsg(err.response?.data?.detail || 'Error al firmar')
    }
  }

  const freeze = async () => {
    try {
      await api.post(`/proposals/${id}/freeze`)
      setMsg('Propuesta congelada y enviada al Congreso.')
      load()
    } catch (err) {
      setMsg(err.response?.data?.detail || 'Error')
    }
  }

  const addResource = async e => {
    e.preventDefault()
    if (!newResource.contenido.trim()) return
    await api.post(`/proposals/${id}/resources`, newResource)
    setNewResource({ tipo: 'comentario', contenido: '' })
    load()
  }

  if (!proposal) return <div className="container"><p>Cargando...</p></div>

  return (
    <div className="container">
      <div className="card">
        <div className="row" style={{ marginBottom: 10 }}>
          <h1 style={{ flex: 1, fontSize: '1.4rem' }}>{proposal.titulo}</h1>
          <span className={`badge badge-${proposal.estado}`}>{proposal.estado}</span>
        </div>
        <p style={{ color: '#555', marginBottom: 12 }}>{proposal.descripcion}</p>

        <div className="progress-bar">
          <div className="progress-bar-fill" style={{ width: `${proposal.porcentaje_firmas}%` }} />
        </div>
        <div className="row" style={{ fontSize: '0.85rem', color: '#555', marginBottom: 16 }}>
          <span><strong>{proposal.firmas_count.toLocaleString()}</strong> / {LIMITE.toLocaleString()} firmas</span>
          <span className="spacer" />
          {proposal.estado === 'activa' && <span>{proposal.dias_restantes} días restantes</span>}
          <span>por <strong>{proposal.autor_nombre}</strong> {proposal.autor_colectivo && `· ${proposal.autor_colectivo}`}</span>
        </div>

        {proposal.hash_congelamiento && (
          <div className="hash-box">
            <strong>Hash SHA-256 (congelamiento criptográfico):</strong><br />{proposal.hash_congelamiento}
            {proposal.tracking_congreso && <><br /><strong>Tracking Congreso:</strong> {proposal.tracking_congreso}</>}
          </div>
        )}

        {msg && <p style={{ margin: '12px 0', fontWeight: 'bold', color: msg.includes('Error') || msg.includes('Ya') ? '#c0392b' : '#1e8449' }}>{msg}</p>}

        {user && proposal.estado === 'activa' && !proposal.ya_firme && (
          <button className="btn btn-primary" style={{ marginTop: 8 }} onClick={sign}>Firmar esta propuesta</button>
        )}
        {proposal.ya_firme && <p style={{ color: '#1e8449', marginTop: 8 }}>Ya has firmado esta propuesta</p>}
        {user && user.id === proposal.autor_id && proposal.estado === 'activa' && (
          <button className="btn btn-secondary" style={{ marginLeft: 10 }} onClick={freeze}>Congelar manualmente</button>
        )}
      </div>

      <div className="card">
        <h2>Texto completo</h2>
        <pre style={{ whiteSpace: 'pre-wrap', fontSize: '0.9rem', color: '#333' }}>{proposal.contenido}</pre>
      </div>

      <div className="card">
        <h2>Recursos de apoyo</h2>
        {resources.length === 0 && <p style={{ color: '#888', marginBottom: 12 }}>Sin recursos aún.</p>}
        {resources.map(r => <ResourceNode key={r.id} r={r} />)}

        {user && (
          <form onSubmit={addResource} style={{ marginTop: 16, borderTop: '1px solid #eee', paddingTop: 14 }}>
            <div className="row" style={{ marginBottom: 6 }}>
              <label style={{ marginRight: 8 }}>Tipo:</label>
              <select style={{ width: 160, margin: 0 }} value={newResource.tipo}
                onChange={e => setNewResource({ ...newResource, tipo: e.target.value })}>
                <option value="comentario">Comentario</option>
                <option value="documento">Documento</option>
                <option value="modificacion">Modificación propuesta</option>
              </select>
            </div>
            <textarea style={{ minHeight: 70 }} placeholder="Escribe tu aporte..."
              value={newResource.contenido}
              onChange={e => setNewResource({ ...newResource, contenido: e.target.value })} />
            <button className="btn btn-primary">Agregar</button>
          </form>
        )}
      </div>
    </div>
  )
}
