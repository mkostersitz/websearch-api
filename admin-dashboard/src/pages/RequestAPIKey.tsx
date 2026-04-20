import React, { useState } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  Snackbar,
  IconButton,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import {
  ContentCopy as CopyIcon,
  CheckCircle as CheckIcon,
  Key as KeyIcon,
} from '@mui/icons-material';

interface APIKeyResponse {
  api_key: string;
  user_id: string;
  username: string;
  email: string;
  name: string;
  groups: string[];
  quotas: {
    daily_limit: number;
    monthly_limit: number;
  };
  message: string;
}

const RequestAPIKey: React.FC = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [apiKeyData, setApiKeyData] = useState<APIKeyResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const handleRequestKey = async () => {
    if (!email || !email.includes('@')) {
      setError('Please enter a valid email address');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/auth/request-key', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to request API key');
      }

      const data = await response.json();
      setApiKeyData(data);
    } catch (err: any) {
      const errorMessage = err instanceof Error ? err.message : 
                          typeof err === 'string' ? err : 
                          'An error occurred';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyKey = () => {
    if (apiKeyData) {
      navigator.clipboard.writeText(apiKeyData.api_key);
      setCopied(true);
    }
  };

  const handleReset = () => {
    setEmail('');
    setApiKeyData(null);
    setError(null);
  };

  return (
    <Container maxWidth="md" sx={{ mt: 8, mb: 8 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <KeyIcon sx={{ fontSize: 40, mr: 2, color: 'primary.main' }} />
          <Typography variant="h4" component="h1">
            Request API Key
          </Typography>
        </Box>

        <Typography variant="body1" color="text.secondary" paragraph>
          Enter your email address to request an API key for the WebSearch API.
          Your email must be registered in the system.
        </Typography>

        {!apiKeyData ? (
          <Box sx={{ mt: 4 }}>
            <TextField
              fullWidth
              label="Email Address"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              error={!!error}
              helperText={error || undefined}
              disabled={loading}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleRequestKey();
                }
              }}
              sx={{ mb: 3 }}
            />

            <Button
              variant="contained"
              size="large"
              fullWidth
              onClick={handleRequestKey}
              disabled={loading || !email}
            >
              {loading ? 'Requesting...' : 'Request API Key'}
            </Button>

            <Alert severity="info" sx={{ mt: 3 }}>
              <Typography variant="body2">
                <strong>Note:</strong> You can only request an API key if your email
                is registered in the system. Contact your administrator if you need access.
              </Typography>
            </Alert>
          </Box>
        ) : (
          <Box sx={{ mt: 4 }}>
            <Alert severity="success" sx={{ mb: 3 }}>
              <Typography variant="body1" fontWeight="bold">
                {apiKeyData.message}
              </Typography>
            </Alert>

            <Paper variant="outlined" sx={{ p: 3, mb: 3, bgcolor: 'grey.50' }}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Your API Key
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography
                  variant="h6"
                  sx={{
                    fontFamily: 'monospace',
                    wordBreak: 'break-all',
                    flex: 1,
                  }}
                >
                  {apiKeyData.api_key}
                </Typography>
                <IconButton
                  color="primary"
                  onClick={handleCopyKey}
                  title="Copy to clipboard"
                >
                  {copied ? <CheckIcon /> : <CopyIcon />}
                </IconButton>
              </Box>
            </Paper>

            <Divider sx={{ my: 3 }} />

            <Typography variant="h6" gutterBottom>
              Account Information
            </Typography>

            <List>
              <ListItem>
                <ListItemText
                  primary="Name"
                  secondary={apiKeyData.name}
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="Email"
                  secondary={apiKeyData.email}
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="User ID"
                  secondary={apiKeyData.user_id}
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="Groups"
                  secondary={
                    <Box sx={{ mt: 1 }}>
                      {apiKeyData.groups.map((group) => (
                        <Chip
                          key={group}
                          label={group}
                          size="small"
                          sx={{ mr: 0.5, mb: 0.5 }}
                        />
                      ))}
                    </Box>
                  }
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="Quotas"
                  secondary={
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="body2">
                        • Daily: {apiKeyData.quotas.daily_limit.toLocaleString()} searches
                      </Typography>
                      <Typography variant="body2">
                        • Monthly: {apiKeyData.quotas.monthly_limit.toLocaleString()} searches
                      </Typography>
                    </Box>
                  }
                />
              </ListItem>
            </List>

            <Divider sx={{ my: 3 }} />

            <Alert severity="warning" sx={{ mb: 3 }}>
              <Typography variant="body2">
                <strong>Important:</strong> Store this API key securely. It won't be
                shown again. If you lose it, you'll need to request a new one.
              </Typography>
            </Alert>

            <Typography variant="h6" gutterBottom>
              How to Use Your API Key
            </Typography>

            <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.900', color: 'grey.100', mb: 3 }}>
              <Typography variant="body2" component="pre" sx={{ fontFamily: 'monospace', m: 0 }}>
{`# Example: Search request
curl -X POST http://localhost/api/v1/search \\
  -H "X-API-Key: ${apiKeyData.api_key}" \\
  -H "Content-Type: application/json" \\
  -d '{"query": "your search query", "max_results": 10}'`}
              </Typography>
            </Paper>

            <Button
              variant="outlined"
              fullWidth
              onClick={handleReset}
            >
              Request Another Key
            </Button>
          </Box>
        )}
      </Paper>

      <Snackbar
        open={copied}
        autoHideDuration={2000}
        onClose={() => setCopied(false)}
        message="API key copied to clipboard"
      />
    </Container>
  );
};

export default RequestAPIKey;
