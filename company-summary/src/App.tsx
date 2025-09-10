import { useState, useEffect } from 'react';
import { Summary } from './pages/Summary';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already authenticated
    const authStatus = localStorage.getItem('isAuthenticated');
    if (authStatus === 'true') {
      setIsAuthenticated(true);
    }
    setLoading(false);
  }, []);

  const handleLogin = (username: string, _password: string) => {
    setIsAuthenticated(true);
    localStorage.setItem('isAuthenticated', 'true');
    localStorage.setItem('username', username);
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    localStorage.removeItem('isAuthenticated');
    localStorage.removeItem('username');
  };

  if (loading) {
    return null; // Or a loading spinner
  }

  return (
    <Summary 
      isAuthenticated={isAuthenticated} 
      onLogin={handleLogin}
      onLogout={handleLogout}
    />
  );
}

export default App
