// src/App.js
import React from 'react'
import Home from './components/home'
import ResultsPage from './components/ResultsPage'
import AdminLogin from './components/AdminLogin'
import AdminPanel from './components/AdminPanel'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'

function App() {
  return (
      <Router>
        <Routes>
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="/admin/panel" element={<AdminPanel />} />
          <Route path="/" element={<Home />} />
          <Route path="/results" element={<ResultsPage />} />
        </Routes>
      </Router>
  )
}

export default App
