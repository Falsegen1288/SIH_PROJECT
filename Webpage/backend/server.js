const express = require('express');
const path = require('path');
const app = express();

// Serve the React app build
app.use(express.static(path.join(__dirname, '../frontend/build')));

// All other routes → React index
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../frontend/build', 'index.html'));
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Static server running on http://localhost:${PORT}`);
});
