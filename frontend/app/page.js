'use client';

import { useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function Home() {
  const [token, setToken] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [bots, setBots] = useState([]);

  const [form, setForm] = useState({
    shopee_app_id: '',
    shopee_secret: '',
    telegram_token: '',
    telegram_channel_id: '',
    status: true,
    post_interval_seconds: 1200,
    fetch_interval_seconds: 60,
    error_retry_seconds: 30,
  });

  async function auth(path) {
    const res = await fetch(`${API}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (data.access_token) setToken(data.access_token);
    else alert(data.detail || 'Erro na autenticação');
  }

  async function loadBots() {
    if (!token) return;
    const res = await fetch(`${API}/bots`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    setBots(Array.isArray(data) ? data : []);
  }

  async function createBot() {
    const res = await fetch(`${API}/bots`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(form),
    });
    if (!res.ok) {
      const err = await res.json();
      alert(err.detail || 'Erro ao criar bot');
      return;
    }
    setForm({ ...form, shopee_secret: '', telegram_token: '' });
    loadBots();
  }

  async function toggleBot(bot) {
    await fetch(`${API}/bots/${bot.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ status: !bot.status }),
    });
    loadBots();
  }

  useEffect(() => {
    loadBots();
  }, [token]);

  return (
    <main style={{ fontFamily: 'sans-serif', maxWidth: 900, margin: '40px auto' }}>
      <h1>Shopee Telegram SaaS</h1>
      <p>Cadastro, login e gerenciamento de bots.</p>

      <section style={{ border: '1px solid #ddd', padding: 16, marginBottom: 20 }}>
        <h2>Autenticação</h2>
        <input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />{' '}
        <input placeholder="Senha" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />{' '}
        <button onClick={() => auth('/auth/register')}>Criar conta</button>{' '}
        <button onClick={() => auth('/auth/login')}>Login</button>
      </section>

      {token && (
        <>
          <section style={{ border: '1px solid #ddd', padding: 16, marginBottom: 20 }}>
            <h2>Novo bot</h2>
            {Object.keys(form).map((k) => (
              <div key={k} style={{ marginBottom: 8 }}>
                <label>{k}: </label>
                <input
                  value={String(form[k])}
                  onChange={(e) =>
                    setForm((prev) => ({
                      ...prev,
                      [k]:
                        k.includes('seconds')
                          ? Number(e.target.value)
                          : k === 'status'
                          ? e.target.value === 'true'
                          : e.target.value,
                    }))
                  }
                />
              </div>
            ))}
            <button onClick={createBot}>Salvar bot</button>
          </section>

          <section style={{ border: '1px solid #ddd', padding: 16 }}>
            <h2>Bots</h2>
            <button onClick={loadBots}>Atualizar</button>
            <ul>
              {bots.map((b) => (
                <li key={b.id} style={{ marginBottom: 12 }}>
                  <b>Bot #{b.id}</b> | app: {b.shopee_app_id} | canal: {b.telegram_channel_id} | status:{' '}
                  {String(b.status)} | última execução: {b.last_run_at || 'N/A'}{' '}
                  <button onClick={() => toggleBot(b)}>{b.status ? 'Desativar' : 'Ativar'}</button>
                </li>
              ))}
            </ul>
          </section>
        </>
      )}
    </main>
  );
}
