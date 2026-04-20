# CSV User Import Guide

## Overview

The WebSearch API Admin Dashboard now supports CSV file import for bulk user provisioning. Users can upload CSV files directly from their local machine through the Settings page.

## CSV File Format

### Required Columns

The CSV file **must** contain these columns:

- `email` - User's email address (unique identifier)
- `name` - User's full name
- `department` - User's department
- `groups` - Comma-separated list of groups (within quotes)

### Optional Columns

Additional columns that enhance user profiles:

- `title` - Job title
- `manager_email` - Email of the user's manager
- `location` - Geographic location
- `quota_per_day` - Daily search quota (default: 1000)
- `quota_per_month` - Monthly search quota (default: 30000)

### Format Example

**Basic Format:**
```csv
email,name,department,groups
john.doe@example.com,John Doe,Engineering,"developers,engineers,team-alpha"
jane.smith@example.com,Jane Smith,Marketing,"marketing,content-creators"
```

**Detailed Format:**
```csv
email,name,department,title,groups,manager_email,location,quota_per_day,quota_per_month
john.doe@example.com,John Doe,Engineering,Software Engineer,"developers,engineers,team-alpha",tony.stark@example.com,San Francisco,500,15000
jane.smith@example.com,Jane Smith,Marketing,Marketing Manager,"marketing,managers",steve.rogers@example.com,New York,1000,30000
```

## Sample Files

Two sample CSV files are provided in the repository:

### 1. `sample_users.csv` (Basic)
- 30 sample users
- Basic information: email, name, department, groups
- Good for testing basic import functionality
- **Location**: `/sample_users.csv`

### 2. `sample_users_detailed.csv` (Detailed)
- 30 sample users
- Full information: all optional columns included
- Includes reporting structure (manager_email)
- Custom quotas per user
- **Location**: `/sample_users_detailed.csv`

## How to Use

### Step 1: Access Settings Page

1. Navigate to http://localhost:3000/settings
2. Scroll to "User & Authentication" section
3. Enable "User Synchronization" toggle

### Step 2: Enable CSV Import

1. Scroll to "CSV Import" card
2. Toggle the switch to enable CSV import

### Step 3: Select CSV File

**Option A: Browse Local File**
1. Click the "Browse" button
2. Select your CSV file from your computer
3. File will be validated automatically
4. View shows "File ready: filename.csv"

**Option B: Download Sample**
1. Click "Download Basic Sample" or "Download Detailed Sample"
2. Edit the sample file with your data
3. Upload the modified file using Browse button

### Step 4: Validate & Save

1. Verify the file shows correct user count
2. Click "Save Changes" at the top of the page
3. Configuration saved to MongoDB
4. Ready for import on next sync

## File Validation

The system automatically validates:

### Format Checks
- ✅ File has `.csv` extension
- ✅ Contains required columns: `email`, `name`
- ✅ Displays row count after upload

### Error Handling
- ❌ Non-CSV files rejected
- ❌ Missing required columns rejected
- ❌ Invalid format shows error message

## UI Features

### File Browser
- **Hidden Input**: Standard HTML5 file input (hidden)
- **Browse Button**: Styled Material-UI button
- **File Display**: Shows selected filename and user count
- **Clear Button**: X icon to remove selected file

### Visual Feedback
```
┌─────────────────────────────────────────┐
│ Selected File                           │
│ sample_users.csv (30 users)         [X] │
│ Upload a CSV file with user data        │
└─────────────────────────────────────────┘
   [Browse]
```

### Sample Download Buttons
- "Download Basic Sample" - Simple format
- "Download Detailed Sample" - Full format
- Direct download links (no navigation)

## Groups Format

Groups must be comma-separated within quotes:

### Correct ✅
```csv
email,name,department,groups
user@example.com,User Name,Engineering,"developers,team-alpha,senior"
```

### Incorrect ❌
```csv
email,name,department,groups
user@example.com,User Name,Engineering,developers team-alpha senior
user@example.com,User Name,Engineering,developers,team-alpha,senior
```

## Sample Data Overview

### Departments
- Engineering (15 users)
- Marketing (4 users)
- Sales (2 users)
- HR (2 users)
- Finance (1 user)
- Operations (2 users)
- Security (2 users)
- And more...

