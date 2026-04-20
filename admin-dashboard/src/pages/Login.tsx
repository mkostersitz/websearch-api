import React, { useState } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  InputAdornment,
  Divider,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  Key as KeyIcon,
  Lock as LockIcon,
} from '@mui/icons-material';

interface LoginProps {
  onLoginSuccess: (apiKey: string) => void;
}

const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // First login flow
  const [showChangePassword, setShowChangePassword] = useState(false);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  // API Key display
  const [showApiKey, setShowApiKey] = useState(false);
  const [generatedApiKey, setGeneratedApiKey] = useState('');

  const handleLogin = async () => {
    setError(null);
    setLoading(true);

    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Login failed');
      }

      const data = await response.json();

      if (data.first_login) {
        // First login - prompt for password change
        setShowChangePassword(true);
      } else {
        // Regular login - create/fetch API key
        await createAdminKey(username, password);
      }
    } catch (err: any) {
      setError(err.message || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async () => {
    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const response = await fetch('/api/v1/auth/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username,
          old_password: password,
          new_password: newPassword,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Password change failed');
      }

      // Password changed successfully, now create admin key
      setPassword(newPassword); // Update to new password
      await createAdminKey(username, newPassword);
      setShowChangePassword(false);
    } catch (err: any) {
      setError(err.message || 'Failed to change password');
    } finally {
      setLoading(false);
    }
  };

  const createAdminKey = async (user: string, pass: string) => {
    try {
      const response = await fetch('/api/v1/auth/create-admin-key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: user,
          password: pass,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to create API key');
      }

      const data = await response.json();
      
      // Check if this is an existing API key
      if (data.existing) {
        // User already has an API key - just continue to dashboard with masked key
        // We'll need to fetch the actual key from storage or let them use the existing one
        setError("You already have an active API key. If you lost it, please revoke it and create a new one.");
        setLoading(false);
        // For now, we'll allow them to continue but they need to use their stored key
        // TODO: Add a "revoke and regenerate" flow
        return;
      }
      
      setGeneratedApiKey(data.api_key);
      setShowApiKey(true);
    } catch (err: any) {
      setError(err.message || 'Failed to create admin API key');
    }
  };

  const handleContinueToDashboard = () => {
    onLoginSuccess(generatedApiKey);
  };

  const handleCopyApiKey = () => {
    navigator.clipboard.writeText(generatedApiKey);
  };

  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 8, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        {/* Logo/Header */}
        <Box sx={{ mb: 4, textAlign: 'center' }}>
          <KeyIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
          <Typography variant="h3" gutterBottom>
            WebSearch API
          </Typography>
          <Typography variant="h5" color="text.secondary">
            Admin Dashboard
          </Typography>
        </Box>

        {/* Login Form */}
        <Paper sx={{ p: 4, width: '100%' }}>
          <Typography variant="h6" gutterBottom>
            Sign In
          </Typography>
          <Divider sx={{ mb: 3 }} />

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <TextField
            fullWidth
            label="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            margin="normal"
            autoComplete="username"
            autoFocus
            disabled={loading}
          />

          <TextField
            fullWidth
            label="Password"
            type={showPassword ? 'text' : 'password'}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            margin="normal"
            autoComplete="current-password"
            disabled={loading}
            onKeyPress={(e) => {
              if (e.key === 'Enter') handleLogin();
            }}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => setShowPassword(!showPassword)}
                    edge="end"
                  >
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          <Button
            fullWidth
            variant="contained"
            size="large"
            onClick={handleLogin}
            disabled={loading || !username || !password}
            sx={{ mt: 3 }}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </Button>

          <Box sx={{ mt: 3, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
            <Typography variant="caption" display="block" gutterBottom>
              <strong>Default Credentials:</strong>
            </Typography>
            <Typography variant="caption" display="block">
              Username: <code>admin</code>
            </Typography>
            <Typography variant="caption" display="block">
              Password: <code>admin</code>
            </Typography>
            <Typography variant="caption" display="block" sx={{ mt: 1, fontStyle: 'italic' }}>
              You'll be prompted to change the password on first login.
            </Typography>
          </Box>
        </Paper>

        {/* Change Password Dialog */}
        <Dialog open={showChangePassword} maxWidth="sm" fullWidth>
          <DialogTitle>
            <LockIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Change Password
          </DialogTitle>
          <DialogContent>
            <Alert severity="warning" sx={{ mb: 2 }}>
              This is your first login. Please set a secure password.
            </Alert>

            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            <TextField
              fullWidth
              label="New Password"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              margin="normal"
              helperText="Minimum 8 characters"
            />

            <TextField
              fullWidth
              label="Confirm New Password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              margin="normal"
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={handleChangePassword} variant="contained" disabled={loading}>
              {loading ? 'Changing...' : 'Change Password'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* API Key Display Dialog */}
        <Dialog open={showApiKey} maxWidth="sm" fullWidth disableEscapeKeyDown>
          <DialogTitle>
            <KeyIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Your Admin API Key
          </DialogTitle>
          <DialogContent>
            <Alert severity="success" sx={{ mb: 2 }}>
              Your admin API key has been generated successfully!
            </Alert>

            <Alert severity="warning" sx={{ mb: 2 }}>
              <strong>Important:</strong> This key will only be shown once. Please copy and store it securely.
            </Alert>

            <Paper
              sx={{
                p: 2,
                bgcolor: 'grey.100',
                fontFamily: 'monospace',
                wordBreak: 'break-all',
                mb: 2,
              }}
            >
              {generatedApiKey}
            </Paper>

            <Button
              fullWidth
              variant="outlined"
              onClick={handleCopyApiKey}
              sx={{ mb: 2 }}
            >
              Copy to Clipboard
            </Button>

            <Typography variant="body2" color="text.secondary">
              This key has been automatically saved to your browser. You can now access the dashboard.
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleContinueToDashboard} variant="contained" size="large">
              Continue to Dashboard
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </Container>
  );
};

export default Login;
