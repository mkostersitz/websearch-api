import React, { useState } from 'react';
import { Button, CircularProgress } from '@mui/material';
import LockOpenIcon from '@mui/icons-material/LockOpen';
import { isKeycloakConfigured, KEYCLOAK_URL, KEYCLOAK_REALM, CLIENT_ID } from '../config/authConfig';

interface KeycloakLoginButtonProps {
  onError?: (error: Error) => void;
}

const KeycloakLoginButton: React.FC<KeycloakLoginButtonProps> = ({ onError }) => {
  const [loading, setLoading] = useState(false);

  if (!isKeycloakConfigured) {
    return null;
  }

  const handleLogin = () => {
    setLoading(true);
    try {
      const state = crypto.randomUUID();
      sessionStorage.setItem('oidc_state', state);
      const params = new URLSearchParams({
        client_id: CLIENT_ID,
        redirect_uri: window.location.origin + '/auth/callback',
        response_type: 'code',
        scope: 'openid profile email roles',
        state,
      });
      const authority = `${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}`;
      window.location.href = `${authority}/protocol/openid-connect/auth?${params}`;
    } catch (error) {
      console.error('Keycloak login error:', error);
      setLoading(false);
      if (onError && error instanceof Error) onError(error);
    }
  };

  return (
    <Button
      variant="outlined"
      size="large"
      fullWidth
      onClick={handleLogin}
      disabled={loading}
      startIcon={loading ? <CircularProgress size={20} /> : <LockOpenIcon />}
      sx={{
        borderColor: '#4d90fe',
        color: '#4d90fe',
        textTransform: 'none',
        fontSize: '16px',
        padding: '12px',
        '&:hover': { borderColor: '#357ae8', backgroundColor: 'rgba(77, 144, 254, 0.04)' },
      }}
    >
      {loading ? 'Redirecting...' : 'Sign in with Keycloak'}
    </Button>
  );
};

export default KeycloakLoginButton;
