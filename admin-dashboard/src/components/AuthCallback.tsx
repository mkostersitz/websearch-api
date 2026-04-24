import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, CircularProgress, Typography } from '@mui/material';

const AuthCallback: React.FC = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // The actual token exchange is handled by the OIDC library or backend.
    // For now, just redirect home after a short delay.
    const timer = setTimeout(() => navigate('/'), 1000);
    return () => clearTimeout(timer);
  }, [navigate]);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mt: 10, gap: 2 }}>
      <CircularProgress />
      <Typography>Completing sign-in…</Typography>
    </Box>
  );
};

export default AuthCallback;
