import { Routes, Route, Link, useNavigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import CreateProposal from './pages/CreateProposal'
import ProposalDetail from './pages/ProposalDetail'

function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  return (
    <nav>
      <Link to="/">Voz del Ciudadano</Link>
      <span className="spacer" />
      {user ? (
        <>
          <Link to="/proposals/new">+ Nueva Propuesta</Link>
          <span style={{ opacity: 0.8 }}>Hola, {user.nombre}</span>
          <button className="btn btn-secondary" style={{ padding: '4px 12px' }}
            onClick={() => { logout(); navigate('/') }}>Salir</button>
        </>
      ) : (
        <>
          <Link to="/login">Ingresar</Link>
          <Link to="/register">Registrarse</Link>
        </>
      )}
    </nav>
  )
}

export default function App() {
  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/proposals/new" element={<CreateProposal />} />
        <Route path="/proposals/:id" element={<ProposalDetail />} />
      </Routes>
    </>
  )
}
