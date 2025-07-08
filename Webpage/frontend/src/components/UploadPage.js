import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './UploadPage.css';

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [msg, setMsg] = useState('');

  const submit = async e => {
    e.preventDefault();

    if (!file) {
      setMsg('Please choose a CSV file.');
      return;
    }

    const data = new FormData();
    data.append('file', file);

    try {
      const res = await fetch('https://sih-project-1647-team-xebecs-crew.onrender.com', {
        method: 'POST',
        body: data
      });

      if (res.ok) {
        const json = await res.json();
        setMsg(`Upload successful! Stored as: ${json.filename}`);
      } else {
        const err = await res.json().catch(() => ({}));
        setMsg(`Upload failed: ${err.error || res.statusText}`);
      }
    } catch (err) {
      setMsg('Upload failed: network or CORS error');
    }
  };

  return (
    <div className="container">
      <h1 className="title">
        Crop Price Predictor using LSTM &amp; CNN (SIH 1647 Project)
      </h1>

      <p className="subtitle">
        Upload your crop price dataset (CSV format) below:
      </p>

      <form onSubmit={submit}>
        <input
          type="file"
          accept=".csv"
          onChange={e => {
            setFile(e.target.files[0]);
            setMsg('');
          }}
        />

        <button type="submit" className="submit">
          Submit Dataset
        </button>
      </form>

      {msg && <p className="description">{msg}</p>}

      <div className="results-link">
        <Link to="/results">Go to Results Page</Link>
      </div>

      <div className="admin-link">
        <Link to="/admin/login">Admin Login</Link>
      </div>
    </div>
  );
}
