import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from 'react-oidc-context';
import {
  AppBar,
  Box,
  Button,
  CircularProgress,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  Container,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  People as PeopleIcon,
  Analytics as AnalyticsIcon,
  Description as DescriptionIcon,
  MonitorHeart as MonitorHeartIcon,
  Settings as SettingsIcon,
  Group as GroupIcon,
  Security as SecurityIcon,
  Logout as LogoutIcon,
  PushPin as PushPinIcon,
  PushPinOutlined as PushPinOutlinedIcon,
  Key as KeyIcon,
  MenuBook as MenuBookIcon,
  Login as LoginIcon,
} from '@mui/icons-material';
import { api } from './services/api';
import AuthCallback from './components/AuthCallback';
import Dashboard from './pages/Dashboard';
import Clients from './pages/Clients';
import Analytics from './pages/Analytics';
import AuditLogs from './pages/AuditLogs';
import SystemHealth from './pages/SystemHealth';
import Settings from './pages/Settings';
import UsersGroups from './pages/UsersGroups';
import Policies from './pages/Policies';
import RequestAPIKey from './pages/RequestAPIKey';
import Documentation from './pages/Documentation';

const drawerWidth = 240;

interface NavItem {
  text: string;
  icon: React.ReactElement;
  path: string;
}

const navItems: NavItem[] = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
  { text: 'Request API Key', icon: <KeyIcon />, path: '/request-key' },
  { text: 'Clients', icon: <PeopleIcon />, path: '/clients' },
  { text: 'Users & Groups', icon: <GroupIcon />, path: '/users-groups' },
  { text: 'Policies', icon: <SecurityIcon />, path: '/policies' },
  { text: 'Analytics', icon: <AnalyticsIcon />, path: '/analytics' },
  { text: 'Audit Logs', icon: <DescriptionIcon />, path: '/audit-logs' },
  { text: 'System Health', icon: <MonitorHeartIcon />, path: '/system-health' },
  { text: 'Documentation', icon: <MenuBookIcon />, path: '/docs' },
  { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
];

function App() {
  const auth = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [drawerPinned, setDrawerPinned] = useState(() => {
    const saved = localStorage.getItem('drawerPinned');
    return saved ? JSON.parse(saved) : true;
  });
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const navigate = useNavigate();
  const location = useLocation();

  // Keep the API service token in sync with the OIDC user
  useEffect(() => {
    if (auth.user?.access_token) {
      api.setBearerToken(auth.user.access_token);
    } else {
      api.setBearerToken('');
    }
  }, [auth.user?.access_token]);

  const handleDrawerToggle = () => setMobileOpen(!mobileOpen);

  const handleDrawerPin = () => {
    const newPinned = !drawerPinned;
    setDrawerPinned(newPinned);
    localStorage.setItem('drawerPinned', JSON.stringify(newPinned));
  };

  const handleLogout = () => {
    auth.signoutRedirect();
  };

  // ── Loading state ──────────────────────────────────────────────────────────
  if (auth.isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }

  // ── Error state ────────────────────────────────────────────────────────────
  if (auth.error) {
    return (
      <Box display="flex" flexDirection="column" justifyContent="center" alignItems="center" minHeight="100vh" gap={2}>
        <Typography color="error">Authentication error: {auth.error.message}</Typography>
        <Button variant="contained" onClick={() => auth.signinRedirect()}>
          Try again
        </Button>
      </Box>
    );
  }

  // ── Not authenticated — show login screen ──────────────────────────────────
  if (!auth.isAuthenticated) {
    return (
      <Box display="flex" flexDirection="column" justifyContent="center" alignItems="center" minHeight="100vh" gap={3}>
        <Typography variant="h4" fontWeight={700}>WebSearch API</Typography>
        <Typography variant="body1" color="text.secondary">
          Sign in with your organisation account to access the admin dashboard.
        </Typography>
        <Button
          variant="contained"
          size="large"
          startIcon={<LoginIcon />}
          onClick={() => auth.signinRedirect()}
        >
          Sign in with Keycloak
        </Button>
      </Box>
    );
  }

  // ── Authenticated app shell ────────────────────────────────────────────────
  const drawer = (
    <Box>
      <Toolbar sx={{ backgroundColor: '#000', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6" noWrap component="div">
          WebSearch API
        </Typography>
        {!isMobile && (
          <IconButton
            size="small"
            onClick={handleDrawerPin}
            sx={{ color: '#fff' }}
            title={drawerPinned ? 'Unpin sidebar' : 'Pin sidebar'}
          >
            {drawerPinned ? <PushPinIcon fontSize="small" /> : <PushPinOutlinedIcon fontSize="small" />}
          </IconButton>
        )}
      </Toolbar>
      <List>
        {navItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => {
                navigate(item.path);
                if (isMobile) setMobileOpen(false);
              }}
              sx={{
                '&.Mui-selected': {
                  backgroundColor: 'rgba(25, 118, 210, 0.2)',
                  '&:hover': { backgroundColor: 'rgba(25, 118, 210, 0.3)' },
                },
              }}
            >
              <ListItemIcon sx={{ color: '#fff' }}>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      <Box sx={{ position: 'absolute', bottom: 0, width: '100%', p: 2 }}>
        <Typography variant="caption" sx={{ px: 1, pb: 1, display: 'block', color: 'grey.500' }}>
          {auth.user?.profile.email}
        </Typography>
        <ListItemButton onClick={handleLogout}>
          <ListItemIcon sx={{ color: '#fff' }}>
            <LogoutIcon />
          </ListItemIcon>
          <ListItemText primary="Logout" />
        </ListItemButton>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { md: drawerPinned ? `calc(100% - ${drawerWidth}px)` : '100%' },
          ml: { md: drawerPinned ? `${drawerWidth}px` : 0 },
          transition: theme.transitions.create(['margin', 'width'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: drawerPinned ? 'none' : 'block' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div">
            Admin Dashboard
          </Typography>
        </Toolbar>
      </AppBar>

      <Box
        component="nav"
        sx={{ width: { md: drawerPinned ? drawerWidth : 0 }, flexShrink: { md: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant={drawerPinned ? 'permanent' : 'temporary'}
          open={drawerPinned || mobileOpen}
          onClose={handleDrawerToggle}
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
              transition: theme.transitions.create('width', {
                easing: theme.transitions.easing.sharp,
                duration: theme.transitions.duration.enteringScreen,
              }),
            },
          }}
        >
          {drawer}
        </Drawer>
      </Box>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { md: drawerPinned ? `calc(100% - ${drawerWidth}px)` : '100%' },
          transition: theme.transitions.create(['margin', 'width'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
        }}
      >
        <Toolbar />
        <Container maxWidth="xl">
          <Routes>
            <Route path="/auth/callback" element={<AuthCallback />} />
            <Route path="/request-key" element={<RequestAPIKey />} />
            <Route path="/" element={<Dashboard />} />
            <Route path="/clients" element={<Clients />} />
            <Route path="/users-groups" element={<UsersGroups />} />
            <Route path="/policies" element={<Policies />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/audit-logs" element={<AuditLogs />} />
            <Route path="/system-health" element={<SystemHealth />} />
            <Route path="/docs" element={<Documentation />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Container>
      </Box>
    </Box>
  );
}

export default App;
