import { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Divider,
  Alert,
  Snackbar,
  Grid,
  Card,
  CardContent,
  CardActions,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
} from '@mui/material';
import {
  Save as SaveIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  OpenInNew as OpenInNewIcon,
  UploadFile as UploadFileIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { api } from '../services/api';
import type { SystemSettings } from '../types';

export default function Settings() {
  const [, setSettings] = useState<SystemSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Local state for form fields
  const [otelEndpoint, setOtelEndpoint] = useState('');
  const [searchPolicyLevel, setSearchPolicyLevel] = useState<'strict' | 'moderate' | 'open' | 'custom'>('moderate');
  const [customKeywords, setCustomKeywords] = useState<string[]>([]);
  const [newKeyword, setNewKeyword] = useState('');
  const [selectedPolicyId, setSelectedPolicyId] = useState<string>('');
  const [policies, setPolicies] = useState<any[]>([]);
  const [groups, setGroups] = useState<any[]>([]);
  const [selectedGroups, setSelectedGroups] = useState<string[]>([]);
  const [parentalControlsEnabled, setParentalControlsEnabled] = useState(false);
  const [ageRestriction, setAgeRestriction] = useState<number>(13);
  const [blockAdultContent, setBlockAdultContent] = useState(true);
  const [blockViolence, setBlockViolence] = useState(true);
  const [grafanaUrl, setGrafanaUrl] = useState('http://localhost:3002');
  const [prometheusUrl, setPrometheusUrl] = useState('http://localhost:9091');
  const [jaegerUrl, setJaegerUrl] = useState('http://localhost:17686');
  
  // User sync settings
  const [userSyncEnabled, setUserSyncEnabled] = useState(false);
  const [syncIntervalHours, setSyncIntervalHours] = useState(24);
  const [groupSyncEnabled, setGroupSyncEnabled] = useState(true);
  const [autoCreateUsers, setAutoCreateUsers] = useState(true);
  const [autoAssignPolicies, setAutoAssignPolicies] = useState(false);
  
  // OAuth/Directory settings
  const [adEnabled, setAdEnabled] = useState(false);
  const [adServerUrl, setAdServerUrl] = useState('');
  const [adDomain, setAdDomain] = useState('');
  const [entraEnabled, setEntraEnabled] = useState(false);
  const [entraTenantId, setEntraTenantId] = useState('');
  const [entraClientId, setEntraClientId] = useState('');
  const [oktaEnabled, setOktaEnabled] = useState(false);
  const [oktaDomain, setOktaDomain] = useState('');
  const [csvEnabled, setCsvEnabled] = useState(false);
  const [csvPath, setCsvPath] = useState('');
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [csvFileName, setCsvFileName] = useState('');
  
  // Keycloak settings
  const [keycloakEnabled, setKeycloakEnabled] = useState(false);
  const [keycloakUrl, setKeycloakUrl] = useState('');
  const [keycloakRealm, setKeycloakRealm] = useState('websearch');
  const [keycloakClientId, setKeycloakClientId] = useState('');
  const [keycloakClientSecret, setKeycloakClientSecret] = useState('');

  // Sync status
  const [lastSyncTime, setLastSyncTime] = useState<string | null>(null);
  const [lastSyncStatus, setLastSyncStatus] = useState<'success' | 'failed' | 'pending' | null>(null);
  const [syncedUserCount, setSyncedUserCount] = useState<number>(0);
  const [syncedGroupCount, setSyncedGroupCount] = useState<number>(0);

  useEffect(() => {
    loadSettings();
    loadPoliciesAndGroups();
  }, []);

  const loadPoliciesAndGroups = async () => {
    try {
      const [policiesData, groupsData] = await Promise.all([
        api.getPolicies(),
        api.getGroups()
      ]);
      setPolicies(policiesData);
      setGroups(groupsData);
    } catch (err) {
      console.error('Failed to load policies and groups:', err);
    }
  };

  const loadSettings = async () => {
    try {
      setLoading(true);
      const data = await api.getSettings();
      setSettings(data);
      
      // Populate form fields
      setOtelEndpoint(data.otel_endpoint || 'http://localhost:5317');
      setSearchPolicyLevel(data.search_policy?.level || 'moderate');
      
      // Load custom keywords if in custom mode
      if (data.search_policy?.level === 'custom' && data.search_policy?.block_keywords) {
        setCustomKeywords(data.search_policy.block_keywords);
      }
      
      setParentalControlsEnabled(data.parental_controls?.enabled || false);
      setAgeRestriction(data.parental_controls?.age_restriction || 13);
      setBlockAdultContent(data.parental_controls?.block_adult_content || true);
      setBlockViolence(data.parental_controls?.block_violence || true);
      setGrafanaUrl(data.integrations?.grafana_url || 'http://localhost:3002');
      setPrometheusUrl(data.integrations?.prometheus_url || 'http://localhost:9091');
      setJaegerUrl(data.integrations?.jaeger_url || 'http://localhost:17686');

      if (data.keycloak) {
        setKeycloakEnabled(data.keycloak.enabled || false);
        setKeycloakUrl(data.keycloak.url || '');
        setKeycloakRealm(data.keycloak.realm || 'websearch');
        setKeycloakClientId(data.keycloak.client_id || '');
        setKeycloakClientSecret(data.keycloak.client_secret || '');
      }
      
      // User sync settings
      if (data.user_sync) {
        setUserSyncEnabled(data.user_sync.enabled || false);
        setSyncIntervalHours(data.user_sync.sync_interval_hours || 24);
        setGroupSyncEnabled(data.user_sync.group_sync_enabled || true);
        setAutoCreateUsers(data.user_sync.auto_create_users || true);
        setAutoAssignPolicies(data.user_sync.auto_assign_policies || false);
        
        // Load source configurations
        const sources = data.user_sync.sources || [];
        const adSource = sources.find(s => s.type === 'active_directory');
        if (adSource) {
          setAdEnabled(adSource.enabled || false);
          setAdServerUrl(adSource.config.server_url || '');
          setAdDomain(adSource.config.domain || '');
        }
        
        const entraSource = sources.find(s => s.type === 'entra_id');
        if (entraSource) {
          setEntraEnabled(entraSource.enabled || false);
          setEntraTenantId(entraSource.config.tenant_id || '');
          setEntraClientId(entraSource.config.client_id || '');
        }
        
        const oktaSource = sources.find(s => s.type === 'okta');
        if (oktaSource) {
          setOktaEnabled(oktaSource.enabled || false);
          setOktaDomain(oktaSource.config.domain || '');
        }
        
        const csvSource = sources.find(s => s.type === 'csv');
        if (csvSource) {
          setCsvEnabled(csvSource.enabled || false);
          setCsvPath(csvSource.config.csv_path || '');
          
          // Load sync status
          if (csvSource.last_sync) {
            setLastSyncTime(csvSource.last_sync);
            setLastSyncStatus(csvSource.last_sync_status || 'pending');
            setSyncedUserCount(csvSource.users_synced || 0);
            setSyncedGroupCount(csvSource.groups_synced || 0);
          }
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      
      const updatedSettings: SystemSettings = {
        otel_endpoint: otelEndpoint,
        search_policy: {
          level: searchPolicyLevel,
          enabled: true,
          block_keywords: getBlockKeywordsByLevel(searchPolicyLevel),
        },
        parental_controls: {
          enabled: parentalControlsEnabled,
          age_restriction: ageRestriction,
          block_adult_content: blockAdultContent,
          block_violence: blockViolence,
          block_gambling: parentalControlsEnabled,
          block_drugs: parentalControlsEnabled,
        },
        integrations: {
          grafana_url: grafanaUrl,
          prometheus_url: prometheusUrl,
          jaeger_url: jaegerUrl,
        },
        user_sync: {
          enabled: userSyncEnabled,
          sync_interval_hours: syncIntervalHours,
          group_sync_enabled: groupSyncEnabled,
          auto_create_users: autoCreateUsers,
          auto_assign_policies: autoAssignPolicies,
          sources: [
            ...(adEnabled ? [{
              source_id: 'ad-sync',
              name: 'Active Directory',
              type: 'active_directory' as const,
              enabled: adEnabled,
              config: {
                server_url: adServerUrl,
                domain: adDomain,
                sync_groups: groupSyncEnabled,
              },
            }] : []),
            ...(entraEnabled ? [{
              source_id: 'entra-sync',
              name: 'Microsoft Entra ID',
              type: 'entra_id' as const,
              enabled: entraEnabled,
              config: {
                tenant_id: entraTenantId,
                client_id: entraClientId,
                sync_groups: groupSyncEnabled,
              },
            }] : []),
            ...(oktaEnabled ? [{
              source_id: 'okta-sync',
              name: 'Okta',
              type: 'okta' as const,
              enabled: oktaEnabled,
              config: {
                domain: oktaDomain,
                sync_groups: groupSyncEnabled,
              },
            }] : []),
            ...(csvEnabled ? [{
              source_id: 'csv-sync',
              name: 'CSV Import',
              type: 'csv' as const,
              enabled: csvEnabled,
              config: {
                csv_path: csvPath,
              },
            }] : []),
          ],
        },
      };

      updatedSettings.keycloak = {
        enabled: keycloakEnabled,
        url: keycloakUrl,
        realm: keycloakRealm,
        client_id: keycloakClientId,
        client_secret: keycloakClientSecret,
      };
      await api.updateSettings(updatedSettings);
      setSuccess(true);
      await loadSettings(); // Reload to get server-side updates
    } catch (err: any) {
      setError(err.message || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const getBlockKeywordsByLevel = (level: string): string[] => {
    switch (level) {
      case 'strict':
        return ['adult', 'explicit', 'violence', 'gambling', 'drugs', 'weapons', 'hate'];
      case 'moderate':
        return ['adult', 'explicit', 'violence', 'gambling'];
      case 'open':
        return ['adult', 'explicit'];
      case 'custom':
        return customKeywords;
      default:
        return [];
    }
  };

  const getPolicyDescription = (level: string): string => {
    switch (level) {
      case 'strict':
        return 'Maximum filtering - blocks adult content, violence, gambling, drugs, weapons, and hate speech';
      case 'moderate':
        return 'Balanced filtering - blocks adult content, explicit material, violence, and gambling';
      case 'open':
        return 'Minimal filtering - only blocks adult and explicit content';
      case 'custom':
        return 'Custom filtering - you choose which keywords to block';
      default:
        return '';
    }
  };

  // Predefined keyword categories
  const keywordCategories = {
    'Adult Content': ['adult', 'explicit', 'pornography', 'nsfw', 'xxx'],
    'Violence': ['violence', 'gore', 'murder', 'assault', 'weapons'],
    'Gambling': ['gambling', 'casino', 'betting', 'poker', 'lottery'],
    'Drugs': ['drugs', 'narcotics', 'marijuana', 'cocaine', 'meth'],
    'Hate Speech': ['hate', 'racism', 'sexism', 'discrimination', 'slur'],
    'Illegal': ['piracy', 'torrent', 'crack', 'hacking', 'fraud'],
    'Profanity': ['profanity', 'curse', 'swear', 'vulgar', 'obscene'],
  };

  const handleAddKeyword = () => {
    if (newKeyword.trim() && !customKeywords.includes(newKeyword.trim().toLowerCase())) {
      setCustomKeywords([...customKeywords, newKeyword.trim().toLowerCase()]);
      setNewKeyword('');
    }
  };

  const handleRemoveKeyword = (keyword: string) => {
    setCustomKeywords(customKeywords.filter(k => k !== keyword));
  };

  const handleAddCategoryKeywords = (keywords: string[]) => {
    const newKeywords = keywords.filter(k => !customKeywords.includes(k));
    setCustomKeywords([...customKeywords, ...newKeywords]);
  };

  const handleApplyKeywordsToPolicy = async () => {
    if (!selectedPolicyId) {
      setError('Please select a policy first');
      return;
    }

    try {
      setSaving(true);
      
      // Get the selected policy
      const policy = policies.find(p => p.policy_id === selectedPolicyId);
      if (!policy) {
        throw new Error('Policy not found');
      }

      // Update policy with custom keywords
      await api.updatePolicy(selectedPolicyId, {
        ...policy,
        search_permissions: {
          ...policy.search_permissions,
          blocked_keywords: customKeywords
        },
        target_group_ids: selectedGroups.length > 0 ? selectedGroups : policy.target_group_ids
      });

      setSuccess(true);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to apply keywords to policy');
    } finally {
      setSaving(false);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Validate it's a CSV file
      if (!file.name.endsWith('.csv')) {
        setError('Please select a CSV file');
        return;
      }
      
      setCsvFile(file);
      setCsvFileName(file.name);
      
      // Read file to set path (for display)
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        // Validate CSV has correct headers
        const firstLine = content.split('\n')[0];
        if (!firstLine.includes('email') || !firstLine.includes('name')) {
          setError('CSV must contain at least "email" and "name" columns');
          setCsvFile(null);
          setCsvFileName('');
          return;
        }
        
        // Count rows
        const rows = content.split('\n').filter(line => line.trim()).length - 1; // -1 for header
        setCsvPath(`${file.name} (${rows} users)`);
      };
      reader.readAsText(file);
    }
  };

  const handleBrowseFile = () => {
    fileInputRef.current?.click();
  };

  const handleClearFile = () => {
    setCsvFile(null);
    setCsvFileName('');
    setCsvPath('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleImportCSV = async () => {
    if (!csvFile) {
      setError('Please select a CSV file first');
      return;
    }

    try {
      setSaving(true);
      setError(null);
      
      const result = await api.importUsersCSV(csvFile);
      
      // Update sync status
      setLastSyncTime(new Date().toISOString());
      setLastSyncStatus(result.status === 'success' ? 'success' : 'failed');
      setSyncedUserCount(result.users_created + result.users_updated);
      setSyncedGroupCount(result.groups_found || 0);
      
      // Update settings to mark CSV as enabled if successful
      if (result.status === 'success' || result.status === 'partial') {
        setCsvEnabled(true);
        await handleSave(); // Save settings to persist CSV enabled state
      }
      
      // Show success message
      setSuccess(true);
      setError(result.errors && result.errors.length > 0 ? 
        `Import completed with ${result.errors.length} errors. Check console for details.` : 
        null
      );
      
      if (result.errors && result.errors.length > 0) {
        console.error('CSV Import Errors:', result.errors);
      }
      
      // Clear file after import
      handleClearFile();
      
    } catch (err: any) {
      setLastSyncStatus('failed');
      setError(err.message || 'Failed to import CSV file');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography>Loading settings...</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4">System Settings</Typography>
        <Box>
          <Button
            startIcon={<RefreshIcon />}
            onClick={loadSettings}
            sx={{ mr: 2 }}
            disabled={loading || saving}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={handleSave}
            disabled={loading || saving}
          >
            Save Changes
          </Button>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* OpenTelemetry Configuration */}
        <Grid item xs={12}>
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">OpenTelemetry Configuration</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <TextField
                  fullWidth
                  label="OTEL Collector Endpoint"
                  value={otelEndpoint}
                  onChange={(e) => setOtelEndpoint(e.target.value)}
                  helperText="gRPC endpoint for OpenTelemetry Collector (e.g., http://localhost:5317)"
                />
                <Alert severity="info">
                  Changes to OTEL endpoint require service restart to take effect.
                </Alert>
              </Box>
            </AccordionDetails>
          </Accordion>
        </Grid>

        {/* Search Policy Configuration */}
        <Grid item xs={12}>
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Enterprise Search Policies</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                <FormControl fullWidth>
                  <InputLabel>Policy Level</InputLabel>
                  <Select
                    value={searchPolicyLevel}
                    label="Policy Level"
                    onChange={(e) => setSearchPolicyLevel(e.target.value as any)}
                  >
                    <MenuItem value="strict">
                      <Box>
                        <Typography variant="body1">Strict</Typography>
                        <Typography variant="caption" color="text.secondary">
                          Maximum content filtering
                        </Typography>
                      </Box>
                    </MenuItem>
                    <MenuItem value="moderate">
                      <Box>
                        <Typography variant="body1">Moderate (Recommended)</Typography>
                        <Typography variant="caption" color="text.secondary">
                          Balanced content filtering
                        </Typography>
                      </Box>
                    </MenuItem>
                    <MenuItem value="open">
                      <Box>
                        <Typography variant="body1">Open</Typography>
                        <Typography variant="caption" color="text.secondary">
                          Minimal content filtering
                        </Typography>
                      </Box>
                    </MenuItem>
                    <MenuItem value="custom">
                      <Box>
                        <Typography variant="body1">Custom</Typography>
                        <Typography variant="caption" color="text.secondary">
                          Define your own blocked keywords
                        </Typography>
                      </Box>
                    </MenuItem>
                  </Select>
                </FormControl>

                <Alert severity="info">
                  {getPolicyDescription(searchPolicyLevel)}
                </Alert>

                {searchPolicyLevel === 'custom' ? (
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Custom Blocked Keywords
                    </Typography>
                    
                    {/* Add keyword input */}
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <TextField
                        fullWidth
                        size="small"
                        label="Add keyword"
                        value={newKeyword}
                        onChange={(e) => setNewKeyword(e.target.value)}
                        onKeyPress={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault();
                            handleAddKeyword();
                          }
                        }}
                        placeholder="Type keyword and press Enter"
                      />
                      <Button 
                        variant="contained" 
                        onClick={handleAddKeyword}
                        disabled={!newKeyword.trim()}
                      >
                        Add
                      </Button>
                    </Box>

                    {/* Keyword categories */}
                    <Box>
                      <Typography variant="body2" gutterBottom sx={{ fontWeight: 'bold' }}>
                        Quick Add from Categories:
                      </Typography>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                        {Object.entries(keywordCategories).map(([category, keywords]) => (
                          <Box key={category}>
                            <Button
                              size="small"
                              variant="outlined"
                              onClick={() => handleAddCategoryKeywords(keywords)}
                              sx={{ mr: 1, mb: 0.5 }}
                            >
                              + {category} ({keywords.length})
                            </Button>
                          </Box>
                        ))}
                      </Box>
                    </Box>

                    {/* Current keywords */}
                    <Box>
                      <Typography variant="body2" gutterBottom sx={{ fontWeight: 'bold' }}>
                        Active Keywords ({customKeywords.length}):
                      </Typography>
                      {customKeywords.length > 0 ? (
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                          {customKeywords.map((keyword) => (
                            <Chip
                              key={keyword}
                              label={keyword}
                              onDelete={() => handleRemoveKeyword(keyword)}
                              size="small"
                              color="primary"
                            />
                          ))}
                        </Box>
                      ) : (
                        <Alert severity="warning" sx={{ mt: 1 }}>
                          No keywords added yet. Add keywords manually or select from categories above.
                        </Alert>
                      )}
                    </Box>

                    <Divider sx={{ my: 3 }} />

                    {/* Policy Assignment Section */}
                    <Box>
                      <Typography variant="h6" gutterBottom>
                        Apply Keywords to Policy
                      </Typography>
                      <Alert severity="info" sx={{ mb: 2 }}>
                        Select a policy and optionally assign it to specific groups. 
                        The custom keywords will be added to the policy's blocked keywords list.
                      </Alert>
                      
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                        <FormControl fullWidth>
                          <InputLabel>Select Policy</InputLabel>
                          <Select
                            value={selectedPolicyId}
                            label="Select Policy"
                            onChange={(e) => setSelectedPolicyId(e.target.value)}
                          >
                            {policies.map((policy) => (
                              <MenuItem key={policy.policy_id} value={policy.policy_id}>
                                {policy.policy_name} (Priority: {policy.priority})
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>

                        <FormControl fullWidth>
                          <InputLabel>Assign to Groups (Optional)</InputLabel>
                          <Select
                            multiple
                            value={selectedGroups}
                            label="Assign to Groups (Optional)"
                            onChange={(e) => setSelectedGroups(e.target.value as string[])}
                            renderValue={(selected) => (
                              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                {selected.map((value) => (
                                  <Chip key={value} label={value} size="small" />
                                ))}
                              </Box>
                            )}
                          >
                            {groups.map((group) => (
                              <MenuItem key={group.group_id} value={group.group_id}>
                                {group.group_id} ({group.user_count} users)
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>

                        <Button
                          variant="contained"
                          color="primary"
                          onClick={handleApplyKeywordsToPolicy}
                          disabled={!selectedPolicyId || customKeywords.length === 0 || saving}
                          startIcon={<SaveIcon />}
                        >
                          Apply Keywords to Policy
                        </Button>
                      </Box>
                    </Box>
                  </Box>
                ) : (
                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      Blocked Keywords ({getBlockKeywordsByLevel(searchPolicyLevel).length})
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {getBlockKeywordsByLevel(searchPolicyLevel).map((keyword) => (
                        <Chip key={keyword} label={keyword} size="small" />
                      ))}
                    </Box>
                  </Box>
                )}
              </Box>
            </AccordionDetails>
          </Accordion>
        </Grid>

        {/* Parental Controls */}
        <Grid item xs={12}>
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Parental Controls</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={parentalControlsEnabled}
                      onChange={(e) => setParentalControlsEnabled(e.target.checked)}
                    />
                  }
                  label="Enable Parental Controls"
                />

                {parentalControlsEnabled && (
                  <>
                    <Divider sx={{ my: 1 }} />
                    
                    <FormControl fullWidth>
                      <InputLabel>Minimum Age Requirement</InputLabel>
                      <Select
                        value={ageRestriction}
                        label="Minimum Age Requirement"
                        onChange={(e) => setAgeRestriction(Number(e.target.value))}
                      >
                        <MenuItem value={13}>13+ (Teen)</MenuItem>
                        <MenuItem value={16}>16+ (Young Adult)</MenuItem>
                        <MenuItem value={18}>18+ (Adult)</MenuItem>
                      </Select>
                    </FormControl>

                    <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                      Content Filters
                    </Typography>

                    <FormControlLabel
                      control={
                        <Switch
                          checked={blockAdultContent}
                          onChange={(e) => setBlockAdultContent(e.target.checked)}
                        />
                      }
                      label="Block Adult Content"
                    />

                    <FormControlLabel
                      control={
                        <Switch
                          checked={blockViolence}
                          onChange={(e) => setBlockViolence(e.target.checked)}
                        />
                      }
                      label="Block Violence & Gore"
                    />

                    <Alert severity="warning">
                      Parental controls will filter search results based on the selected age restriction
                      and content filters. This applies to all API clients unless overridden.
                    </Alert>
                  </>
                )}
              </Box>
            </AccordionDetails>
          </Accordion>
        </Grid>

        {/* User & Authentication Settings */}
        <Grid item xs={12}>
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">User & Authentication</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={userSyncEnabled}
                      onChange={(e) => setUserSyncEnabled(e.target.checked)}
                    />
                  }
                  label="Enable User Synchronization"
                />

                {userSyncEnabled && (
                  <>
                    <Divider sx={{ my: 1 }} />
                    
                    <Typography variant="subtitle2" gutterBottom>
                      Sync Settings
                    </Typography>
                    
                    <Grid container spacing={2}>
                      <Grid item xs={12} md={6}>
                        <FormControl fullWidth>
                          <InputLabel>Sync Interval</InputLabel>
                          <Select
                            value={syncIntervalHours}
                            label="Sync Interval"
                            onChange={(e) => setSyncIntervalHours(Number(e.target.value))}
                          >
                            <MenuItem value={1}>Every Hour</MenuItem>
                            <MenuItem value={6}>Every 6 Hours</MenuItem>
                            <MenuItem value={12}>Every 12 Hours</MenuItem>
                            <MenuItem value={24}>Daily</MenuItem>
                            <MenuItem value={168}>Weekly</MenuItem>
                          </Select>
                        </FormControl>
                      </Grid>
                    </Grid>

                    <FormControlLabel
                      control={
                        <Switch
                          checked={groupSyncEnabled}
                          onChange={(e) => setGroupSyncEnabled(e.target.checked)}
                        />
                      }
                      label="Sync Groups/OUs from Directory"
                    />

                    <FormControlLabel
                      control={
                        <Switch
                          checked={autoCreateUsers}
                          onChange={(e) => setAutoCreateUsers(e.target.checked)}
                        />
                      }
                      label="Auto-create Users on First Login"
                    />

                    <FormControlLabel
                      control={
                        <Switch
                          checked={autoAssignPolicies}
                          onChange={(e) => setAutoAssignPolicies(e.target.checked)}
                        />
                      }
                      label="Auto-assign Policies Based on Groups"
                    />

                    <Divider sx={{ my: 2 }} />
                    
                    <Typography variant="subtitle2" gutterBottom>
                      Directory Sources
                    </Typography>

                    {/* Active Directory */}
                    <Card variant="outlined">
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                          <Typography variant="h6">Active Directory (LDAP)</Typography>
                          <Switch
                            checked={adEnabled}
                            onChange={(e) => setAdEnabled(e.target.checked)}
                          />
                        </Box>
                        {adEnabled && (
                          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                            <TextField
                              fullWidth
                              label="Server URL"
                              value={adServerUrl}
                              onChange={(e) => setAdServerUrl(e.target.value)}
                              placeholder="ldap://dc.example.com:389"
                              helperText="LDAP server address"
                            />
                            <TextField
                              fullWidth
                              label="Domain"
                              value={adDomain}
                              onChange={(e) => setAdDomain(e.target.value)}
                              placeholder="example.com"
                              helperText="Active Directory domain"
                            />
                          </Box>
                        )}
                      </CardContent>
                    </Card>

                    {/* Microsoft Entra ID */}
                    <Card variant="outlined">
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                          <Typography variant="h6">Microsoft Entra ID (Azure AD)</Typography>
                          <Switch
                            checked={entraEnabled}
                            onChange={(e) => setEntraEnabled(e.target.checked)}
                          />
                        </Box>
                        {entraEnabled && (
                          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                            <TextField
                              fullWidth
                              label="Tenant ID"
                              value={entraTenantId}
                              onChange={(e) => setEntraTenantId(e.target.value)}
                              placeholder="00000000-0000-0000-0000-000000000000"
                              helperText="Azure AD tenant ID"
                            />
                            <TextField
                              fullWidth
                              label="Client ID (Application ID)"
                              value={entraClientId}
                              onChange={(e) => setEntraClientId(e.target.value)}
                              placeholder="00000000-0000-0000-0000-000000000000"
                              helperText="Application (client) ID from Azure portal"
                            />
                            <Alert severity="info">
                              Client secret should be configured in environment variables for security
                            </Alert>
                          </Box>
                        )}
                      </CardContent>
                    </Card>

                    {/* Okta */}
                    <Card variant="outlined">
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                          <Typography variant="h6">Okta</Typography>
                          <Switch
                            checked={oktaEnabled}
                            onChange={(e) => setOktaEnabled(e.target.checked)}
                          />
                        </Box>
                        {oktaEnabled && (
                          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                            <TextField
                              fullWidth
                              label="Okta Domain"
                              value={oktaDomain}
                              onChange={(e) => setOktaDomain(e.target.value)}
                              placeholder="example.okta.com"
                              helperText="Your Okta organization domain"
                            />
                            <Alert severity="info">
                              API token should be configured in environment variables for security
                            </Alert>
                          </Box>
                        )}
                      </CardContent>
                    </Card>

                    {/* Keycloak */}
                    <Card variant="outlined">
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                          <Typography variant="h6">Keycloak (OIDC)</Typography>
                          <Switch
                            checked={keycloakEnabled}
                            onChange={(e) => setKeycloakEnabled(e.target.checked)}
                          />
                        </Box>
                        {keycloakEnabled && (
                          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                            <TextField
                              fullWidth
                              label="Keycloak URL"
                              value={keycloakUrl}
                              onChange={(e) => setKeycloakUrl(e.target.value)}
                              placeholder="https://keycloak.example.com"
                              helperText="Base URL of your Keycloak server"
                            />
                            <TextField
                              fullWidth
                              label="Realm"
                              value={keycloakRealm}
                              onChange={(e) => setKeycloakRealm(e.target.value)}
                              placeholder="websearch"
                              helperText="Keycloak realm name"
                            />
                            <TextField
                              fullWidth
                              label="Client ID"
                              value={keycloakClientId}
                              onChange={(e) => setKeycloakClientId(e.target.value)}
                              placeholder="websearch-api"
                              helperText="Client ID registered in Keycloak"
                            />
                            <TextField
                              fullWidth
                              label="Client Secret"
                              type="password"
                              value={keycloakClientSecret}
                              onChange={(e) => setKeycloakClientSecret(e.target.value)}
                              placeholder="••••••••"
                              helperText="Client secret from Keycloak credentials tab"
                            />
                            <Alert severity="info">
                              Users with the <strong>websearch-admin</strong> realm role will receive admin access.
                              All other authenticated users receive agent-level access.
                              Changes require a service restart to take effect.
                            </Alert>
                          </Box>
                        )}
                      </CardContent>
                    </Card>

                    {/* CSV Import */}
                    <Card variant="outlined">
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                          <Typography variant="h6">CSV Import</Typography>
                          <Switch
                            checked={csvEnabled}
                            onChange={(e) => setCsvEnabled(e.target.checked)}
                          />
                        </Box>
                        {csvEnabled && (
                          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                            {/* Hidden file input */}
                            <input
                              ref={fileInputRef}
                              type="file"
                              accept=".csv"
                              style={{ display: 'none' }}
                              onChange={handleFileSelect}
                            />
                            
                            {/* File selection UI */}
                            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                              <TextField
                                fullWidth
                                label="Selected File"
                                value={csvPath}
                                placeholder="No file selected"
                                helperText="Upload a CSV file with user data"
                                InputProps={{
                                  readOnly: true,
                                  endAdornment: csvFile && (
                                    <IconButton size="small" onClick={handleClearFile}>
                                      <CloseIcon />
                                    </IconButton>
                                  ),
                                }}
                              />
                              <Button
                                variant="contained"
                                startIcon={<UploadFileIcon />}
                                onClick={handleBrowseFile}
                              >
                                Browse
                              </Button>
                            </Box>
                            
                            <Alert severity="info">
                              <Typography variant="body2" gutterBottom>
                                <strong>CSV Format (Required columns):</strong>
                              </Typography>
                              <Typography variant="body2" component="pre" sx={{ fontFamily: 'monospace', mt: 1 }}>
                                email,name,department,groups
                              </Typography>
                              <Typography variant="body2" sx={{ mt: 1 }}>
                                Optional columns: title, manager_email, location, quota_per_day, quota_per_month
                              </Typography>
                              <Typography variant="body2" sx={{ mt: 1 }}>
                                Groups should be comma-separated within quotes: "group1,group2,group3"
                              </Typography>
                            </Alert>
                            
                            {csvFile && (
                              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                                <Alert severity="success">
                                  File ready: <strong>{csvFileName}</strong>
                                </Alert>
                                <Button
                                  variant="contained"
                                  color="primary"
                                  onClick={handleImportCSV}
                                  disabled={saving}
                                  startIcon={<UploadFileIcon />}
                                >
                                  {saving ? 'Importing...' : 'Import Users Now'}
                                </Button>
                              </Box>
                            )}
                            
                            {/* Sync Status */}
                            {lastSyncTime && (
                              <Card variant="outlined" sx={{ bgcolor: lastSyncStatus === 'success' ? 'success.50' : lastSyncStatus === 'failed' ? 'error.50' : 'info.50' }}>
                                <CardContent>
                                  <Typography variant="subtitle2" gutterBottom>
                                    Last Sync Status
                                  </Typography>
                                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                      <Typography variant="body2">Status:</Typography>
                                      <Chip 
                                        label={lastSyncStatus?.toUpperCase()} 
                                        color={lastSyncStatus === 'success' ? 'success' : lastSyncStatus === 'failed' ? 'error' : 'default'}
                                        size="small"
                                      />
                                    </Box>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                      <Typography variant="body2">Time:</Typography>
                                      <Typography variant="body2" fontWeight="bold">
                                        {new Date(lastSyncTime).toLocaleString()}
                                      </Typography>
                                    </Box>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                      <Typography variant="body2">Users Imported:</Typography>
                                      <Typography variant="body2" fontWeight="bold">
                                        {syncedUserCount}
                                      </Typography>
                                    </Box>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                      <Typography variant="body2">Groups Created:</Typography>
                                      <Typography variant="body2" fontWeight="bold">
                                        {syncedGroupCount}
                                      </Typography>
                                    </Box>
                                  </Box>
                                </CardContent>
                              </Card>
                            )}
                            
                            <Box sx={{ display: 'flex', gap: 1 }}>
                              <Button
                                variant="outlined"
                                size="small"
                                href="/sample_users.csv"
                                download="sample_users.csv"
                              >
                                Download Basic Sample
                              </Button>
                              <Button
                                variant="outlined"
                                size="small"
                                href="/sample_users_detailed.csv"
                                download="sample_users_detailed.csv"
                              >
                                Download Detailed Sample
                              </Button>
                            </Box>
                          </Box>
                        )}
                      </CardContent>
                    </Card>

                    <Alert severity="warning">
                      User synchronization will import users and groups from enabled directory sources.
                      Policies can be automatically assigned based on group membership.
                    </Alert>
                  </>
                )}
              </Box>
            </AccordionDetails>
          </Accordion>
        </Grid>

        {/* Observability Integrations */}
        <Grid item xs={12}>
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Observability Integrations</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={3}>
                <Grid item xs={12} md={4}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Grafana
                      </Typography>
                      <TextField
                        fullWidth
                        size="small"
                        label="Grafana URL"
                        value={grafanaUrl}
                        onChange={(e) => setGrafanaUrl(e.target.value)}
                        sx={{ mb: 2 }}
                      />
                      <Typography variant="body2" color="text.secondary">
                        Metrics visualization and dashboards
                      </Typography>
                    </CardContent>
                    <CardActions>
                      <Button
                        size="small"
                        endIcon={<OpenInNewIcon />}
                        onClick={() => window.open(grafanaUrl, '_blank')}
                      >
                        Open Grafana
                      </Button>
                    </CardActions>
                  </Card>
                </Grid>

                <Grid item xs={12} md={4}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Prometheus
                      </Typography>
                      <TextField
                        fullWidth
                        size="small"
                        label="Prometheus URL"
                        value={prometheusUrl}
                        onChange={(e) => setPrometheusUrl(e.target.value)}
                        sx={{ mb: 2 }}
                      />
                      <Typography variant="body2" color="text.secondary">
                        Metrics collection and storage
                      </Typography>
                    </CardContent>
                    <CardActions>
                      <Button
                        size="small"
                        endIcon={<OpenInNewIcon />}
                        onClick={() => window.open(prometheusUrl, '_blank')}
                      >
                        Open Prometheus
                      </Button>
                    </CardActions>
                  </Card>
                </Grid>

                <Grid item xs={12} md={4}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Jaeger
                      </Typography>
                      <TextField
                        fullWidth
                        size="small"
                        label="Jaeger URL"
                        value={jaegerUrl}
                        onChange={(e) => setJaegerUrl(e.target.value)}
                        sx={{ mb: 2 }}
                      />
                      <Typography variant="body2" color="text.secondary">
                        Distributed tracing and monitoring
                      </Typography>
                    </CardContent>
                    <CardActions>
                      <Button
                        size="small"
                        endIcon={<OpenInNewIcon />}
                        onClick={() => window.open(jaegerUrl, '_blank')}
                      >
                        Open Jaeger
                      </Button>
                    </CardActions>
                  </Card>
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Grid>
      </Grid>


      {/* Danger Zone */}
      <Box sx={{ mt: 4 }}>
        <Accordion sx={{ bgcolor: 'error.lighter', border: '1px solid', borderColor: 'error.main' }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6" color="error">⚠️ Danger Zone</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Alert severity="error" sx={{ mb: 2 }}>
              <strong>Warning:</strong> The actions in this section are irreversible and will permanently delete data.
            </Alert>

            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Reset to Defaults
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  This will delete all users (except admin), groups (except admins), custom policies,
                  API keys, and old audit logs. The admin user will be reset to default credentials (admin/admin).
                </Typography>
                <Typography variant="body2" color="error" paragraph>
                  <strong>This action cannot be undone!</strong>
                </Typography>

                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" gutterBottom>
                    What will be deleted:
                  </Typography>
                  <ul>
                    <li>All users except admin</li>
                    <li>All groups except admins</li>
                    <li>All custom policies</li>
                    <li>All API keys</li>
                    <li>Audit logs older than 7 days</li>
                  </ul>
                  <Typography variant="body2" gutterBottom sx={{ mt: 2 }}>
                    What will be preserved:
                  </Typography>
                  <ul>
                    <li>Admin user (password reset to admin/admin)</li>
                    <li>Admins group</li>
                    <li>Default policies (enterprise_default, safe_search_strict)</li>
                    <li>Recent audit logs (last 7 days)</li>
                  </ul>
                </Box>
              </CardContent>
              <CardActions>
                <Button
                  variant="contained"
                  color="error"
                  onClick={async () => {
                    if (!window.confirm(
                      'Are you absolutely sure you want to reset the system to defaults?\n\n' +
                      'This will delete all users, groups, policies, and API keys except the defaults.\n\n' +
                      'This action CANNOT be undone!\n\n' +
                      'Type "RESET" in the next prompt to confirm.'
                    )) {
                      return;
                    }

                    const confirmation = window.prompt('Type RESET to confirm:');
                    if (confirmation !== 'RESET') {
                      alert('Reset cancelled - confirmation text did not match');
                      return;
                    }

                    try {
                      setLoading(true);
                      const apiKey = localStorage.getItem('adminApiKey');
                      const response = await fetch('/api/v1/admin/reset-to-defaults', {
                        method: 'POST',
                        headers: {
                          'X-API-Key': apiKey || '',
                          'Content-Type': 'application/json',
                        },
                      });
                      
                      if (!response.ok) {
                        throw new Error('Failed to reset system');
                      }
                      
                      const data = await response.json();
                      alert(
                        'System reset successfully!\n\n' +
                        `Deleted:\n` +
                        `- Users: ${data.deleted.users}\n` +
                        `- Groups: ${data.deleted.groups}\n` +
                        `- Policies: ${data.deleted.policies}\n` +
                        `- Clients: ${data.deleted.clients}\n\n` +
                        'Admin credentials reset to: admin/admin\n\n' +
                        'You will need to log in again.'
                      );
                      // Clear stored API key and redirect to login
                      localStorage.removeItem('adminApiKey');
                      window.location.href = '/';
                    } catch (err: any) {
                      setError(err.message || 'Failed to reset system');
                    } finally {
                      setLoading(false);
                    }
                  }}
                  disabled={loading}
                >
                  Reset System to Defaults
                </Button>
              </CardActions>
            </Card>
          </AccordionDetails>
        </Accordion>
      </Box>
      {/* Success/Error Notifications */}
      <Snackbar
        open={success}
        autoHideDuration={3000}
        onClose={() => setSuccess(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert severity="success" onClose={() => setSuccess(false)}>
          Settings saved successfully!
        </Alert>
      </Snackbar>

      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      </Snackbar>
    </Box>
  );
}
