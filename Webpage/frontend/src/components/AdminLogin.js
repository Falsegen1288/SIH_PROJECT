// src/components/AdminLogin.js

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './AdminLogin.css'; // 👈 Import the CSS file

const USER = 'admin';
const PASS = 'secret123';

export default function AdminLogin() {
  const [u, setU] = useState('');
  const [p, setP] = useState('');
  const [err, setErr] = useState('');
  const nav = useNavigate();

  const submit = e => {
    e.preventDefault();
    if (u === USER && p === PASS) {
      sessionStorage.setItem('isAdmin', '1');
      nav('/admin/panel');
    } else {
      setErr('Invalid credentials');
    }
  };

  return (
    <div className="login-container">
      <form onSubmit={submit} className="login-box">
        <h2>Admin Login</h2>
        <input
          placeholder="Username"
          value={u}
          onChange={e => setU(e.target.value)}
        /><br />
        <input
          placeholder="Password"
          type="password"
          value={p}
          onChange={e => setP(e.target.value)}
        /><br />
        <button type="submit">Login</button>
        {err && <p className="error">{err}</p>}
      </form>
    </div>
  );
}
