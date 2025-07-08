import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import './ResultsPage.css';

export default function ResultsPage() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('https://sih-project-1647-team-xebecs-crew.onrender.com/results')
      .then(res => res.json())
      .then(data => {
        setResults(data);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
        alert("Failed to load results");
      });
  }, []);

  return (
    <div className="results-container">
      <div className="results-box">
        <h2>Predicted Results</h2>

        {loading ? (
          <p className="no-results">Loading...</p>
        ) : results.length === 0 ? (
          <p className="no-results">No results available.</p>
        ) : (
          <ul className="results-list">
            {results.map(r => (
              <li key={r._id}>
                <strong>Dataset:</strong> {r.name} <br />
                <strong>Buy:</strong> {r.buy} <br />
                <strong>Sell:</strong> {r.sell}
              </li>
            ))}
          </ul>
        )}

        <Link to="/" className="home-button">Back</Link>
      </div>
    </div>
  );
}
