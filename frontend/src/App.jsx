import { useEffect, useMemo, useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const emptyBot = {
  name: '',
  shopee_app_id: '',
  shopee_secret: '',
  telegram_token: '',
  telegram_channel_id: '',
  status: true,
  post_interval_seconds: 1200,
  fetch_interval_seconds: 60,
  error_retry_seconds: 30
}

export function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '')
  const [authMode, setAuthMode] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [bots, setBots] = useState([])
  const [form, setForm] = useState(emptyBot)
  const [selectedBot, setSelectedBot] = useState(null)
  const [sentProducts, setSentProducts] = useState([])

  const authHeaders = useMemo(() => ({ Authorization: `Bearer ${token}` }), [token])

  async function handleAuth(e) {
    e.preventDefault()
    const endpoint = authMode === 'login' ? '/auth/login' : '/auth/register'
    const res = await fetch(`${API_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    })
    if (!res.ok) return alert('Falha na autenticação')
    const data = await res.json()
    localStorage.setItem('token', data.access_token)
    setToken(data.access_token)
  }

  async function loadBots() {
    const res = await fetch(`${API_URL}/bots`, { headers: authHeaders })
    if (res.ok) setBots(await res.json())
  }

  useEffect(() => {
    if (token) loadBots()
  }, [token])

  async function saveBot(e) {
    e.preventDefault()
    const payload = { ...form }
    const endpoint = selectedBot ? `/bots/${selectedBot.id}` : '/bots'
    const method = selectedBot ? 'PUT' : 'POST'

    const res = await fetch(`${API_URL}${endpoint}`, {
      method,
      headers: { ...authHeaders, 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    if (!res.ok) return alert('Erro ao salvar bot')
    setForm(emptyBot)
    setSelectedBot(null)
    loadBots()
  }

  async function toggleBot(id) {
    await fetch(`${API_URL}/bots/${id}/toggle`, { method: 'PATCH', headers: authHeaders })
    loadBots()
  }

  async function loadSent(botId) {
    const res = await fetch(`${API_URL}/bots/${botId}/sent-products`, { headers: authHeaders })
    if (res.ok) setSentProducts(await res.json())
  }

  if (!token) {
    return (
      <main className="auth-wrapper">
        <form className="card" onSubmit={handleAuth}>
          <h1>Shopee SaaS</h1>
          <p>Automação multiusuário de ofertas Shopee no Telegram.</p>
          <input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input placeholder="Senha" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <button type="submit">{authMode === 'login' ? 'Entrar' : 'Criar conta'}</button>
          <button type="button" className="ghost" onClick={() => setAuthMode(authMode === 'login' ? 'register' : 'login')}>
            {authMode === 'login' ? 'Não tenho conta' : 'Já tenho conta'}
          </button>
        </form>
      </main>
    )
  }

  return (
    <main className="dashboard">
      <section className="card">
        <h2>{selectedBot ? 'Editar Bot' : 'Novo Bot'}</h2>
        <form className="grid" onSubmit={saveBot}>
          {Object.keys(emptyBot).map((field) => (
            <label key={field}>
              <span>{field}</span>
              <input
                value={form[field]}
                type={typeof emptyBot[field] === 'number' ? 'number' : 'text'}
                onChange={(e) => setForm({ ...form, [field]: typeof emptyBot[field] === 'number' ? Number(e.target.value) : e.target.value })}
              />
            </label>
          ))}
          <button type="submit">Salvar</button>
        </form>
      </section>

      <section className="card">
        <h2>Meus Bots</h2>
        <div className="list">
          {bots.map((bot) => (
            <article key={bot.id} className="bot-item">
              <div>
                <h3>{bot.name}</h3>
                <p>Status: {bot.status ? 'Ativo' : 'Inativo'}</p>
                <p>Última execução: {bot.last_run_at || 'Ainda não executado'}</p>
              </div>
              <div className="actions">
                <button onClick={() => { setSelectedBot(bot); setForm({ ...form, ...bot }) }}>Editar</button>
                <button onClick={() => toggleBot(bot.id)}>{bot.status ? 'Desativar' : 'Ativar'}</button>
                <button onClick={() => loadSent(bot.id)}>Últimos envios</button>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="card">
        <h2>Produtos enviados</h2>
        <ul>
          {sentProducts.map((p) => (
            <li key={p.id}>{p.product_link} — {new Date(p.created_at).toLocaleString()}</li>
          ))}
        </ul>
      </section>
    </main>
  )
}
