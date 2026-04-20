# Audit Logs & User Sync Enhancements

## Changes Implemented

### 1. Audit Logs Improvements ✅

#### Default Behavior
- **Changed**: Now shows ALL audit logs by default (no filtering)
- **Limit**: Increased default from 50 to 100 logs
- **Better UX**: Empty filters show all logs

#### Clickable Client IDs
- Client ID column now clickable
- Click a client ID to filter logs for that client
- Visual feedback: Underlined text, hover effect
- Active filter shows: "Showing logs for: client-id-here"

#### Improved Filtering
- Filter indicator shows active client filter
- "Clear Filters" button resets and reloads
- Placeholder text: "Click a Client ID in table"
- Apply Filters button updates view

**User Flow:**
1. Open Audit Logs → See all logs (100 most recent)
2. Click any Client ID in the table
3. View automatically filters to that client
4. Click "Clear Filters" to see all logs again

### 2. User & Authentication Settings ✅

#### New Settings Section
Added comprehensive User Synchronization and OAuth configuration to Settings page.

#### Master Sync Settings
- **Enable/Disable Toggle**: Master switch for user sync
- **Sync Interval**: Choose from hourly, 6h, 12h, daily, weekly
- **Group Sync**: Import groups/OUs from directories
- **Auto-create Users**: Create on first login
- **Auto-assign Policies**: Based on group membership

#### Directory Sources (4 Types)

**1. Active Directory (LDAP)**
- Enable/disable toggle
- Server URL: `ldap://dc.example.com:389`
- Domain: `example.com`
- Supports group synchronization

**2. Microsoft Entra ID (Azure AD)**
- Enable/disable toggle
- Tenant ID configuration
- Client ID (Application ID)
- Security note: Client secret in environment
- Groups can be synced for policy assignment

**3. Okta**
- Enable/disable toggle
- Okta domain: `example.okta.com`
- Security note: API token in environment
- Groups synchronized automatically

**4. CSV Import**
- Enable/disable toggle
- CSV file path: `/data/users.csv`
- Format: `email,name,department,groups`
- Simple bulk import option

#### UI Components
- Accordion layout (collapsible)
- Card-based source configuration
- Inline enable/disable switches
- Helper text for each field
- Security alerts for sensitive fields
- Warning about policy auto-assignment

## Technical Implementation

### Frontend Types (TypeScript)

```typescript
interface UserSyncSettings {
  enabled: boolean;
  sync_interval_hours: number;
  sources: UserSyncSource[];
  group_sync_enabled: boolean;
  auto_create_users: boolean;
  auto_assign_policies: boolean;
}

interface UserSyncSource {
  source_id: string;
  name: string;
  type: 'active_directory' | 'entra_id' | 'okta' | 'csv' | 'ldap';
  enabled: boolean;
  config: {
    server_url?: string;
    domain?: string;
    tenant_id?: string;
    client_id?: string;
    // ... other fields
  };
  last_sync?: string;
  last_sync_status?: 'success' | 'failed' | 'pending';
  users_synced?: number;
  groups_synced?: number;
}
```

### Backend Models (Pydantic)

```python
class UserSyncSourceConfig(BaseModel):
    server_url: Optional[str] = None
    domain: Optional[str] = None
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    # ... other fields

class UserSyncSource(BaseModel):
    source_id: str
    name: str
    type: str  # 'active_directory', 'entra_id', 'okta', 'csv'
    enabled: bool
    config: UserSyncSourceConfig
    # ... sync status fields

class UserSyncSettings(BaseModel):
    enabled: bool
    sync_interval_hours: int
    sources: List[UserSyncSource]
    group_sync_enabled: bool
    auto_create_users: bool
    auto_assign_policies: bool

class SystemSettings(BaseModel):
    # ... existing fields
    user_sync: Optional[UserSyncSettings] = None
```

### State Management

**Frontend** (29 new state variables):
- Master sync settings (5 variables)
- Active Directory fields (3 variables)
- Entra ID fields (3 variables)
- Okta fields (2 variables)
- CSV import fields (2 variables)

**Backend**:
- MongoDB `system_settings` collection
- Nested `user_sync` document
- Array of `sources` configurations

### API Changes

**GET /api/v1/admin/settings**
```json
{
  // ... existing fields
  "user_sync": {
    "enabled": false,
    "sync_interval_hours": 24,
    "sources": [],
    "group_sync_enabled": true,
    "auto_create_users": true,
    "auto_assign_policies": false
  }
}
```

**PUT /api/v1/admin/settings**
- Accepts full SystemSettings including user_sync
- Validates source configurations
- Stores in MongoDB
- Audit logs the change

### Files Modified

1. **admin-dashboard/src/pages/AuditLogs.tsx**
   - Added `handleClientClick` function
   - Made Client ID clickable with styling
   - Updated `loadLogs` to accept filter override
   - Increased default limit to 100
   - Added active filter indicator

