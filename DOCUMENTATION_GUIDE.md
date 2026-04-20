# WebSearch API Documentation System

Comprehensive, searchable documentation integrated into the admin dashboard.

## Features

### Built-in Documentation Viewer
- **Markdown Rendering:** Full CommonMark support with syntax highlighting
- **Left Navigation:** Collapsible sections organized by topic
- **Search:** Real-time search across all documentation
- **Breadcrumbs:** Easy navigation tracking
- **Code Highlighting:** Syntax highlighting for multiple languages
- **Responsive Design:** Works on desktop, tablet, and mobile

### Documentation Structure

```
docs/
├── index.md                    # Main landing page
├── nav.json                    # Navigation structure
│
├── user/                       # End-user documentation
│   ├── getting-started.md      # Quick start guide (complete)
│   ├── authentication.md       # Auth methods (complete)
│   └── best-practices.md       # Usage tips (stub)
│
├── api/                        # API reference
│   └── reference.md            # Complete API docs (complete)
│
├── admin/                      # Administrator guides
│   ├── installation.md         # Setup guide (complete)
│   ├── user-management.md      # User admin (stub)
│   ├── policy-management.md    # Policy config (stub)
│   ├── monitoring.md           # Monitoring guide (complete)
│   └── security.md             # Security config (stub)
│
└── guides/                     # Topic-specific guides
    ├── search-policies.md      # Policy deep-dive (stub)
    ├── quotas.md               # Quota management (stub)
    ├── troubleshooting.md      # Common issues (stub)
    └── integration.md          # Integration guide (stub)
```

## Accessing Documentation

### Via Admin Dashboard

