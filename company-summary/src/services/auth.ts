export async function validateCredentials(username: string, password: string): Promise<boolean> {
  try {
    const authMode = import.meta.env.VITE_AUTH_MODE || 'local';

    // Local development mode - use hardcoded credentials
    if (authMode === 'local') {
      const devUsername = import.meta.env.VITE_DEV_USERNAME || 'admin';
      const devPassword = import.meta.env.VITE_DEV_PASSWORD || 'password123';
      
      console.warn('Using local development credentials');
      return username === devUsername && password === devPassword;
    }

    // API mode - call Lambda authentication endpoint
    if (authMode === 'api') {
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;
      
      if (!apiBaseUrl) {
        throw new Error('VITE_API_BASE_URL not configured for API mode');
      }

      const response = await fetch(`${apiBaseUrl}/auth`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password })
      });

      if (!response.ok) {
        console.error('Authentication API error:', response.status, response.statusText);
        return false;
      }

      const result = await response.json();
      return result.valid === true;
    }

    throw new Error(`Unknown auth mode: ${authMode}`);

  } catch (error) {
    console.error('Failed to validate credentials:', error);
    return false;
  }
}