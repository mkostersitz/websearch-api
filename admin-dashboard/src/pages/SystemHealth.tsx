import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  Button,
  Switch,
  FormControlLabel,
  Link,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  OpenInNew as OpenInNewIcon,
  InsertChart as InsertChartIcon,
  BugReport as BugReportIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';
import { api } from '../services/api';
import type { SystemHealth } from '../types';

const SystemHealthPage: React.FC = () => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [tabValue, setTabValue] = useState(0);
  const [logs, setLogs] = useState<any[]>([]);

  useEffect(() => {
    loadHealth();
    if (tabValue === 1) {
      loadLogs();
    }
    if (autoRefresh) {
      const interval = setInterval(() => {
        loadHealth();
        if (tabValue === 1) {
          loadLogs();
        }
      }, 30000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, tabValue]);

  const loadHealth = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getSystemHealth();
      setHealth(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load system health');
      console.error('Error loading health:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadLogs = async () => {
    try {
      // Get recent error logs from audit logs
      const auditLogs = await api.getAuditLogs({ limit: 50 });
      setLogs(auditLogs.slice(0, 20)); // Show last 20 entries
    } catch (err: any) {
      console.error('Error loading logs:', err);
    }
  };

  const getStatusColor = (status: string) => {
    if (status === 'healthy') return 'success';
    if (status === 'degraded' || status === 'unhealthy') return 'warning';
    return 'error';
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">System Health</Typography>
        <Box display="flex" gap={2} alignItems="center">
          <FormControlLabel
            control={
              <Switch
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
            }
            label="Auto-refresh (30s)"
          />
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadHealth}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {loading && !health && (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      )}

      {health && (
        <>
          <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
            <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
              <Tab label="Health Status" />
              <Tab label="System Logs" />
              <Tab label="Monitoring" />
            </Tabs>
          </Box>

          {tabValue === 0 && (
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Overall Status
                    </Typography>
                    <Chip
                      label={health.status.toUpperCase()}
                      color={getStatusColor(health.status)}
                      sx={{ fontSize: '1.1rem', py: 2 }}
                    />
                    <Typography variant="caption" color="textSecondary" sx={{ ml: 2 }}>
                      Last checked: {new Date(health.timestamp).toLocaleString()}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Database
                    </Typography>
                    <Box sx={{ mb: 2 }}>
                      <Chip
                        label={health.components.database.status}
                        color={getStatusColor(health.components.database.status)}
                      />
                    </Box>
                    <Typography variant="body2">
                      Type: {health.components.database.type}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Cache
                    </Typography>
                    <Box sx={{ mb: 2 }}>
                      <Chip
                        label={health.components.cache.status}
                        color={getStatusColor(health.components.cache.status)}
                      />
                    </Box>
                    <Typography variant="body2">
                      Type: {health.components.cache.type}
                    </Typography>
                    {health.components.cache.memory_used && (
                      <Typography variant="body2">
                        Memory Used: {health.components.cache.memory_used}
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}

          {tabValue === 1 && (
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                      <Typography variant="h6">
                        Recent System Activity
                      </Typography>
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={<RefreshIcon />}
                        onClick={loadLogs}
                      >
                        Refresh
                      </Button>
                    </Box>
                    <TableContainer component={Paper} variant="outlined">
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Timestamp</TableCell>
                            <TableCell>Action</TableCell>
                            <TableCell>Client ID</TableCell>
                            <TableCell>Status</TableCell>
                            <TableCell>Resource</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {logs.length === 0 ? (
                            <TableRow>
                              <TableCell colSpan={5} align="center">
                                <Typography color="textSecondary">No recent logs</Typography>
                              </TableCell>
                            </TableRow>
                          ) : (
                            logs.map((log) => (
                              <TableRow key={log.audit_id}>
                                <TableCell>{new Date(log.timestamp).toLocaleString()}</TableCell>
                                <TableCell>{log.action}</TableCell>
                                <TableCell>{log.client_id}</TableCell>
                                <TableCell>
                                  <Chip 
                                    label={log.status} 
                                    size="small"
                                    color={log.status === 'success' ? 'success' : 'default'}
                                  />
                                </TableCell>
                                <TableCell>{log.resource_type}</TableCell>
                              </TableRow>
                            ))
                          )}
                        </TableBody>
                      </Table>
                    </TableContainer>
                    <Box mt={2}>
                      <Typography variant="caption" color="textSecondary">
                        Showing last 20 system events. For detailed logs, check Audit Logs page.
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}

          {tabValue === 2 && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Box display="flex" alignItems="center" mb={2}>
                      <InsertChartIcon sx={{ mr: 1, color: 'primary.main' }} />
                      <Typography variant="h6">
                        Grafana
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="textSecondary" paragraph>
                      Visualize metrics and dashboards for system performance monitoring.
                    </Typography>
                    <Link
                      href="/grafana/"
                      target="_blank"
                      rel="noopener noreferrer"
                      underline="none"
                    >
                      <Button
                        variant="contained"
                        endIcon={<OpenInNewIcon />}
                        fullWidth
                      >
                        Open Grafana
                      </Button>
                    </Link>
                    <Typography variant="caption" color="textSecondary" display="block" mt={1}>
                      Default credentials: admin / admin
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Box display="flex" alignItems="center" mb={2}>
                      <SpeedIcon sx={{ mr: 1, color: 'warning.main' }} />
                      <Typography variant="h6">
                        Prometheus
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="textSecondary" paragraph>
                      Query metrics and view system performance data.
                    </Typography>
                    <Link
                      href="/prometheus/"
                      target="_blank"
                      rel="noopener noreferrer"
                      underline="none"
                    >
                      <Button
                        variant="contained"
                        endIcon={<OpenInNewIcon />}
                        fullWidth
                      >
                        Open Prometheus
                      </Button>
                    </Link>
                    <Typography variant="caption" color="textSecondary" display="block" mt={1}>
                      Time-series metrics database
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Box display="flex" alignItems="center" mb={2}>
                      <BugReportIcon sx={{ mr: 1, color: 'error.main' }} />
                      <Typography variant="h6">
                        Jaeger
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="textSecondary" paragraph>
                      Distributed tracing for request flow analysis and debugging.
                    </Typography>
                    <Link
                      href="/jaeger/"
                      target="_blank"
                      rel="noopener noreferrer"
                      underline="none"
                    >
                      <Button
                        variant="contained"
                        endIcon={<OpenInNewIcon />}
                        fullWidth
                      >
                        Open Jaeger
                      </Button>
                    </Link>
                    <Typography variant="caption" color="textSecondary" display="block" mt={1}>
                      Search using Trace IDs from Audit Logs
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12}>
                <Alert severity="info">
                  <Typography variant="body2">
                    <strong>Note:</strong> Ensure monitoring services are running via Docker Compose.
                    Use <code>./run.sh monitoring</code> to start Grafana, Prometheus, and Jaeger.
                  </Typography>
                </Alert>
              </Grid>
            </Grid>
          )}
        </>
      )}
    </Box>
  );
};

export default SystemHealthPage;