1. Log into the admin dashboard (http://localhost:3000)
2. Click **Documentation** in the left navigation
3. Browse sections or use search

### Direct File Access

Documentation files are markdown and can be viewed directly:

```bash
# View in terminal
cat docs/user/getting-started.md

# View in browser (after starting dashboard)
open http://localhost:3000/docs/index.md
```

## Navigation Structure

The `docs/nav.json` file controls the left navigation menu:

```json
{
  "sections": [
    {
      "title": "Section Name",
      "icon": "MaterialUIIconName",
      "items": [
        {
          "title": "Document Title",
          "path": "relative/path/to/file.md",
          "description": "Optional description"
        }
      ]
    }
  ]
}
```

**Available Icons:**
- `PlayArrow` - Getting started
- `Person` - User guides
- `Code` - API reference
- `AdminPanelSettings` - Admin docs
- `MenuBook` - Guides/tutorials

## Writing Documentation

### Markdown Features

All standard markdown is supported:

**Headings:**
```markdown
# H1 Title
## H2 Title
### H3 Title
```

**Code Blocks:**
````markdown
```python
def search(query):
    return api.search(query)
```
````

**Tables:**
```markdown
| Column 1 | Column 2 |
|----------|----------|
| Value 1  | Value 2  |
```

**Lists:**
```markdown
- Bullet point
- Another point
  - Nested point

1. Numbered item
2. Another item
```

**Links:**
```markdown
[Link Text](relative/path/to/doc.md)
[External Link](https://example.com)
```

**Images:**
```markdown
![Alt text](images/diagram.png)
```

### Style Guide

**Headings:**
- Use title case for H1
- Use sentence case for H2-H6
- One H1 per document
- Don't skip heading levels

**Code:**
- Always specify language for syntax highlighting
- Use `inline code` for commands, filenames, variables
- Use code blocks for multi-line examples

**Examples:**
- Provide working, copy-paste ready examples
- Include error handling in code samples
- Show both request and response for API calls

**Organization:**
- Start with overview/summary
- Group related content under H2 sections
- Use H3 for subsections
- Add "See also" links at the end

### Document Template

```markdown
# Document Title

Brief 1-2 sentence overview of what this document covers.

## Overview

More detailed introduction explaining:
- What the feature/topic is
- Why it's important
- When to use it

## Section 1

Content for first major section...

### Subsection 1.1

Detailed information...

### Subsection 1.2

More details...

## Section 2

Next major topic...

## Examples

Practical, working examples...

## Troubleshooting

Common issues and solutions...

## Next Steps

- [Related Doc 1](link.md)
- [Related Doc 2](link.md)
```

## Adding New Documentation

### 1. Create Markdown File

```bash
# Create new file in appropriate directory
touch docs/guides/new-topic.md

# Write content
nano docs/guides/new-topic.md
```

### 2. Add to Navigation

Edit `docs/nav.json` to add the new document:

```json
{
  "title": "Guides",
  "icon": "MenuBook",
  "items": [
    {
      "title": "New Topic",
      "path": "guides/new-topic.md",
      "description": "Brief description for search"
    }
  ]
}
```

### 3. Copy to Public Folder

The build process automatically copies docs, but for development:

```bash
cp -r docs admin-dashboard/public/
```

### 4. Rebuild Dashboard (if needed)

```bash
cd admin-dashboard
npm run build
```

## Complete Documentation Content

### Finished Documents

✅ **index.md** - Main documentation landing page  
✅ **user/getting-started.md** - Quick start with examples (7800+ chars)  
✅ **user/authentication.md** - Auth methods guide (7500+ chars)  
✅ **api/reference.md** - Complete API reference (8200+ chars)  
✅ **admin/installation.md** - Installation guide (10,000+ chars)  
✅ **admin/monitoring.md** - Monitoring & observability (9500+ chars)

### Stub Documents (To Be Expanded)

📝 **user/best-practices.md** - Usage optimization tips  
📝 **admin/user-management.md** - User/group administration  
📝 **admin/policy-management.md** - Policy configuration  
📝 **admin/security.md** - Security hardening  
📝 **guides/search-policies.md** - Policy deep-dive  
📝 **guides/quotas.md** - Quota management  
📝 **guides/troubleshooting.md** - Issue resolution  
📝 **guides/integration.md** - Integration patterns

## Customization

### Theming

The documentation viewer uses Material-UI theming. Customize in `Documentation.tsx`:

```typescript
// Adjust code block theme
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

// Use different theme
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
```

### Search Behavior

Search is case-insensitive and searches:
- Document titles
- Document descriptions
- Section titles (in nav.json)

Customize in `Documentation.tsx`:

```typescript
const query = searchQuery.toLowerCase();
const filteredSections = navigation.sections
  .map(section => ({
    ...section,
    items: section.items.filter(item =>
      item.title.toLowerCase().includes(query) ||
      item.description?.toLowerCase().includes(query)
    )
  }))
```

### Navigation Width

Adjust sidebar width in `Documentation.tsx`:

```typescript
<Paper
  sx={{
    width: 280,  // Change this value
    height: '100%',
    // ...
  }}
>
```

## Maintenance

### Updating Documentation

1. Edit markdown files in `docs/` directory
2. Copy to public folder: `cp -r docs admin-dashboard/public/`
3. Refresh browser (no rebuild needed in dev mode)

### Version Control

- ✅ **Commit:** `docs/` directory (source of truth)
- ✅ **Commit:** `docs/nav.json` (navigation config)
- ❌ **Don't commit:** `admin-dashboard/public/docs/` (build artifact)

Add to `.gitignore`:
```
admin-dashboard/public/docs/
```

### Documentation Updates

Track changes in commit messages:
```bash
git commit -m "docs: Add quota management guide"
git commit -m "docs: Update API reference with new endpoints"
```

## Technical Details

### Dependencies

```json
{
  "react-markdown": "^9.x",
  "react-syntax-highlighter": "^15.x",
  "@types/react-syntax-highlighter": "^15.x"
}
```

### Component Architecture

**Documentation.tsx**
- Main documentation viewer component
- Handles navigation, search, markdown rendering
- Located: `admin-dashboard/src/pages/Documentation.tsx`

**Navigation Data**
- JSON structure defining docs hierarchy
- Located: `docs/nav.json`
- Loaded at runtime via fetch

**Markdown Files**
- CommonMark format
- Served from: `admin-dashboard/public/docs/`
- Loaded dynamically based on selection

### Routing

Documentation route in `App.tsx`:

```typescript
<Route path="/docs" element={<Documentation />} />
```

Menu item:
```typescript
{ text: 'Documentation', icon: <MenuBookIcon />, path: '/docs' }
```

## Future Enhancements

### Planned Features

- [ ] Full-text search across document content
- [ ] Document version history
- [ ] PDF export
- [ ] Dark mode toggle
- [ ] Printable view
- [ ] Table of contents for long documents
- [ ] Copy code button
- [ ] Embedded video support
- [ ] Interactive API explorer
- [ ] User feedback/ratings

### Contributing

To contribute documentation:

1. Fork repository
2. Create feature branch
3. Add/update markdown files in `docs/`
4. Update `docs/nav.json` if adding new files
5. Test in local dashboard
6. Submit pull request

## Support

For documentation questions:
- **Content Issues:** Check existing docs or create issue
- **Technical Issues:** Review troubleshooting guide
- **Feature Requests:** Submit via GitHub Issues

---

**Documentation System Version:** 1.0.0  
**Last Updated:** 2026-04-20  
**Total Documents:** 14 (6 complete, 8 stubs)  
**Total Characters:** 48,000+
