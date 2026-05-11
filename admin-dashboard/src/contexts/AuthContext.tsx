import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';

interface User {
  user_id: string;
  email: string;
  name: string;
  groups: string[];
  auth_method: 'entra_id' | 'local' | 'api_key';
}

interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  sessionToken: string | null;
  apiKey: string | null;
  login: (token: string, userData: User) => void;
  loginWithApiKey: (apiKey: string) => void;
  logout: () => void;
  refreshToken: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const navigate = useNavigate();

  // Load auth state from localStorage on mount
  useEffect(() => {
    const storedSessionToken = localStorage.getItem('session_token');
    const storedApiKey = localStorage.getItem('api_key');
    const storedUser = localStorage.getItem('user');

    if (storedSessionToken && storedUser) {
      // OAuth session authentication
      try {
        const userData = JSON.parse(storedUser);
        setSessionToken(storedSessionToken);
        setUser(userData);
        setIsAuthenticated(true);
      } catch (err) {
        console.error('Failed to parse stored user data:', err);
        localStorage.removeItem('session_token');
        localStorage.removeItem('user');
      }
    } else if (storedApiKey) {
      // API key authentication (legacy)
      setApiKey(storedApiKey);
      setIsAuthenticated(true);
      // For API key auth, we don't have full user data
      setUser({
        user_id: 'api-key-user',
        email: '',
        name: 'Admin',
        groups: ['admin'],
        auth_method: 'api_key',
      });
    }
  }, []);

  const login = (token: string, userData: User) => {
    setSessionToken(token);
    setUser(userData);
    setIsAuthenticated(true);
    localStorage.setItem('session_token', token);
    localStorage.setItem('user', JSON.stringify(userData));
    
    // Clear legacy API key if exists
    localStorage.removeItem('api_key');
    setApiKey(null);
  };

  const loginWithApiKey = (key: string) => {
    setApiKey(key);
    setIsAuthenticated(true);
    localStorage.setItem('api_key', key);
    
    // Set minimal user data for API key auth
    const apiKeyUser: User = {
      user_id: 'api-key-user',
      email: '',
      name: 'Admin',
      groups: ['admin'],
      auth_method: 'api_key',
    };
    setUser(apiKeyUser);
    
    // Clear OAuth session if exists
    localStorage.removeItem('session_token');
    localStorage.removeItem('user');
    setSessionToken(null);
  };

  const logout = async () => {
    try {
      // Call logout endpoint if using session token
      if (sessionToken) {
        await fetch('/api/v1/oauth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${sessionToken}`,
          },
        });
      }
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      // Clear all auth data
      setSessionToken(null);
      setApiKey(null);
      setUser(null);
      setIsAuthenticated(false);
      localStorage.removeItem('session_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('api_key');
      localStorage.removeItem('user');
      
      // Redirect to login
      navigate('/');
    }
  };

  const refreshToken = async (): Promise<boolean> => {
    const refreshTokenValue = localStorage.getItem('refresh_token');
    
    if (!refreshTokenValue) {
      return false;
    }

    try {
      const response = await fetch('/api/v1/oauth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          refresh_token: refreshTokenValue,
        }),
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const data = await response.json();
      
      // Update tokens
      setSessionToken(data.session_token);
      setUser(data.user);
      localStorage.setItem('session_token', data.session_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      
      return true;
    } catch (err) {
      console.error('Token refresh error:', err);
      // If refresh fails, logout user
      logout();
      return false;
    }
  };

  const value: AuthContextType = {
    isAuthenticated,
    user,
    sessionToken,
    apiKey,
    login,
    loginWithApiKey,
    logout,
    refreshToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
