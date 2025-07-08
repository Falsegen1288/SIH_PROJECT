// src/components/AdminPanel.js

import React, { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import './AdminPanel.css';
import { Link } from 'react-router-dom';

const BASE_URL = 'https://sih-project-1647-team-xebecs-crew.onrender.com';

export default function AdminPanel() {
  const [dataset, setDataset] = useState('');
  const [buy, setBuy] = useState('');
  const [sell, setSell] = useState('');
  const [msg, setMsg] = useState('');
  const [existing, setExisting] = useState([]);

  useEffect(() => {
    fetch(`${BASE_URL}/results`)
      .then(res => res.json())
      .then(data => setExisting(data))
      .catch(() => setMsg("Failed to load results from server"));
  }, []);

  const isAdmin = sessionStorage.getItem('isAdmin') === '1';
  if (!isAdmin) {
    return <Navigate to="/admin/login" replace />;
  }

  const submit = async (e) => {
    e.preventDefault();
    if (!dataset.trim()) {
      setMsg('Dataset name cannot be empty');
      return;
    }

    try {
      const res = await fetch(`${BASE_URL}/post-result`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: dataset, buy, sell })
      });

      if (res.ok) {
        setMsg('Result added!');
        const updated = await fetch(`${BASE_URL}/results`).then(r => r.json());
        setExisting(updated);
        setDataset(''); setBuy(''); setSell('');
      } else {
        const err = await res.json().catch(() => ({}));
        setMsg(`Error: ${err.error || res.statusText}`);
      }
    } catch (err) {
      setMsg('Network error while posting result');
    }
  };

  const handleDelete = async (id) => {
    const confirmDelete = window.confirm("Are you sure you want to delete this entry?");
    if (!confirmDelete) return;

    try {
      const resp = await fetch(`${BASE_URL}/delete-result/${id}`, {
        method: 'DELETE'
      });

      if (resp.ok) {
        setExisting(prev => prev.filter(r => r._id !== id));
      } else {
        alert("Failed to delete entry.");
      }
    } catch (err) {
      alert("Network error during delete.");
    }
  };

  return (
    <div className="admin-panel-container">
      <div className="admin-panel-box">
        <h2>Admin Panel</h2>

        <form onSubmit={submit}>
          <input
            placeholder="Dataset name"
            value={dataset}
            onChange={e => setDataset(e.target.value)}
          />
          <input
            placeholder="Buy date"
            value={buy}
            onChange={e => setBuy(e.target.value)}
          />
          <input
            placeholder="Sell date"
            value={sell}
            onChange={e => setSell(e.target.value)}
          />
          <button type="submit">Post Results</button>
        </form>

        {msg && <p className="status-msg">{msg}</p>}

        <Link to="/" className="green-button">
          Back
        </Link>

        <h3>Current Entries</h3>
        {existing.length === 0 ? (
          <p>No results yet.</p>
        ) : (
          <ul className="entry-list">
            {existing.map(r => (
              <li key={r._id}>
                <span>
                  <strong>{r.name}</strong> — Buy: {r.buy}, Sell: {r.sell}
                </span>
                <button onClick={() => handleDelete(r._id)}>Delete</button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
