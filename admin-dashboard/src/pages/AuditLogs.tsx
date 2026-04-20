import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  CircularProgress,
  Alert,
  IconButton,
  Chip,
  Divider,
  Grid,
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Refresh as RefreshIcon,
  FirstPage as FirstPageIcon,
  LastPage as LastPageIcon,
  NavigateBefore as NavigateBeforeIcon,
  NavigateNext as NavigateNextIcon,
} from '@mui/icons-material';
import { api } from '../services/api';
import type { AuditLog } from '../types';

const AuditLogs: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [filters, setFilters] = useState({
    client_id: '',
    action: '',
  });
  const detailPanelRef = React.useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadLogs();
  }, []);

  const loadLogs = async (filterOverride?: any) => {
    try {
      setLoading(true);
      setError(null);
      const activeFilters = filterOverride || filters;
      const params: any = { limit: 100 }; // Get more logs by default
      if (activeFilters.client_id) params.client_id = activeFilters.client_id;
      if (activeFilters.action) params.action = activeFilters.action;
      const data = await api.getAuditLogs(params);
      setLogs(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load audit logs');
      console.error('Error loading logs:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleExpand = (auditId: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(auditId)) {
      newExpanded.delete(auditId);
    } else {
      newExpanded.add(auditId);
      // Scroll to detail panel after state update
      setTimeout(() => {
        detailPanelRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    }
    setExpandedRows(newExpanded);
  };

  const handleNavigate = (direction: 'first' | 'previous' | 'next' | 'last') => {
    if (logs.length === 0) return;
    
    const expandedArray = Array.from(expandedRows);
    if (expandedArray.length === 0) {
      // No row expanded, expand the first one
      const firstId = logs[0].audit_id;
      setExpandedRows(new Set([firstId]));
      setTimeout(() => {
        detailPanelRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
      return;
    }

    const currentId = expandedArray[0]; // Use first expanded row
    const currentIndex = logs.findIndex(log => log.audit_id === currentId);
    
    let newIndex = currentIndex;
    switch (direction) {
      case 'first':
        newIndex = 0;
        break;
      case 'previous':
        newIndex = Math.max(0, currentIndex - 1);
        break;
      case 'next':
        newIndex = Math.min(logs.length - 1, currentIndex + 1);
        break;
      case 'last':
        newIndex = logs.length - 1;
        break;
    }

    if (newIndex !== currentIndex || expandedArray.length > 1) {
      setExpandedRows(new Set([logs[newIndex].audit_id]));
      setTimeout(() => {
        detailPanelRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    }
  };

  const handleClientClick = (clientId: string) => {
    const newFilters = { ...filters, client_id: clientId };
    setFilters(newFilters);
    loadLogs(newFilters);
  };

  const DetailPanel = ({ row }: { row: AuditLog }) => {
    return (
      <Box sx={{ p: 3, bgcolor: 'grey.50' }}>
        <Grid container spacing={3}>
          {/* User Context */}
          {row.user_id && (
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="primary" gutterBottom>
                User Context
              </Typography>
              <Box sx={{ pl: 2 }}>
                <Typography variant="body2"><strong>User ID:</strong> {row.user_id}</Typography>
                {row.user_email && <Typography variant="body2"><strong>Email:</strong> {row.user_email}</Typography>}
                {row.user_name && <Typography variant="body2"><strong>Name:</strong> {row.user_name}</Typography>}
              </Box>
            </Grid>
          )}

          {/* Trace Information */}
          {row.trace && (
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="primary" gutterBottom>
                Trace Information
              </Typography>
              <Box sx={{ pl: 2 }}>
                <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                  <strong>Trace ID:</strong> {row.trace.trace_id}
                </Typography>
                <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                  <strong>Span ID:</strong> {row.trace.span_id}
                </Typography>
              </Box>
            </Grid>
          )}

          {/* Request Details */}
          {row.request && (
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="primary" gutterBottom>
                Request Details
              </Typography>
              <Box sx={{ pl: 2 }}>
                <Typography variant="body2"><strong>Method:</strong> {row.request.method}</Typography>
                <Typography variant="body2"><strong>Path:</strong> {row.request.path}</Typography>
                {row.request.query && <Typography variant="body2"><strong>Query:</strong> "{row.request.query}"</Typography>}
                {row.request.ip_address && <Typography variant="body2"><strong>IP:</strong> {row.request.ip_address}</Typography>}
                {row.request.user_agent && (
                  <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                    <strong>User Agent:</strong> {row.request.user_agent}
                  </Typography>
                )}
              </Box>
            </Grid>
          )}

          {/* Response Details */}
          {row.response && (
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="primary" gutterBottom>
                Response Details
              </Typography>
              <Box sx={{ pl: 2 }}>
                <Typography variant="body2">
                  <strong>Status:</strong>{' '}
                  <Chip 
                    label={row.response.status_code || 'N/A'} 
                    size="small" 
                    color={row.response.status_code === 200 ? 'success' : 'error'}
                  />
                </Typography>
                {row.response.provider && <Typography variant="body2"><strong>Provider:</strong> {row.response.provider}</Typography>}
                {row.response.results_count !== undefined && (
                  <Typography variant="body2"><strong>Results:</strong> {row.response.results_count}</Typography>
                )}
                {row.response.response_time_ms && (
                  <Typography variant="body2"><strong>Response Time:</strong> {row.response.response_time_ms.toFixed(2)}ms</Typography>
                )}
                {row.response.blocked_reason && (
                  <Alert severity="warning" sx={{ mt: 1 }}>
                    <strong>Blocked:</strong> {row.response.blocked_reason}
                  </Alert>
                )}
              </Box>
            </Grid>
          )}

          {/* Policies Applied */}
          {row.policies_details && row.policies_details.length > 0 && (
            <Grid item xs={12}>
              <Typography variant="subtitle2" color="primary" gutterBottom>
                Policies Applied ({row.policies_details.length})
              </Typography>
              <Box sx={{ pl: 2 }}>
                {row.policies_details.map((policy: any, idx: number) => (
                  <Box key={idx} sx={{ mb: 1 }}>
                    <Typography variant="body2">
                      <strong>{policy.policy_name || policy.policy_id}</strong> (Priority: {policy.priority})
                    </Typography>
                    {policy.blocked_keywords && policy.blocked_keywords.length > 0 && (
                      <Box sx={{ mt: 0.5 }}>
                        <Typography variant="caption" color="text.secondary">Blocked Keywords: </Typography>
                        {policy.blocked_keywords.slice(0, 10).map((kw: string) => (
                          <Chip key={kw} label={kw} size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                        ))}
                        {policy.blocked_keywords.length > 10 && (
                          <Chip label={`+${policy.blocked_keywords.length - 10} more`} size="small" />
                        )}
                      </Box>
                    )}
                  </Box>
                ))}
              </Box>
            </Grid>
          )}

          {/* Quotas */}
          {row.quotas && (
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="primary" gutterBottom>
                Quota Usage
              </Typography>
              <Box sx={{ pl: 2 }}>
                <Typography variant="body2">
                  <strong>Daily:</strong> {row.quotas.used_today || 0} / {row.quotas.limit_today || 0}
                </Typography>
                <Typography variant="body2">
                  <strong>Monthly:</strong> {row.quotas.used_month || 0} / {row.quotas.limit_month || 0}
                </Typography>
              </Box>
            </Grid>
          )}

          {/* Filtering Info */}
          {row.filtering && (
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="primary" gutterBottom>
                Result Filtering
              </Typography>
              <Box sx={{ pl: 2 }}>
                <Typography variant="body2"><strong>Total Results:</strong> {row.filtering.total_results}</Typography>
                <Typography variant="body2"><strong>Blocked:</strong> {row.filtering.blocked_results}</Typography>
                <Typography variant="body2"><strong>Returned:</strong> {row.filtering.returned_results}</Typography>
              </Box>
            </Grid>
          )}

          {/* Additional Details */}
          {row.details && Object.keys(row.details).length > 0 && (
            <Grid item xs={12}>
              <Typography variant="subtitle2" color="primary" gutterBottom>
                Additional Details
              </Typography>
              <Box sx={{ pl: 2, fontFamily: 'monospace', fontSize: '0.75rem', bgcolor: 'grey.100', p: 1, borderRadius: 1 }}>
                <pre style={{ margin: 0, overflow: 'auto' }}>
                  {JSON.stringify(row.details, null, 2)}
                </pre>
              </Box>
            </Grid>
          )}
        </Grid>
      </Box>
    );
  };

  const columns: GridColDef[] = [
    {
      field: 'expand',
      headerName: '',
      width: 50,
      renderCell: (params) => (
        <IconButton size="small" onClick={() => handleToggleExpand(params.row.audit_id)}>
          {expandedRows.has(params.row.audit_id) ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </IconButton>
      ),
    },
    {
      field: 'timestamp',
      headerName: 'Timestamp',
      width: 180,
      valueFormatter: (params) => new Date(params.value).toLocaleString(),
    },
    { 
      field: 'client_id', 
      headerName: 'Client ID', 
      width: 150,
      renderCell: (params) => (
        <Box
          sx={{
            cursor: 'pointer',
            color: 'primary.main',
            textDecoration: 'underline',
            '&:hover': {
              color: 'primary.dark',
              fontWeight: 'bold',
            },
          }}
          onClick={() => handleClientClick(params.value)}
        >
          {params.value}
        </Box>
      ),
    },
    { field: 'action', headerName: 'Action', width: 150 },
    { field: 'resource_type', headerName: 'Resource Type', width: 150 },
    { field: 'status', headerName: 'Status', width: 120 },
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Audit Logs
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" gap={2} flexWrap="wrap" alignItems="center">
            <TextField
              label="Client ID"
              value={filters.client_id}
              onChange={(e) => setFilters({ ...filters, client_id: e.target.value })}
              size="small"
              placeholder="Click a Client ID in table"
            />
            <TextField
              label="Action"
              value={filters.action}
              onChange={(e) => setFilters({ ...filters, action: e.target.value })}
              size="small"
            />
            <Button variant="contained" onClick={() => loadLogs()}>
              Apply Filters
            </Button>
            <Button
              variant="outlined"
              onClick={() => {
                const clearedFilters = { client_id: '', action: '' };
                setFilters(clearedFilters);
                loadLogs(clearedFilters);
              }}
            >
              Clear Filters
            </Button>
            <Button variant="outlined" startIcon={<RefreshIcon />} onClick={() => loadLogs()}>
              Refresh
            </Button>
            {filters.client_id && (
              <Typography variant="body2" color="text.secondary">
                Showing logs for: <strong>{filters.client_id}</strong>
              </Typography>
            )}
            {!filters.client_id && !filters.action && logs.length > 0 && (
              <Typography variant="body2" color="text.secondary">
                Showing all logs ({logs.length} total)
              </Typography>
            )}
          </Box>
        </CardContent>
      </Card>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      ) : (
        <>
          <Box sx={{ height: 600, width: '100%', mb: 2 }}>
            <DataGrid
              rows={logs}
              columns={columns}
              getRowId={(row) => row.audit_id}
              pageSizeOptions={[25, 50, 100]}
              initialState={{
                pagination: { paginationModel: { pageSize: 25 } },
              }}
              disableRowSelectionOnClick
              sx={{
                '& .MuiDataGrid-row': {
                  cursor: 'pointer',
                },
              }}
            />
          </Box>
          
          {/* Expanded Row Details - Show Below Grid */}
          {expandedRows.size > 0 && (
            <Box ref={detailPanelRef} sx={{ mt: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  Expanded Details ({expandedRows.size})
                </Typography>
                {/* Navigation Buttons */}
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<FirstPageIcon />}
                    onClick={() => handleNavigate('first')}
                    disabled={logs.length === 0}
                  >
                    First
                  </Button>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<NavigateBeforeIcon />}
                    onClick={() => handleNavigate('previous')}
                    disabled={logs.length === 0}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outlined"
                    size="small"
                    endIcon={<NavigateNextIcon />}
                    onClick={() => handleNavigate('next')}
                    disabled={logs.length === 0}
                  >
                    Next
                  </Button>
                  <Button
                    variant="outlined"
                    size="small"
                    endIcon={<LastPageIcon />}
                    onClick={() => handleNavigate('last')}
                    disabled={logs.length === 0}
                  >
                    Last
                  </Button>
                </Box>
              </Box>
              {Array.from(expandedRows).map((auditId) => {
                const log = logs.find((l) => l.audit_id === auditId);
                if (!log) return null;
                
                const currentIndex = logs.findIndex((l) => l.audit_id === auditId);
                
                return (
                  <Card key={auditId} sx={{ mb: 2 }}>
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                        <Typography variant="h6">
                          {log.action} - {new Date(log.timestamp).toLocaleString()}
                          <Typography component="span" variant="body2" color="text.secondary" sx={{ ml: 2 }}>
                            (Entry {currentIndex + 1} of {logs.length})
                          </Typography>
                        </Typography>
                        <IconButton onClick={() => handleToggleExpand(auditId)} size="small">
                          <ExpandLessIcon />
                        </IconButton>
                      </Box>
                      <Divider sx={{ mb: 2 }} />
                      <DetailPanel row={log} />
                    </CardContent>
                  </Card>
                );
              })}
              {/* Bottom Navigation Buttons */}
              <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1, mb: 2 }}>
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<FirstPageIcon />}
                  onClick={() => handleNavigate('first')}
                  disabled={logs.length === 0}
                >
                  First
                </Button>
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<NavigateBeforeIcon />}
                  onClick={() => handleNavigate('previous')}
                  disabled={logs.length === 0}
                >
                  Previous
                </Button>
                <Button
                  variant="outlined"
                  size="small"
                  endIcon={<NavigateNextIcon />}
                  onClick={() => handleNavigate('next')}
                  disabled={logs.length === 0}
                >
                  Next
                </Button>
                <Button
                  variant="outlined"
                  size="small"
                  endIcon={<LastPageIcon />}
                  onClick={() => handleNavigate('last')}
                  disabled={logs.length === 0}
                >
                  Last
                </Button>
              </Box>
            </Box>
          )}
        </>
      )}
    </Box>
  );
};

export default AuditLogs;
