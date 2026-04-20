import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  ToggleButtonGroup,
  ToggleButton,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { api } from '../services/api';
import type { SearchStats } from '../types';

const Analytics: React.FC = () => {
  const [stats, setStats] = useState<SearchStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(1);

  useEffect(() => {
    loadStats();
  }, [days]);

  const loadStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getSearchStats(days);
      setStats(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load analytics');
      console.error('Error loading analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Search Analytics</Typography>
        <ToggleButtonGroup
          value={days}
          exclusive
          onChange={(_, value) => value && setDays(value)}
          size="small"
        >
          <ToggleButton value={1}>24 Hours</ToggleButton>
          <ToggleButton value={7}>7 Days</ToggleButton>
          <ToggleButton value={30}>30 Days</ToggleButton>
          <ToggleButton value={90}>90 Days</ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {stats && (
        <>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Search Volume Trend
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={stats.daily_stats}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="searches"
                    stroke="#1976d2"
                    name="Searches"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
              <Typography variant="caption" color="textSecondary">
                Period: {stats.start_date.split('T')[0]} to {stats.end_date.split('T')[0]}
              </Typography>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Performance Metrics
              </Typography>
              <Box sx={{ display: 'flex', gap: 4, flexWrap: 'wrap', mt: 2 }}>
                <Box>
                  <Typography color="textSecondary" variant="caption">
                    Total Searches ({stats.period_days} days)
                  </Typography>
                  <Typography variant="h5">
                    {stats.daily_stats.reduce((sum, day) => sum + day.searches, 0)}
                  </Typography>
                </Box>
                <Box>
                  <Typography color="textSecondary" variant="caption">
                    Avg Response Time
                  </Typography>
                  <Typography variant="h5">
                    {Math.round(
                      stats.daily_stats.reduce((sum, day) => sum + day.avg_response_time_ms, 0) /
                        stats.daily_stats.length
                    )}ms
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </>
      )}
    </Box>
  );
};

export default Analytics;
