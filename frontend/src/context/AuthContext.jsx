import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Read backend URL from env or use default local port 8000
  const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      fetch(`${API_URL}/api/me`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      .then(res => {
        if (res.ok) return res.json();
        throw new Error('Unauthorized');
      })
      .then(data => setUser(data))
      .catch(() => {
        localStorage.removeItem('token');
        setUser(null);
      })
      .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [API_URL]);

  const login = async (email, password) => {
    const res = await fetch(`${API_URL}/api/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email, password })
    });

    if (!res.ok) {
        let errorMessage = 'Login failed';
        try {
            const errorData = await res.json();
            if (typeof errorData.detail === 'string') {
                errorMessage = errorData.detail;
            } else if (Array.isArray(errorData.detail)) {
                errorMessage = errorData.detail.map(e => e.msg).join(', ');
            } else if (typeof errorData.detail === 'object') {
                errorMessage = JSON.stringify(errorData.detail);
            }
        } catch(e) {}
        throw new Error(errorMessage);
    }

    const data = await res.json();
    localStorage.setItem('token', data.access_token);
    setUser({ email }); // For now, just set email as user until /me is implemented
  };

  const signup = async (email, password, fullName) => {
    const res = await fetch(`${API_URL}/api/signup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email, password, name: fullName })
    });

    if (!res.ok) {
        let errorMessage = 'Signup failed';
        try {
            const errorData = await res.json();
            if (typeof errorData.detail === 'string') {
                errorMessage = errorData.detail;
            } else if (Array.isArray(errorData.detail)) {
                errorMessage = errorData.detail.map(e => e.msg).join(', ');
            } else if (typeof errorData.detail === 'object') {
                errorMessage = JSON.stringify(errorData.detail);
            }
        } catch(e) {}
        throw new Error(errorMessage);
    }

    return await res.json();
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
