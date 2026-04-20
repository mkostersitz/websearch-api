import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Alert,
  Snackbar,
  IconButton,
  Autocomplete,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { api } from '../services/api';

interface Policy {
  policy_id: string;
  policy_name: string;
  description?: string;
  scope: 'global' | 'group' | 'user';
  target_group_ids: string[];
  target_user_ids: string[];
  is_active: boolean;
  priority: number;
}

interface User {
  user_id: string;
  email: string;
  name: string;
}

interface Group {
  group_id: string;
  name: string;
  user_count: number;
}

export default function Policies() {
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedPolicy, setSelectedPolicy] = useState<Policy | null>(null);
  const [tabValue, setTabValue] = useState(0);
  
  // Basic form states
  const [policyName, setPolicyName] = useState('');
  const [description, setDescription] = useState('');
  const [scope, setScope] = useState<'global' | 'group' | 'user'>('global');
  const [priority, setPriority] = useState(0);
  
  // Assignment states
  const [selectedGroups, setSelectedGroups] = useState<string[]>([]);
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  
  useEffect(() => {
    loadPolicies();
    loadUsers();
    loadGroups();
  }, []);
  
  const loadPolicies = async () => {
    try {
      setLoading(true);
      const data = await api.getPolicies();
      setPolicies(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load policies');
    } finally {
      setLoading(false);
    }
  };
  
  const loadUsers = async () => {
    try {
      const data = await api.getUsers();
      setUsers(data);
    } catch (err: any) {
      console.error('Failed to load users:', err);
    }
  };
  
  const loadGroups = async () => {
    try {
      const data = await api.getGroups();
      setGroups(data);
    } catch (err: any) {
      console.error('Failed to load groups:', err);
    }
  };
  
  const handleEditPolicy = (policy: Policy) => {
    setSelectedPolicy(policy);
    setPolicyName(policy.policy_name);
    setDescription(policy.description || '');
    setScope(policy.scope);
    setPriority(policy.priority);
    setSelectedGroups(policy.target_group_ids || []);
    setSelectedUsers(policy.target_user_ids || []);
    setEditDialogOpen(true);
  };
  
  const handleUpdatePolicy = async () => {
    if (!selectedPolicy) return;
    
    try {
      const updateData = {
        policy_name: policyName,
        description: description,
        priority: priority,
        target_group_ids: selectedGroups,
        target_user_ids: selectedUsers,
      };
      
      await api.updatePolicy(selectedPolicy.policy_id, updateData);
      setSuccess(true);
      setEditDialogOpen(false);
      loadPolicies();
    } catch (err: any) {
      setError(err.message || 'Failed to update policy');
    }
  };
  
  const handleCreatePolicy = async () => {
    try {
      const policyData = {
        policy_name: policyName,
        description: description,
        scope: scope,
        priority: priority,
        target_group_ids: [],
      };
      
      await api.createPolicy(policyData);
      setSuccess(true);
      setCreateDialogOpen(false);
      loadPolicies();
    } catch (err: any) {
      setError(err.message || 'Failed to create policy');
    }
  };
  
  const handleDeletePolicy = async () => {
    if (!selectedPolicy) return;
    
    try {
      await api.deletePolicy(selectedPolicy.policy_id);
      setSuccess(true);
      setDeleteDialogOpen(false);
      loadPolicies();
    } catch (err: any) {
      setError(err.message || 'Failed to delete policy');
    }
  };
  
  const columns: GridColDef[] = [
    { field: 'policy_name', headerName: 'Policy Name', width: 200 },
    { field: 'description', headerName: 'Description', width: 300 },
    { 
      field: 'scope', 
      headerName: 'Scope', 
      width: 100,
      renderCell: (params) => (
        <Chip label={params.value} size="small" color="primary" />
      )
    },
    { 
      field: 'target_group_ids', 
      headerName: 'Groups', 
      width: 200,
      renderCell: (params) => (
        <Box>
          {params.value.slice(0, 2).map((group: string) => (
            <Chip key={group} label={group} size="small" sx={{ mr: 0.5 }} />
          ))}
          {params.value.length > 2 && (
            <Chip label={`+${params.value.length - 2}`} size="small" />
          )}
        </Box>
      )
    },
    { field: 'priority', headerName: 'Priority', width: 100 },
    {
      field: 'is_active',
      headerName: 'Status',
      width: 100,
      renderCell: (params) => (
        <Chip 
          label={params.value ? 'Active' : 'Inactive'} 
          color={params.value ? 'success' : 'default'}
          size="small"
        />
      )
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 120,
      renderCell: (params) => (
        <Box>
          <IconButton size="small" onClick={() => handleEditPolicy(params.row)}>
            <EditIcon fontSize="small" />
          </IconButton>
          <IconButton size="small" onClick={() => {
            setSelectedPolicy(params.row);
            setDeleteDialogOpen(true);
          }}>
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Box>
      )
    },
  ];
  
  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4">Policy Management</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateDialogOpen(true)}
        >
          Create Policy
        </Button>
      </Box>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      
      <Card>
        <CardContent>
          <DataGrid
            rows={policies}
            columns={columns}
            getRowId={(row) => row.policy_id}
            loading={loading}
            autoHeight
            pageSizeOptions={[10, 25, 50]}
            initialState={{
              pagination: { paginationModel: { pageSize: 10 } },
            }}
          />
        </CardContent>
      </Card>
      
      {/* Create Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create New Policy</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              fullWidth
              label="Policy Name"
              value={policyName}
              onChange={(e) => setPolicyName(e.target.value)}
              required
            />
            <TextField
              fullWidth
              label="Description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              multiline
              rows={2}
            />
            <FormControl fullWidth>
              <InputLabel>Scope</InputLabel>
              <Select value={scope} onChange={(e) => setScope(e.target.value as any)}>
                <MenuItem value="global">Global</MenuItem>
                <MenuItem value="group">Group</MenuItem>
                <MenuItem value="user">User</MenuItem>
              </Select>
            </FormControl>
            <TextField
              fullWidth
              label="Priority"
              type="number"
              value={priority}
              onChange={(e) => setPriority(Number(e.target.value))}
              helperText="Higher priority policies override lower ones"
            />
            <Alert severity="info">
              More advanced settings (access schedules, permissions, limits) can be configured after creation.
            </Alert>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={handleCreatePolicy}
            disabled={!policyName}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Edit Policy: {selectedPolicy?.policy_name}</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)} sx={{ mb: 2 }}>
              <Tab label="Basic Info" />
              <Tab label="Assignments" />
            </Tabs>
            
            {tabValue === 0 && (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <TextField
                  fullWidth
                  label="Policy Name"
                  value={policyName}
                  onChange={(e) => setPolicyName(e.target.value)}
                  required
                />
                <TextField
                  fullWidth
                  label="Description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  multiline
                  rows={2}
                />
                <FormControl fullWidth>
                  <InputLabel>Scope</InputLabel>
                  <Select value={scope} onChange={(e) => setScope(e.target.value as any)}>
                    <MenuItem value="global">Global</MenuItem>
                    <MenuItem value="group">Group</MenuItem>
                    <MenuItem value="user">User</MenuItem>
                  </Select>
                </FormControl>
                <TextField
                  fullWidth
                  label="Priority"
                  type="number"
                  value={priority}
                  onChange={(e) => setPriority(Number(e.target.value))}
                  helperText="Higher priority policies override lower ones"
                />
              </Box>
            )}
            
            {tabValue === 1 && (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                {/* Group Selection */}
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Assign to Groups
                  </Typography>
                  <Autocomplete
                    multiple
                    options={groups.map(g => g.group_id)}
                    value={selectedGroups}
                    onChange={(_, newValue) => setSelectedGroups(newValue)}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        label="Select Groups"
                        placeholder="Type to search groups..."
                      />
                    )}
                    renderTags={(value, getTagProps) =>
                      value.map((option, index) => (
                        <Chip
                          label={option}
                          {...getTagProps({ index })}
                          color="primary"
                        />
                      ))
                    }
                  />
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    Selected: {selectedGroups.length} group(s)
                  </Typography>
                </Box>
                
                {/* User Selection */}
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Assign to Users
                  </Typography>
                  <Autocomplete
                    multiple
                    options={users}
                    getOptionLabel={(option) => typeof option === 'string' ? option : `${option.name} (${option.email})`}
                    value={users.filter(u => selectedUsers.includes(u.user_id))}
                    onChange={(_, newValue) => setSelectedUsers(newValue.map(v => typeof v === 'string' ? v : v.user_id))}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        label="Select Users"
                        placeholder="Type to search users..."
                      />
                    )}
                    renderTags={(value, getTagProps) =>
                      value.map((option, index) => (
                        <Chip
                          label={typeof option === 'string' ? option : option.name}
                          {...getTagProps({ index })}
                          color="secondary"
                        />
                      ))
                    }
                  />
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    Selected: {selectedUsers.length} user(s)
                  </Typography>
                </Box>
                
                <Alert severity="info">
                  This policy will apply to all selected groups and users. Group policies apply to all members of those groups.
                </Alert>
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={handleUpdatePolicy}
            disabled={!policyName}
          >
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Delete Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Policy</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete the policy "{selectedPolicy?.policy_name}"?
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" color="error" onClick={handleDeletePolicy}>
            Delete
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Success Snackbar */}
      <Snackbar
        open={success}
        autoHideDuration={3000}
        onClose={() => setSuccess(false)}
        message="Operation successful"
      />
    </Box>
  );
}
