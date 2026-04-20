import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  Typography,
  TextField,
  Button,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
} from '@mui/material';
import { DataGrid, GridColDef, GridRenderCellParams } from '@mui/x-data-grid';
import {
  Refresh as RefreshIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Group as GroupIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import { api } from '../services/api';

interface User {
  user_id: string;
  email: string;
  name: string;
  department?: string;
  title?: string;
  groups: string[];
  is_active: boolean;
  quota_per_day: number;
  quota_per_month: number;
  created_at: string;
  last_login?: string;
}

interface Group {
  group_id: string;
  name: string;
  description?: string;
  user_count: number;
  policies: string[];
  created_at: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function UsersGroups() {
  const [tabValue, setTabValue] = useState(0);
  const [users, setUsers] = useState<User[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Load users and groups
      const [usersData, groupsData] = await Promise.all([
        api.getUsers(),
        api.getGroups(),
      ]);
      
      setUsers(usersData);
      setGroups(groupsData);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load data');
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleEditUser = (user: User) => {
    setSelectedUser(user);
    setEditDialogOpen(true);
  };

  const handleCloseEditDialog = () => {
    setSelectedUser(null);
    setEditDialogOpen(false);
  };

  const handleSaveUser = async () => {
    if (!selectedUser) return;
    
    try {
      await api.updateUser(selectedUser.user_id, selectedUser);
      await loadData();
      handleCloseEditDialog();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to update user');
    }
  };

  const handleDeleteUser = async (userId: string) => {
    if (!confirm('Are you sure you want to delete this user?')) return;
    
    try {
      await api.deleteUser(userId);
      await loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to delete user');
    }
  };

  const filteredUsers = users.filter(user =>
    user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.department?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const userColumns: GridColDef[] = [
    {
      field: 'name',
      headerName: 'Name',
      width: 200,
      renderCell: (params: GridRenderCellParams) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <PersonIcon fontSize="small" color="primary" />
          <Typography variant="body2">{params.value}</Typography>
        </Box>
      ),
    },
    { field: 'email', headerName: 'Email', width: 250 },
    { field: 'department', headerName: 'Department', width: 150 },
    { field: 'title', headerName: 'Title', width: 180 },
    {
      field: 'groups',
      headerName: 'Groups',
      width: 250,
      renderCell: (params: GridRenderCellParams) => (
        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
          {(params.value as string[]).slice(0, 3).map((group) => (
            <Chip key={group} label={group} size="small" />
          ))}
          {(params.value as string[]).length > 3 && (
            <Chip label={`+${(params.value as string[]).length - 3}`} size="small" />
          )}
        </Box>
      ),
    },
    {
      field: 'is_active',
      headerName: 'Status',
      width: 100,
      renderCell: (params: GridRenderCellParams) => (
        <Chip
          label={params.value ? 'Active' : 'Inactive'}
          color={params.value ? 'success' : 'default'}
          size="small"
        />
      ),
    },
    {
      field: 'quota_per_day',
      headerName: 'Daily Quota',
      width: 120,
      valueFormatter: (params) => params.value.toLocaleString(),
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 120,
      renderCell: (params: GridRenderCellParams) => (
        <Box>
          <IconButton size="small" onClick={() => handleEditUser(params.row)}>
            <EditIcon fontSize="small" />
          </IconButton>
          <IconButton
            size="small"
            color="error"
            onClick={() => handleDeleteUser(params.row.user_id)}
          >
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Box>
      ),
    },
  ];

  const groupColumns: GridColDef[] = [
    {
      field: 'name',
      headerName: 'Group Name',
      width: 200,
      renderCell: (params: GridRenderCellParams) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <GroupIcon fontSize="small" color="primary" />
          <Typography variant="body2" fontWeight="bold">{params.value}</Typography>
        </Box>
      ),
    },
    { field: 'description', headerName: 'Description', width: 300 },
    { field: 'user_count', headerName: 'Users', width: 100 },
    {
      field: 'policies',
      headerName: 'Policies',
      width: 250,
      renderCell: (params: GridRenderCellParams) => (
        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
          {(params.value as string[]).slice(0, 2).map((policy) => (
            <Chip key={policy} label={policy} size="small" color="secondary" />
          ))}
          {(params.value as string[]).length > 2 && (
            <Chip label={`+${(params.value as string[]).length - 2}`} size="small" />
          )}
        </Box>
      ),
    },
    {
      field: 'created_at',
      headerName: 'Created',
      width: 180,
      valueFormatter: (params) => new Date(params.value).toLocaleString(),
    },
  ];

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4">Users & Groups</Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={loadData}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
            <Tab
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <PersonIcon />
                  <span>Users ({users.length})</span>
                </Box>
              }
            />
            <Tab
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <GroupIcon />
                  <span>Groups ({groups.length})</span>
                </Box>
              }
            />
          </Tabs>
        </Box>

        {error && (
          <Alert severity="error" sx={{ m: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <TabPanel value={tabValue} index={0}>
          <Box sx={{ mb: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
            <TextField
              label="Search Users"
              variant="outlined"
              size="small"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by name, email, or department"
              sx={{ flexGrow: 1, maxWidth: 500 }}
            />
            <Button variant="contained" startIcon={<AddIcon />}>
              Add User
            </Button>
          </Box>

          {loading ? (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
              <CircularProgress />
            </Box>
          ) : (
            <Box sx={{ height: 600, width: '100%' }}>
              <DataGrid
                rows={filteredUsers}
                columns={userColumns}
                getRowId={(row) => row.user_id}
                pageSizeOptions={[25, 50, 100]}
                initialState={{
                  pagination: { paginationModel: { pageSize: 25 } },
                }}
                disableRowSelectionOnClick
              />
            </Box>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Box sx={{ mb: 2, display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            <Button variant="contained" startIcon={<AddIcon />}>
              Create Group
            </Button>
          </Box>

          {loading ? (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
              <CircularProgress />
            </Box>
          ) : (
            <Box sx={{ height: 600, width: '100%' }}>
              <DataGrid
                rows={groups}
                columns={groupColumns}
                getRowId={(row) => row.group_id}
                pageSizeOptions={[25, 50, 100]}
                initialState={{
                  pagination: { paginationModel: { pageSize: 25 } },
                }}
                disableRowSelectionOnClick
              />
            </Box>
          )}
        </TabPanel>
      </Card>

      {/* Edit User Dialog */}
      <Dialog open={editDialogOpen} onClose={handleCloseEditDialog} maxWidth="md" fullWidth>
        <DialogTitle>Edit User</DialogTitle>
        <DialogContent>
          {selectedUser && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
              <TextField
                label="Name"
                value={selectedUser.name}
                onChange={(e) => setSelectedUser({ ...selectedUser, name: e.target.value })}
                fullWidth
              />
              <TextField
                label="Email"
                value={selectedUser.email}
                onChange={(e) => setSelectedUser({ ...selectedUser, email: e.target.value })}
                fullWidth
                disabled
              />
              <TextField
                label="Department"
                value={selectedUser.department || ''}
                onChange={(e) => setSelectedUser({ ...selectedUser, department: e.target.value })}
                fullWidth
              />
              <TextField
                label="Title"
                value={selectedUser.title || ''}
                onChange={(e) => setSelectedUser({ ...selectedUser, title: e.target.value })}
                fullWidth
              />
              <TextField
                label="Daily Quota"
                type="number"
                value={selectedUser.quota_per_day}
                onChange={(e) =>
                  setSelectedUser({ ...selectedUser, quota_per_day: Number(e.target.value) })
                }
                fullWidth
              />
              <TextField
                label="Monthly Quota"
                type="number"
                value={selectedUser.quota_per_month}
                onChange={(e) =>
                  setSelectedUser({ ...selectedUser, quota_per_month: Number(e.target.value) })
                }
                fullWidth
              />
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={selectedUser.is_active ? 'active' : 'inactive'}
                  label="Status"
                  onChange={(e) =>
                    setSelectedUser({ ...selectedUser, is_active: e.target.value === 'active' })
                  }
                >
                  <MenuItem value="active">Active</MenuItem>
                  <MenuItem value="inactive">Inactive</MenuItem>
                </Select>
              </FormControl>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseEditDialog}>Cancel</Button>
          <Button variant="contained" onClick={handleSaveUser}>
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
