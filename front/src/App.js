import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [message, setMessage] = useState('');

  useEffect(() => {
    // Replace with your backend URL when deployed
    const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
    fetch(backendUrl)
      .then(response => response.json())
      .then(data => setMessage(data.message))
      .catch(error => console.error('Error fetching data:', error));
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <p>
          Message from backend: {message}
        </p>
      </header>
    </div>
  );
}

export default App;