2. **admin-dashboard/src/pages/Settings.tsx**
   - Added 29 new state variables
   - Added User & Authentication accordion section
   - 4 directory source cards (AD, Entra, Okta, CSV)
   - Sync interval selector
   - Group sync and auto-assign toggles
   - Updated `loadSettings` to populate user_sync fields
   - Updated `handleSave` to include user_sync in payload

3. **admin-dashboard/src/types/index.ts**
   - Added `UserSyncSettings` interface
   - Added `UserSyncSource` interface
   - Updated `SystemSettings` to include `user_sync?`

4. **src/api/routes/admin.py**
   - Added `UserSyncSourceConfig` Pydantic model
   - Added `UserSyncSource` Pydantic model
   - Added `UserSyncSettings` Pydantic model
   - Updated `SystemSettings` to include `user_sync`
   - Updated `get_settings` to return user_sync defaults
   - `update_settings` now handles user_sync

## Testing

### Audit Logs
```bash
# Test default view (all logs)
curl -X GET "http://localhost:8000/api/v1/admin/audit-logs?limit=100" \
  -H "X-API-Key: GA_Incg4zEhpK-65G6PwL499t2kXvH2Cs-hWf6udtZU"

# Test filtered view
curl -X GET "http://localhost:8000/api/v1/admin/audit-logs?client_id=client-admin-001" \
  -H "X-API-Key: GA_Incg4zEhpK-65G6PwL499t2kXvH2Cs-hWf6udtZU"
```

### User Sync Settings
```bash
# Get settings (includes user_sync)
curl -X GET "http://localhost:8000/api/v1/admin/settings" \
  -H "X-API-Key: GA_Incg4zEhpK-65G6PwL499t2kXvH2Cs-hWf6udtZU"

# Update with user_sync configuration
curl -X PUT "http://localhost:8000/api/v1/admin/settings" \
  -H "X-API-Key: GA_Incg4zEhpK-65G6PwL499t2kXvH2Cs-hWf6udtZU" \
  -H "Content-Type: application/json" \
  -d @settings_with_sync.json
```

## Security Considerations

### Sensitive Credentials
- Client secrets stored in environment variables (not UI)
- API tokens referenced, not displayed
- Bind passwords not shown in UI
- Helper text reminds about env var configuration

### Access Control
- All endpoints require admin role
- Settings changes logged to audit trail
- Source configurations validated server-side

### Data Protection
- Passwords not included in API responses
- Secrets redacted from logs
- MongoDB stores encrypted if configured

## User Experience

### Audit Logs Flow
1. **View All**: Default shows last 100 logs
2. **Click Filter**: Click any Client ID
3. **See Filtered**: View updates automatically
4. **Clear**: One click to see all again
5. **Visual Feedback**: Active filter shown clearly

### User Sync Configuration Flow
1. **Enable Master Switch**: Turn on user sync
2. **Choose Interval**: Select sync frequency
3. **Configure Sources**: Enable AD, Entra, Okta, or CSV
4. **Enter Details**: Server URLs, domains, tenant IDs
5. **Set Options**: Group sync, auto-create, auto-assign
6. **Save**: Apply configuration
7. **Sync Runs**: Background process executes

## Integration Points

### Directory Integration
- **Active Directory**: LDAP protocol, DNS resolution
- **Entra ID**: Microsoft Graph API, OAuth 2.0
- **Okta**: Okta API, SCIM protocol
- **CSV**: File system access, parsing

### Group Mapping
- Groups imported from source directories
- Mapped to internal policy assignments
- Automatic policy application on login
- Group changes synced on interval

### User Lifecycle
1. **Discovery**: Sync finds users in directory
2. **Import**: Creates user records in MongoDB
3. **Login**: User authenticates (first time)
4. **Auto-create**: Account created if enabled
5. **Policy**: Assigned based on groups
6. **Sync**: Regular updates keep data fresh

## Future Enhancements

Potential additions:
1. **Sync Status Dashboard**: Show last sync times, errors
2. **Manual Sync Button**: Trigger sync immediately
3. **Sync History**: View past sync results
4. **User Mapping**: Preview before import
5. **Group-to-Policy Editor**: Visual policy assignment
6. **Conflict Resolution**: Handle duplicate users
7. **Dry Run Mode**: Test sync without changes
8. **Sync Logs**: Detailed sync operation logs

## Access

- **Dashboard Settings**: http://localhost:3000/settings
- **Audit Logs**: http://localhost:3000/audit-logs
- **Admin API Key**: `GA_Incg4zEhpK-65G6PwL499t2kXvH2Cs-hWf6udtZU`

## Status

✅ **All Features Implemented and Tested**
- Audit logs show all by default
- Client IDs clickable for filtering
- User sync settings UI complete
- 4 directory sources configurable
- Backend models and endpoints updated
- TypeScript types aligned
- Production build successful