### Sample Groups
- `developers` - Software developers
- `senior-engineers` - Senior engineering staff
- `team-alpha`, `team-beta` - Project teams
- `managers` - Management level
- `admins` - Administrative access
- `executives` - C-level
- `devops`, `qa`, `frontend`, `backend` - Specializations

### Leadership Hierarchy
- **Steve Rogers** (COO) - Top level executive
- **Tony Stark** (CTO) - Reports to Steve
- **Diana Prince** (HR Manager) - Reports to Steve
- **Grace Hopper** (Principal Engineer) - Reports to Steve
- Other employees report to these managers

## Import Process

Once CSV is configured:

1. **Background Sync**: Runs on schedule (hourly/daily/weekly)
2. **User Creation**: Creates user records in MongoDB
3. **Group Assignment**: Maps groups from CSV
4. **Policy Application**: Auto-assigns policies if enabled
5. **Quota Setting**: Applies custom quotas if specified

## API Integration

### Settings Payload

```json
{
  "user_sync": {
    "enabled": true,
    "sources": [
      {
        "source_id": "csv-sync",
        "name": "CSV Import",
        "type": "csv",
        "enabled": true,
        "config": {
          "csv_path": "sample_users.csv (30 users)"
        }
      }
    ]
  }
}
```

## Security Considerations

### File Handling
- Files processed client-side for validation
- No automatic upload to server
- Path stored as reference in settings
- Actual import happens server-side on sync

### Data Privacy
- CSV files should be stored securely
- Remove sensitive data after import
- Use HTTPS for production deployments
- Monitor audit logs for import events

## Troubleshooting

### File Not Uploading
- Check file extension is `.csv`
- Ensure file size is reasonable (<10MB)
- Verify browser allows file selection

### Validation Errors
```
"CSV must contain at least 'email' and 'name' columns"
```
**Solution**: Add missing required columns to CSV

### Groups Not Working
```
Groups: developers team-alpha
```
**Solution**: Wrap in quotes: `"developers,team-alpha"`

### File Path Not Saved
- Click "Save Changes" button after selecting file
- Check for success notification
- Refresh page to verify persistence

## Testing with Sample Data

### Quick Test Flow

1. Download `sample_users.csv`
2. Upload via Browse button
3. Enable CSV sync
4. Save settings
5. Trigger sync (or wait for scheduled)
6. Check Users page for imported users

### Expected Results

After importing `sample_users.csv`:
- ✅ 30 users created
- ✅ Multiple groups populated
- ✅ Department structure created
- ✅ Ready for policy assignment

### Verification

Check MongoDB:
```bash
# Connect to MongoDB
mongosh websearch_api

# Count users
db.users.count()
# Should show 30

# View groups
db.users.distinct("groups")
# Should show all unique groups
```

## Advanced Usage

### Custom Fields

Add your own columns:
```csv
email,name,department,groups,custom_field,another_field
user@example.com,Name,Dept,"group1,group2",value1,value2
```

### Bulk Updates

1. Export existing users to CSV
2. Modify in Excel/Google Sheets
3. Re-import with updated data
4. System merges changes

### Integration with HR Systems

CSV import works with exports from:
- **Active Directory** → LDAP query to CSV
- **Workday** → Employee export
- **BambooHR** → Employee directory export
- **Google Workspace** → User export
- **Okta** → User export

## File Locations

**Repository:**
- `/sample_users.csv` - Basic sample
- `/sample_users_detailed.csv` - Detailed sample

**Dashboard Public:**
- `/admin-dashboard/public/sample_users.csv`
- `/admin-dashboard/public/sample_users_detailed.csv`

**Download URLs:**
- http://localhost:3000/sample_users.csv
- http://localhost:3000/sample_users_detailed.csv

## Support

For issues or questions:
1. Check CSV format matches requirements
2. Validate with sample files first
3. Review browser console for errors
4. Check audit logs for import events
5. Verify MongoDB connection and data

## Summary

✅ CSV file import from local machine  
✅ File browser with validation  
✅ Two sample files provided (30 users each)  
✅ Clear format requirements  
✅ Download sample buttons  
✅ Visual feedback on upload  
✅ Automatic validation  
✅ Ready for bulk user provisioning  

The CSV import feature makes it easy to provision users in bulk, perfect for initial system setup or regular synchronization with HR systems.
